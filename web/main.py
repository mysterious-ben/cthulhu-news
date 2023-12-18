import base64
import itertools
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
import httpx
import pymongo
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dateutil import parser  # type: ignore
from dotenv import find_dotenv, load_dotenv
from envparse import env
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from logutil import init_loguru
from openai import OpenAI

load_dotenv(find_dotenv())

NEWS_UPDATE_HOURS = "12"
NEWS_UPDATE_HOURS_PARSED = [int(x) for x in NEWS_UPDATE_HOURS.split(",")]
NEWS_LOOKBACK_WINDOW_SECONDS = 3600 * 24 - 300
NEWS_MIN_NUMBER = 3
MONGO_USER = env.str("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = env.str("MONGO_INITDB_ROOT_PASSWORD")
MONGO_HOST = env.str("MONGO_HOST")
MONGO_PORT = env.int("MONGO_PORT")
MONGODB_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}?retryWrites=true&w=majority"
MONGO_NEWS_DB = "news"
MONGO_NEWS_COLLECTION = "gnews"
OPENAI_API_KEY = env.str("OPENAI_API_KEY")
OPENAI_GPT_MODEL = env.str("OPENAI_GPT_CTHULHU_MODEL")
OPENAI_GPT_MAX_TOKENS = env.int("OPENAI_GPT_CTHULHU_MAX_TOKENS")
# SQLITE_READ_CACHE_FOR_X_SECONDS = env.int("SQLITE_READ_CACHE_FOR_X_SECONDS")
CTHULHU_DEFAULT_FIRST_TIMESTAMP = parser.parse(env.str("CTHULHU_DEFAULT_FIRST_TIMESTAMP"))
CTHULHU_DALLE_MODEL = "dall-e-3"
CTHULHU_IMAGE_DIR = Path("data", "images")
CTHULHU_IMAGE_DIR.mkdir(exist_ok=True, parents=True)
logger.debug(f"CTHULHU_IMAGE_DIR={CTHULHU_IMAGE_DIR.absolute()}")

DEFAULT_NEWS_REACTIONS = {
    "like": {"pretty": "Truth", "value": 0},
    "dislike": {"pretty": "Lie", "value": 0},
}


init_loguru(file_path="logs/log.log")

app = FastAPI(title="Cthulhu-News")
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)

templates = Jinja2Templates(directory="templates")
db_path = Path("data", "local.db")
db_path.parent.mkdir(exist_ok=True)


def init_local_news_db():
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()

        # c.execute("""DROP TABLE news""")
        c.execute(
            f"""\
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                media_source_name TEXT NOT NULL,
                published_at TEXT NOT NULL,
                title TEXT NOT NULL,
                original_text TEXT NOT NULL,
                cthulhu_new_title TEXT NOT NULL,
                cthulhu_truth TEXT NOT NULL,
                cthulhu_image BLOB,
                meta JSON,
                reactions JSON DEFAULT '{json.dumps(DEFAULT_NEWS_REACTIONS)}',
                UNIQUE(url),
                UNIQUE(title)
            )"""
        )
        logger.info("initialized the local news db")


init_local_news_db()


def _get_external_articles(
    from_: Optional[datetime],
    to_: Optional[datetime],
    limit: int,
    exclude_titles: Optional[list[str]] = None,
    exclude_ids: Optional[list[str]] = None,
) -> list[dict]:
    client: pymongo.MongoClient = pymongo.MongoClient(MONGODB_URI)
    db = client.get_database(MONGO_NEWS_DB)
    collection = db[MONGO_NEWS_COLLECTION]
    filter_params: dict[str, dict] = {
        "gpt_summary": {"$exists": True},
    }
    if from_ is not None or to_ is not None:
        filter_params["published_at"] = {}
        if from_ is not None:
            filter_params["published_at"].update({"$gt": from_})
        if to_ is not None:
            filter_params["published_at"].update({"$lt": to_})
    if exclude_ids is not None:
        filter_params["_id"] = {"$nin": exclude_ids}
    if exclude_titles is not None:
        filter_params["title"] = {"$nin": exclude_titles}

    mongo_docs = collection.find(
        filter_params, sort=[("published_at", pymongo.DESCENDING)], limit=limit
    )

    docs: list[dict] = []

    # key name, key is on the top level
    keys_levels = (
        ("url", True),
        ("media_source_name", True),
        ("published_at", True),
        ("title", True),
        ("gpt_summary", True),
        ("_id", False),
        ("gpt_sectors", False),
        ("gpt_mood", False),
        ("gpt_breaking_news", False),
        ("gpt_like_a_hollywood_movie", False),
        ("gpt_trustworthy", False),
        ("gpt_economic_impact", False),
    )
    main_keys = [x[0] for x in keys_levels if x[1]]
    meta_keys = [x[0] for x in keys_levels if not x[1]]
    logger.debug(f"mongo {filter_params=}")
    for mongo_doc in mongo_docs:
        doc = {k: mongo_doc[k] for k in main_keys}
        doc["meta"] = {k: mongo_doc[k] for k in meta_keys}
        doc["meta"]["_id"] = str(doc["meta"]["_id"])
        docs.append(doc)
        logger.debug(
            f"article title={doc['title']} "
            f"published_at={doc['published_at'].strftime(r'%Y-%m-%dT%H:%M:%SZ')}"
        )
    logger.info(f"loaded external articles count={len(docs)}")
    return docs


def _parse_gpt_json_response(expected_fields: dict, response_json: dict) -> dict:
    formatted_gpt_json = {}
    for field, conditions in expected_fields.items():
        value_is_correct = True
        if field in response_json:
            value: str = response_json[field]
            value = value.strip()
            if conditions["force_lower"]:
                value = value.lower()
            if conditions["split"]:
                value = [v.strip() for v in value.split(",")]  # type: ignore
                if conditions["choices"]:
                    value_is_correct = set(value).issubset(set(conditions["choices"]))  # type: ignore
            else:
                if conditions["choices"]:
                    value_is_correct = value in set(conditions["choices"])  # type: ignore
        if value_is_correct:
            formatted_gpt_json[field] = value
        else:
            logger.warning(f"incorrect gpt value field={field} value={value}")
    return formatted_gpt_json


def _add_cthulhu_news(docs: list[dict]) -> None:
    client = OpenAI(api_key=OPENAI_API_KEY)
    gpt_role = "You are a news reporter who believes in Cthulhu mythology"
    gpt_query = (
        "The news article below only tells a part of the story but the truth lies deeper: "
        "there is a hidden link to ancient artifacts or servants of Cthulhu or other Old Gods. "
        "You need write a story to expose this hidden link. "
        "Return a json file. "
        "JSON fields: "
        "'truth' = 2-4 sentences for your thrilling and compelling story which starts with "
        "'But this is just the facade'; "
        "'new_title' = a title of your story; "
        "'doom_gauge' = high, medium, or low; "
        "'the_end_is_near' = yes, no, or unclear. "
        "The news article:\n\n{text}"
    )
    expected_fields = {
        "truth": {"choices": [], "split": False, "force_lower": False},
        "new_title": {"choices": [], "split": False, "force_lower": False},
        "doom_gauge": {
            "choices": ["high", "medium", "low", "unclear"],
            "split": False,
            "force_lower": True,
        },
        "the_end_is_near": {
            "choices": ["yes", "no", "unclear"],
            "split": False,
            "force_lower": True,
        },
    }
    primary_keys = ["truth", "new_title"]
    for doc in docs:
        original_text = doc["gpt_summary"]
        gpt_messages = [
            {"role": "system", "content": gpt_role},
            {"role": "user", "content": gpt_query.format(text=original_text)},
        ]
        try:
            openai_response = client.chat.completions.create(
                model=OPENAI_GPT_MODEL,
                messages=gpt_messages,  # type: ignore
                stream=False,
                max_tokens=OPENAI_GPT_MAX_TOKENS,
                n=1,
                stop=None,
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            response_json = json.loads(openai_response.choices[0].message.content)
            formatted_response_json = _parse_gpt_json_response(expected_fields, response_json)
            doc.update(
                {
                    f"cthulhu_{k}": v
                    for k, v in formatted_response_json.items()
                    if k in primary_keys
                }
            )
            doc["meta"].update(
                {
                    f"cthulhu_{k}": v
                    for k, v in formatted_response_json.items()
                    if k not in primary_keys
                }
            )
            logger.debug(f"added gpt generated fields title='{doc['title']}'")
        except Exception as e:
            logger.exception(e)
    logger.info(f"generated gpt cthulhu news count={len(docs)}")


def _add_cthulhu_images(docs: list[dict]) -> None:
    client = OpenAI(api_key=OPENAI_API_KEY)
    for doc in docs:
        dalle_prompt = (
            "Create a dark retro surrealism image that depicts this alarming news article:\n\n"
        )
        dalle_prompt += doc["gpt_summary"]
        dalle_prompt += " " + doc["cthulhu_truth"]
        title: str = doc["cthulhu_new_title"]
        image_name = "".join(x for x in title.lower() if x.isalnum())

        response = client.images.generate(
            model=CTHULHU_DALLE_MODEL,
            prompt=dalle_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
        revised_prompt = response.data[0].revised_prompt
        logger.debug(f"{revised_prompt=}")
        img_json = response.data[0].b64_json
        assert img_json is not None
        img_bytes = base64.b64decode(img_json)

        if revised_prompt is not None:
            with open(CTHULHU_IMAGE_DIR / f"{image_name}.txt", "wt") as f:
                f.write(revised_prompt)

        with open(CTHULHU_IMAGE_DIR / f"{image_name}.png", "wb") as f:
            f.write(img_bytes)

        doc["cthulhu_image"] = img_bytes

    logger.info(f"generated gpt cthulhu images count={len(docs)}")


def _upload_articles(docs: list[dict]) -> None:
    if len(docs) == 0:
        return

    expected_entries = [
        ("url", "url", "?"),
        ("media_source_name", "media_source_name", "?"),
        ("published_at", "published_at", "?"),
        ("title", "title", "?"),
        ("gpt_summary", "original_text", "?"),
        ("cthulhu_new_title", "cthulhu_new_title", "?"),
        ("cthulhu_truth", "cthulhu_truth", "?"),
        ("cthulhu_image", "cthulhu_image", "?"),
        ("meta", "meta", "json(?)"),
    ]
    expected_keys = [k[0] for k in expected_entries]
    sql_keys = [k[1] for k in expected_entries]
    sql_values = [k[2] for k in expected_entries]
    assert len(set(expected_keys)) == len(expected_keys)
    assert len(set(sql_keys)) == len(sql_keys)

    # Convert records to SQLite-friendly format
    docs_to_insert = []
    for doc in docs:
        doc = {k: v for k, v in doc.items()}
        # doc = doc[expected_keys]
        if not set(doc.keys()) == set(expected_keys):
            raise AssertionError(f"actual={list(doc.keys())} vs expected={expected_keys}")
        for k, v in doc.items():
            if isinstance(v, dict):
                doc[k] = json.dumps(v)
            elif isinstance(v, datetime):
                doc[k] = v.strftime(r"%Y-%m-%dT%H:%M:%SZ")
        # docs_to_insert = {k: doc[k] for k in expected_keys}
        docs_to_insert.append([doc[k] for k in expected_keys])

    # Insert records
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        # sql = (
        #     f"""INSERT OR IGNORE INTO news ({",".join(expected_keys)}) """
        #     f"""VALUES ({",".join([":"+x for x in expected_keys])})"""
        # )
        sql = (
            f"""INSERT OR IGNORE INTO news ({",".join(sql_keys)}) """
            f"""VALUES ({",".join(sql_values)})"""
        )
        c.executemany(sql, docs_to_insert)
    logger.info(f"inserted news into the internal db count={len(docs_to_insert)}")


def load_external_news(from_: Optional[datetime], to_: Optional[datetime], limit: int) -> int:
    """Load external news into the internal database.

    Returns the number of loaded external news articles (not the uploaded articles)"""

    logger.info(f"started loading news articles limit={limit}...")
    articles = _get_external_articles(from_=from_, to_=to_, limit=limit)
    _add_cthulhu_news(articles)
    _add_cthulhu_images(articles)
    _upload_articles(articles)
    logger.info(f"finished loading news articles count={len(articles)}")
    return len(articles)


# @TTLCache(maxsize=0, ttl=SQLITE_READ_CACHE_FOR_X_SECONDS)
async def get_news() -> list[dict]:
    """Get news from the local db"""

    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(
            """SELECT * FROM news ORDER BY published_at DESC""",
        ) as c:
            records = await c.fetchall()
            columns = [x[0] for x in c.description]
    news_articles = [{k: v for k, v in zip(columns, rec)} for rec in records]
    for article in news_articles:
        for k in ("meta", "reactions"):
            article[k] = json.loads(article[k])
    return news_articles


async def count_news() -> int:
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(
            """SELECT count(*) FROM news""",
        ) as c:
            row = await c.fetchone()
        assert row is not None
    count = row[0]
    return count


@app.get("/", response_class=HTMLResponse)
async def read_news(request: Request):
    try:
        news_articles = await get_news()
        if len(news_articles) > 0:
            assert hasattr(news_articles[0]["reactions"], "items")

        # Make data HTML-friendly
        for article in news_articles:
            if article["cthulhu_image"] is not None:
                article["cthulhu_image"] = base64.b64encode(article["cthulhu_image"]).decode(
                    "utf-8"
                )
            if article["reactions"] is not None:
                for reaction in article["reactions"]:
                    if reaction in DEFAULT_NEWS_REACTIONS:
                        article["reactions"][reaction]["pretty"] = DEFAULT_NEWS_REACTIONS[
                            reaction
                        ]["pretty"]

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Error while collecting news articles") from e

    return templates.TemplateResponse(
        "news_page.html", {"request": request, "news_articles": news_articles}
    )


@app.post("/react/{reaction}/{article_id}")
async def react_to_article(reaction: str, article_id: int) -> PlainTextResponse:
    try:
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute(
                f"""UPDATE news SET """
                f"""reactions = json_replace(reactions, '$.{reaction}.value', """
                f"""json_extract(reactions, '$.{reaction}.value') + 1 ) """
                f"""WHERE id == {article_id}"""
            )
            await conn.commit()
            async with conn.execute(
                f"""SELECT json_extract(reactions, '$.{reaction}.value') FROM news WHERE id == {article_id}"""
            ) as c:
                rows = await c.fetchone()
            assert rows is not None
            new_count = rows[0]
        return PlainTextResponse(
            f"""<span id="{reaction}-count-{article_id}">{new_count}</span>"""
        )
    except Exception as e:
        raise e
        # raise HTTPException(status_code=500, detail=str(e)) from e


def latest_published_at() -> Optional[datetime]:
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        row = c.execute("""SELECT max(published_at) FROM news""").fetchone()
    if row is None or row[0] is None:
        return None
    published_at = row[0]
    return parser.parse(published_at)


def update_news(fill_gaps: bool = True):
    now = datetime.now(tz=timezone.utc)
    lookback_delta = timedelta(seconds=NEWS_LOOKBACK_WINDOW_SECONDS)
    if fill_gaps:
        latest = latest_published_at()
        if latest is None:
            latest = CTHULHU_DEFAULT_FIRST_TIMESTAMP
        n_days = (now - latest).days + 1
        dates = [latest.date() + timedelta(days=x) for x in range(n_days)]
        timestamps = [
            datetime(d.year, d.month, d.day, h, tzinfo=timezone.utc)
            for d, h in itertools.product(dates, NEWS_UPDATE_HOURS_PARSED)
        ]
        timestamps = [x for x in timestamps if (x > latest + lookback_delta) and (x < now)]
        logger.debug(
            f"updating news with latest={latest.strftime(r'%Y-%m-%dT%H:%M:%SZ')} "
            f"latest_={(latest + lookback_delta).strftime(r'%Y-%m-%dT%H:%M:%SZ')} "
            f"now={now.strftime(r'%Y-%m-%dT%H:%M:%SZ')} n={len(timestamps)}"
        )
        for t in timestamps:
            load_external_news(from_=t - lookback_delta, to_=t, limit=1)
            logger.info(f"updated news t={t.strftime(r'%Y-%m-%dT%H:%M:%SZ')}")
    else:
        load_external_news(from_=now - lookback_delta, to_=now, limit=1)
        logger.info(f"updated news now={now.strftime(r'%Y-%m-%dT%H:%M:%SZ')}")


def start_cthulhu_etl():
    logger.info("starting the scheduler...")
    scheduler = BlockingScheduler()
    # start_time = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
    scheduler.add_job(
        update_news,
        CronTrigger(hour=NEWS_UPDATE_HOURS, minute=0, second=1),
        kwargs={},
        name="download_news",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("started the scheduler...")


if __name__ == "__main__":
    update_news()
    start_cthulhu_etl()

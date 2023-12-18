import json
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import httpx
import newspaper
import nltk
import pymongo
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import find_dotenv, load_dotenv
from envparse import env
from loguru import logger
from logutil import init_loguru
from openai import OpenAI
from pymongo.errors import BulkWriteError

load_dotenv(find_dotenv())

GNEWS_API_KEY = env.str("GNEWS_API_KEY")
GNEWS_URL = "https://gnews.io/api/v4/search"
GNEWS_SORT_BY: Literal["publishedAt", "relevance"] = "relevance"
GNEWS_MAX_ARTICLES: int = 10
GNEWS_LANG = "en"
MONGO_USER = env.str("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = env.str("MONGO_INITDB_ROOT_PASSWORD")
MONGO_HOST = env.str("MONGO_HOST")
MONGO_PORT = env.int("MONGO_PORT")
MONGODB_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}?retryWrites=true&w=majority"
MONGO_NEWS_DB = "news"
MONGO_NEWS_COLLECTION = "gnews"
NEWS_QUERIES = ["finance", "energy", "weather", "murders", "funny"]
NEWS_QUERY_EVERY_X_SECONDS = env.int("NEWS_QUERY_EVERY_X_SECONDS")
NEWS_QUERY_WINDOW_EXTENSION_SECONDS = env.int("NEWS_QUERY_WINDOW_EXTENSION_SECONDS")
OPENAI_API_KEY = env.str("OPENAI_API_KEY")
OPENAI_GPT_MODEL = env.str("OPENAI_GPT_SUMMARY_MODEL")
OPENAI_GPT_MAX_TOKENS = env.int("OPENAI_GPT_SUMMARY_MAX_TOKENS")


init_loguru(file_path="logs/log.log")

logger.info("downloadeding nltk punkt...")
# nltk.download("punkt", download_dir=NLTK_DOWNLOADS_DIR, quiet=True, raise_on_error=True)
nltk.download("punkt", raise_on_error=True)
logger.info("downloaded nltk punkt")


def get_news_links_gnews(
    query: str,
    from_: Optional[datetime],
    to_: Optional[datetime],
    lang: str,
    limit: int,
    sortby: Literal["publishedAt", "relevance"],
) -> list[dict]:
    params = {
        "q": query,
        "lang": lang,
        "max": limit,
        "sortby": sortby,
        "apikey": GNEWS_API_KEY,
    }

    if from_ is not None:
        from_s = from_.strftime(r"%Y-%m-%dT%H:%M:%SZ")
        params.update({"from": from_s})
    else:
        from_s = "none"

    if to_ is not None:
        to_s = to_.strftime(r"%Y-%m-%dT%H:%M:%SZ")
        params.update({"to": to_s})
    else:
        to_s = "none"

    response = httpx.get(GNEWS_URL, params=params, timeout=60)
    data = json.loads(response.read().decode("utf-8"))
    if "articles" in data:
        news_listings = data["articles"]
    else:
        news_listings = []
        logger.warning("response json no key 'articles':  " + str(data))
    logger.info(
        f"downloaded news listings count={len(news_listings)} {query=} from={from_s} to={to_s}"
    )

    formatted_news_listings = []
    for listing in news_listings:
        formatted_listing = {}
        formatted_listing["title"] = listing["title"]
        formatted_listing["description"] = listing["description"]
        formatted_listing["partial_text"] = listing["content"]
        formatted_listing["url"] = listing["url"]
        # formatted_news_link["image"] = news_link["image"]
        formatted_listing["published_at"] = datetime.strptime(
            listing["publishedAt"], r"%Y-%m-%dT%H:%M:%S%z"
        )
        formatted_listing["media_source_name"] = listing["source"]["name"]
        formatted_listing["media_source_url"] = (
            listing["source"]["url"].replace("http://", "").replace("https://", "")
        )
        listing["partial_text"] = listing["content"]
        formatted_listing["listing_query"] = query
        formatted_listing["listing_source"] = "gnews"
        formatted_news_listings.append(formatted_listing)

    logger.info(
        f"formatted news listings count={len(formatted_news_listings)} {query=} from={from_s} to={to_s}"
    )

    return formatted_news_listings


def load_news_articles(news_listings: list[dict]) -> None:
    for listing in news_listings:
        try:
            page = newspaper.Article(listing["url"])
            page.download()
            page.parse()
            page.nlp()
        except Exception as e:
            logger.exception(e)
        else:
            listing["full_text"] = page.text
            listing["full_html"] = page.html
            listing["tags"] = list(page.tags)
            listing["nltk_summary"] = page.summary
            listing["nltk_keywords"] = page.keywords
            logger.debug(f"downloaded and parsed news article title='{listing['title']}'")
    logger.info(f"downloaded and parsed full news articles count={len(news_listings)}")


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


def add_gpt_info(news_listings: list[dict]) -> None:
    client = OpenAI(api_key=OPENAI_API_KEY)
    gpt_role = "You're a news editor"
    gpt_query = (
        "Return a json file based on the news article below. "
        "Ignore ads and debugging messages related to the web. "
        "JSON fields: "
        "'summary' = a one-paragraph summary of the news article; "
        "'keywords' = 5 to 10 keywords separated by a comma; "
        "'sectors' = most relevant sectors separated by a comma; "
        "'mood' = positive, negative, neutral, mixed, or unclear; "
        "'breaking_news' = yes, no, or unclear; "
        "'like_a_hollywood_movie' = yes, no, or unclear; "
        "'trustworthy' = yes, no, or unclear; "
        "'economic_impact' = high, medium, low, or unclear. "
        "The news article:\n\n{text}"
    )
    expected_fields = {
        "summary": {"choices": [], "split": False, "force_lower": False},
        "keywords": {"choices": [], "split": True, "force_lower": False},
        "sectors": {"choices": [], "split": True, "force_lower": True},
        "mood": {
            "choices": ["positive", "negative", "neutral", "mixed", "unclear"],
            "split": False,
            "force_lower": True,
        },
        "breaking_news": {
            "choices": ["yes", "no", "unclear"],
            "split": False,
            "force_lower": True,
        },
        "like_a_hollywood_movie": {
            "choices": ["yes", "no", "unclear"],
            "split": False,
            "force_lower": True,
        },
        "trustworthy": {
            "choices": ["yes", "no", "unclear"],
            "split": False,
            "force_lower": True,
        },
        "economic_impact": {
            "choices": ["high", "medium", "low", "unclear"],
            "split": False,
            "force_lower": True,
        },
    }

    for listing in news_listings:
        if "full_text" in listing:
            text = listing["full_text"]
            gpt_messages = [
                {"role": "system", "content": gpt_role},
                {"role": "user", "content": gpt_query.format(text=text)},
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
                listing.update({f"gpt_{k}": v for k, v in formatted_response_json.items()})
                logger.debug(f"added gpt generated fields title='{listing['title']}'")
            except Exception as e:
                logger.exception(e)
        else:
            logger.warning(
                f"no key=full_text to generate gpt fields (skip) title='{listing['title']}'"
            )
    logger.info(f"added gpt generated fields count={len(news_listings)}")


def save_to_mongo_db(news_articles: list[dict]) -> None:
    client: pymongo.MongoClient = pymongo.MongoClient(MONGODB_URI)
    db = client.get_database(MONGO_NEWS_DB)
    collection = db[MONGO_NEWS_COLLECTION]
    collection.create_index([("url", pymongo.ASCENDING)], unique=True)
    try:
        collection.insert_many(news_articles, ordered=False)
    except BulkWriteError as e:
        logger.warning("error on mongo bulk insert: " + str(e)[:300])
    logger.info("saved news articles to mongo db")


def load_news(
    query: str,
    from_: Optional[datetime],
    to_: Optional[datetime],
):
    news_listings = get_news_links_gnews(
        query=query,
        from_=from_,
        to_=to_,
        lang=GNEWS_LANG,
        limit=GNEWS_MAX_ARTICLES,
        sortby=GNEWS_SORT_BY,
    )
    if len(news_listings) > 0:
        load_news_articles(news_listings)
        add_gpt_info(news_listings)
        save_to_mongo_db(news_listings)
    else:
        logger.info("no news articles to parse and save (skip)")


def load_all_recent_news():
    time_now = datetime.now(tz=timezone.utc)
    time_from = time_now - timedelta(
        seconds=NEWS_QUERY_EVERY_X_SECONDS + NEWS_QUERY_WINDOW_EXTENSION_SECONDS
    )
    for q in NEWS_QUERIES:
        load_news(q, from_=time_from, to_=None)
    logger.info("loaded, parsed and saved all recent news articles")


def start_news_etl():
    logger.info("starting the scheduler...")
    scheduler = BlockingScheduler()
    start_time = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
    scheduler.add_job(
        load_all_recent_news,
        IntervalTrigger(seconds=NEWS_QUERY_EVERY_X_SECONDS),
        name="download_news",
        replace_existing=True,
        next_run_time=start_time,
    )
    scheduler.start()
    logger.info("started the scheduler...")


if __name__ == "__main__":
    start_news_etl()

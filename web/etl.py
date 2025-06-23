###################################
### CREATE CHTHULHU STORIES ETL ###
###################################

import itertools
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Iterable

import pymongo
from prefect import flow, task
from prefect.schedules import Cron
from dateutil import parser  # type: ignore
from dotenv import find_dotenv, load_dotenv
from envparse import env
from loguru import logger
from logutil import init_loguru
from time import sleep

from web.llm_cthulhu_new import add_cthulhu_images, generate_cthulhu_news
import web.mapping as mapping
import web.db_utils as dbu

load_dotenv(find_dotenv())

NEWS_UPDATE_HOURS = env.str("CTHULHU_NEWS_UPDATE_HOURS")
NEWS_UPDATE_HOURS_PARSED = [int(x.strip()) for x in NEWS_UPDATE_HOURS.split(",")]
NEWS_LOOKBACK_WINDOW_SECONDS = env.int("CTHULHU_NEWS_LOOKBACK_WINDOW_SECONDS")
NEWS_MIN_NUMBER = 3
MONGO_USER = env.str("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = env.str("MONGO_INITDB_ROOT_PASSWORD")
MONGO_HOST = env.str("MONGO_HOST")
MONGO_PORT = env.int("MONGO_PORT")
MONGODB_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}?retryWrites=true&w=majority"
MONGO_NEWS_DB = "news"
MONGO_NEWS_COLLECTION = "gnews"
CTHULHU_DEFAULT_FIRST_TIMESTAMP = parser.parse(env.str("CTHULHU_DEFAULT_FIRST_TIMESTAMP"))
CTHULHU_IMAGE_MODEL = "dall-e-3"
CTHULHU_IMAGE_DIR = Path(__file__).parent / "data" / "images"
CTHULHU_IMAGE_DIR.mkdir(exist_ok=True, parents=True)

init_loguru(file_path="logs/web_etl_log.log")
logger.debug(f"CTHULHU_IMAGE_DIR={CTHULHU_IMAGE_DIR.absolute()}")


dbu.init_local_news_db()


def dt_to_str(dt: Optional[datetime]) -> str:
    if dt is None:
        return "None"
    return dt.strftime(r"%Y-%m-%dT%H:%M:%SZ")


def load_mongo_news_articles(
    from_: Optional[datetime],
    to_: Optional[datetime],
    limit: int,
    exclude_titles: Optional[list[str]] = None,
    exclude_ids: Optional[list[str]] = None,
) -> list[mapping.NewsArticle]:
    """Download news articles from the Mongo database."""

    logger.debug(
        f"loading mongo news articles from={dt_to_str(from_)} to={dt_to_str(to_)} limit={limit} "
    )
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

    mongo_docs: Iterable[mapping.NewsArticle] = collection.find(
        filter_params, sort=[("published_at", pymongo.DESCENDING)], limit=limit
    )

    news_articles: list[mapping.NewsArticle] = []

    logger.debug(f"mongo {filter_params=}")
    for doc in mongo_docs:
        news_articles.append(doc)
        logger.debug(
            f"loaded a news article title={doc['title']} published_at={doc['published_at']}"
        )
    logger.info(f"loaded mongo articles count={len(news_articles)}")
    return news_articles


# async def count_news() -> int:
#     async with apgpool.connection() as conn:
#         async with conn.cursor() as c:
#             await c.execute("""SELECT count(*) FROM news""")
#             row = await c.fetchone()
#         assert row is not None
#     count = row[0]
#     return count


def create_and_upload_cthulhu_article(
    from_: Optional[datetime], to_: Optional[datetime], raise_on_zero_articles: bool = False
) -> int:
    """Download news articles, add Chthulhu stories and images, and upload into the web database.

    Returns the number of loaded news articles (not the uploaded articles)"""

    logger.info("started processing a news article...")
    news_articles = load_mongo_news_articles(from_=from_, to_=to_, limit=1)
    if len(news_articles) == 0:
        if raise_on_zero_articles:
            raise ValueError("No news articles found to process.")
        logger.warning("no news articles found to process")
        return 0
    elif len(news_articles) > 1:
        raise ValueError(f"Expected 1 news article, got {len(news_articles)}")
    cthulhu_articles = dbu.load_formatted_cthulhu_articles(article_id=None)
    to_2 = to_ if to_ is not None else datetime.now(tz=timezone.utc)
    new_cthulhu_articles = generate_cthulhu_news(cthulhu_articles, news_articles, [to_2])
    add_cthulhu_images(new_cthulhu_articles)
    dbu.insert_cthulhu_articles(new_cthulhu_articles)
    logger.info(f"finished loading a news article count={len(new_cthulhu_articles)}")
    return len(new_cthulhu_articles)


@task(
    name="create_and_upload_cthulhu_article",
    task_run_name="create_and_upload_cthulhu_article",
    retries=2,
    retry_delay_seconds=30,
)
def create_and_upload_cthulhu_article_task(
    from_: Optional[datetime] = None, to_: Optional[datetime] = None
) -> int:
    """Task to create and upload a Cthulhu article."""
    logger.info("start task to create and upload Cthulhu article")
    return create_and_upload_cthulhu_article(from_=from_, to_=to_)


@flow(name="update_cthulhu_articles", log_prints=True)
def update_cthulhu_articles(fill_gaps: bool = False) -> None:
    """Wrapper function to create and upload multiple Cthulhu articles."""

    now = datetime.now(tz=timezone.utc)
    lookback_delta = timedelta(seconds=NEWS_LOOKBACK_WINDOW_SECONDS)
    if fill_gaps:
        latest = dbu.latest_scene_timestamp()
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
            f"updating news with latest={dt_to_str(latest)} "
            f"latest_={dt_to_str(latest + lookback_delta)} "
            f"now={dt_to_str(now)} n={len(timestamps)}"
        )
        for t in timestamps:
            create_and_upload_cthulhu_article(from_=t - lookback_delta, to_=t)
            logger.info(f"updated news t={dt_to_str(t)}")
    else:
        create_and_upload_cthulhu_article(from_=now - lookback_delta, to_=now)
        logger.info(f"updated news now={dt_to_str(now)}")


def start_cthulhu_etl_with_serve():
    """Start the Cthulhu news ETL using Prefect serve (blocking)"""

    logger.info("serving the Cthulhu news ETL...")

    hours_str = ",".join(map(str, NEWS_UPDATE_HOURS_PARSED))
    cron_expression = f"1 0 {hours_str} * * *"  # minute=0, second=1, specified hours

    scheduler = Cron(cron_expression)
    update_cthulhu_articles.serve(
        name="update_cthulhu_articles",
        schedule=scheduler,
        tags=["cthulhu", "etl"],
        description="Generate Cthulhu news articles periodically",
    )


if __name__ == "__main__":
    update_cthulhu_articles()
    sleep(5)
    start_cthulhu_etl_with_serve()

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

# from web.llm_cthulhu import add_cthulhu_images, add_cthulhu_news
from llm_cthulhu_new import add_cthulhu_images, generate_cthulhu_news
import mapping as mapping
import db as db

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
CTHULHU_DEFAULT_FIRST_TIMESTAMP = parser.parse(
    env.str("CTHULHU_DEFAULT_FIRST_TIMESTAMP")
)
CTHULHU_IMAGE_MODEL = "dall-e-3"
CTHULHU_IMAGE_DIR = Path("data", "images")
CTHULHU_IMAGE_DIR.mkdir(exist_ok=True, parents=True)

init_loguru(file_path="logs/log.log")
logger.debug(f"CTHULHU_IMAGE_DIR={CTHULHU_IMAGE_DIR.absolute()}")


db.init_local_news_db()


def load_external_news_articles(
    from_: Optional[datetime],
    to_: Optional[datetime],
    limit: int,
    exclude_titles: Optional[list[str]] = None,
    exclude_ids: Optional[list[str]] = None,
) -> list[mapping.NewsArticle]:
    """Download news articles from the Mongo database."""

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
    logger.info(f"loaded external articles count={len(news_articles)}")
    return news_articles


def create_and_upload_cthulhu_article(
    from_: Optional[datetime], to_: Optional[datetime]
) -> int:
    """Download news articles, add Chthulhu stories and images, and upload into the web database.

    Returns the number of loaded news articles (not the uploaded articles)"""

    logger.info("started processing a news article...")
    news_articles = load_external_news_articles(from_=from_, to_=to_, limit=1)
    assert len(news_articles) == 1
    cthulhu_articles = db.load_formatted_cthulhu_articles(article_id=None)
    to_2 = to_ if to_ is not None else datetime.now(tz=timezone.utc)
    new_cthulhu_articles = generate_cthulhu_news(
        cthulhu_articles, news_articles, [to_2]
    )
    add_cthulhu_images(new_cthulhu_articles)
    db.insert_cthulhu_articles(new_cthulhu_articles)
    logger.info(f"finished loading a news article count={len(new_cthulhu_articles)}")
    return len(new_cthulhu_articles)


# async def count_news() -> int:
#     async with apgpool.connection() as conn:
#         async with conn.cursor() as c:
#             await c.execute("""SELECT count(*) FROM news""")
#             row = await c.fetchone()
#         assert row is not None
#     count = row[0]
#     return count


def update_cthulhu_articles(fill_gaps: bool = True):
    """Wrapper function to create and upload multiple Cthulhu articles."""

    now = datetime.now(tz=timezone.utc)
    lookback_delta = timedelta(seconds=NEWS_LOOKBACK_WINDOW_SECONDS)
    if fill_gaps:
        latest = db.latest_scene_timestamp()
        if latest is None:
            latest = CTHULHU_DEFAULT_FIRST_TIMESTAMP
        n_days = (now - latest).days + 1
        dates = [latest.date() + timedelta(days=x) for x in range(n_days)]
        timestamps = [
            datetime(d.year, d.month, d.day, h, tzinfo=timezone.utc)
            for d, h in itertools.product(dates, NEWS_UPDATE_HOURS_PARSED)
        ]
        timestamps = [
            x for x in timestamps if (x > latest + lookback_delta) and (x < now)
        ]
        logger.debug(
            f"updating news with latest={latest.strftime(r'%Y-%m-%dT%H:%M:%SZ')} "
            f"latest_={(latest + lookback_delta).strftime(r'%Y-%m-%dT%H:%M:%SZ')} "
            f"now={now.strftime(r'%Y-%m-%dT%H:%M:%SZ')} n={len(timestamps)}"
        )
        for t in timestamps:
            create_and_upload_cthulhu_article(from_=t - lookback_delta, to_=t)
            logger.info(f"updated news t={t.strftime(r'%Y-%m-%dT%H:%M:%SZ')}")
    else:
        create_and_upload_cthulhu_article(from_=now - lookback_delta, to_=now)
        logger.info(f"updated news now={now.strftime(r'%Y-%m-%dT%H:%M:%SZ')}")


def start_cthulhu_etl():
    """Start the Cthulhu ETL scheduler"""

    logger.info("starting the scheduler...")
    scheduler = BlockingScheduler()
    # start_time = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
    scheduler.add_job(
        update_cthulhu_articles,
        CronTrigger(hour=NEWS_UPDATE_HOURS, minute=0, second=1),
        kwargs={},
        name="download_news",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("started the scheduler...")


if __name__ == "__main__":
    update_cthulhu_articles()
    start_cthulhu_etl()

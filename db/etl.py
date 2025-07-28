#########################
### DOWNLOAD NEWS ETL ###
#########################

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Literal

# import click
import httpx
import newspaper
import nltk
import pymongo
from dotenv import find_dotenv, load_dotenv
from envparse import env
from loguru import logger
from logutil import init_loguru
from pymongo.errors import BulkWriteError

from db.llm_summary import add_gpt_info
from prefect import flow, task
from prefect.schedules import Interval
from shared.paths import DB_ETL_LOG_PATH

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

init_loguru(file_path=str(DB_ETL_LOG_PATH))
logger.info("downloadeding nltk punkt...")
# nltk.download("punkt", download_dir=NLTK_DOWNLOADS_DIR, quiet=True, raise_on_error=True)
nltk.download("punkt", raise_on_error=True)
nltk.download("punkt_tab", raise_on_error=True)
logger.info("downloaded nltk punkt")


def get_news_links_gnews(
    query: str,
    from_: datetime | None,
    to_: datetime | None,
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
        time.sleep(0.5)
    logger.info(f"downloaded and parsed full news articles count={len(news_listings)}")


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
    from_: datetime | None,
    to_: datetime | None,
) -> None:
    """Load a news article, add a GPT summary and save to the local db"""

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


@task(
    name="load_news_for_query",
    task_run_name="load_news_for_query-{query}",
    retries=2,
    retry_delay_seconds=30,
)
def load_news_task(query, from_, to_=None):
    """Task to load news for a specific query"""
    logger.info(f"start task to load news for query: {query}")
    return load_news(query, from_=from_, to_=to_)


@flow(name="load_all_recent_news", log_prints=True)
def load_all_recent_news_flow():
    """Load all recent news articles, add a GPT summary and save to the local db"""

    time_now = datetime.now(tz=timezone.utc)
    time_from = time_now - timedelta(
        seconds=NEWS_QUERY_EVERY_X_SECONDS + NEWS_QUERY_WINDOW_EXTENSION_SECONDS
    )
    for q in NEWS_QUERIES:
        load_news_task(q, from_=time_from, to_=None)

    logger.info("loaded, parsed and saved all recent news articles")


# @click.command("serve")
def start_news_etl_with_serve():
    """Start the normal news ETL using Prefect serve (blocking)"""

    logger.info("serving the normal news ETL...")
    schedule = Interval(
        timedelta(seconds=NEWS_QUERY_EVERY_X_SECONDS),
        anchor_date=datetime.now(tz=timezone.utc) + timedelta(seconds=5),
    )
    load_all_recent_news_flow.serve(
        name="news-etl-deployment",
        schedule=schedule,
        tags=["news", "etl"],
        description="Load normal news articles periodically",
    )


if __name__ == "__main__":
    start_news_etl_with_serve()

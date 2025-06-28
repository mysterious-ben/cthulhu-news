###################################
### CHTHULHU-NEWS WEB INTERFACE ###
###################################

import cachetools
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv, load_dotenv
from envparse import env
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from loguru import logger
from logutil import init_loguru

import web.mapping as mapping
import web.db_utils as dbu
from shared.paths import CTHULHU_IMAGE_DIR, HTML_STATIC_DIR, TEMPLATES_DIR, WEB_APP_LOG_PATH

load_dotenv(find_dotenv())

templates = Jinja2Templates(directory=TEMPLATES_DIR)
CTHULHU_NEWS_CACHE_FOR_X_SECONDS = env.float("CTHULHU_NEWS_CACHE_FOR_X_SECONDS")


STATIC_IMAGE_TYPES: dict[str, dict] = {
    "default": {"size": None, "jpg_quality": 95},
    "large": {"size": None, "jpg_quality": 95},
    "medium": {"size": (768, 768), "jpg_quality": 95},
    "small": {"size": (512, 512), "jpg_quality": 95},
}

app = FastAPI(title="Cthulhu-News")
app.mount(
    "/static",
    StaticFiles(directory=HTML_STATIC_DIR.absolute()),
    name="static",
)

init_loguru(file_path=str(WEB_APP_LOG_PATH))
logger.debug(f"HTML_STATIC_DIR={HTML_STATIC_DIR.absolute()}")


def _prepare_news_articles_for_html(cthulhu_articles: list[mapping.Scene]) -> None:
    static_image_dir = HTML_STATIC_DIR / "cthulhu-images"
    for article in cthulhu_articles:
        if (
            "cthulhu_image_filename" in article["image_meta"]
        ):
            image_filename: str = article["image_meta"]["cthulhu_image_filename"]
            logger.debug(f"processing article image: {image_filename}")
            logger.debug(f"image_dir={CTHULHU_IMAGE_DIR.absolute()}")
            image_path = CTHULHU_IMAGE_DIR / image_filename
            if image_path.exists():
                article["image_meta"]["cthulhu_image_name"] = str(Path(image_filename).stem)
                image_name = article["image_meta"]["cthulhu_image_name"]
                for img_type, img_params in STATIC_IMAGE_TYPES.items():
                    static_image_path: Path = static_image_dir / f"{image_name}-{img_type}.jpg"
                    if not static_image_path.exists():
                        with Image.open(image_path) as img:
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            if img_params["size"] is not None:
                                img = img.resize(img_params["size"], Image.Resampling.LANCZOS)
                            img.save(static_image_path, "JPEG", quality=img_params["jpg_quality"])
                        logger.debug(f"created static image path={static_image_path}")
            else:
                logger.warning(f"image file not found: {image_path}")
        else:
            logger.warning(f"no image for article '{article['news_title']}'")
        article["published_at"] = article["news_published_at"].isoformat()  # type: ignore
        if article["reactions"] is not None:
            for comment in article["reactions"]["comments"]:
                if "author" in comment:
                    comment["author"] = "".join(
                        " " if x == " " else "█" for x in comment["author"]
                    )


@cachetools.cached(cachetools.TTLCache(maxsize=100, ttl=CTHULHU_NEWS_CACHE_FOR_X_SECONDS))
def _get_cthulhu_articles_cached(scene_number: Optional[int] = None) -> list[mapping.Scene]:
    return dbu.load_formatted_cthulhu_articles(scene_number=scene_number)


@app.get("/", response_class=HTMLResponse)
async def news_main_page(request: Request):
    start = datetime.now()
    logger.debug("loading the news page...")

    news_articles = _get_cthulhu_articles_cached()
    _prepare_news_articles_for_html(news_articles)
    response = templates.TemplateResponse(
        "news_main_page.html", {"request": request, "news_articles": news_articles}
    )

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"prepared the news page elapsed={elapsed:.2f}s")
    return response


def _assert_one_article_exists(news_articles: list, scene_number: int):
    if scene_number is not None:
        if len(news_articles) == 0:
            raise HTTPException(404, detail=f"The article not found scene_number={scene_number}")
        elif len(news_articles) > 1:
            raise HTTPException(
                500,
                detail=f"Too many articles scene_number={scene_number} n={len(news_articles)}",
            )


@app.get("/article/{scene_number}", response_class=HTMLResponse)
async def news_article_page(request: Request, scene_number: int):
    start = datetime.now()
    logger.debug("loading the article page...")

    news_articles = _get_cthulhu_articles_cached(scene_number=scene_number)
    _assert_one_article_exists(news_articles, scene_number)
    _prepare_news_articles_for_html(news_articles)

    response = templates.TemplateResponse(
        "news_article.html", {"request": request, "article": news_articles[0]}
    )
    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"prepared the article page elapsed={elapsed:.2f}s")
    return response


@app.post("/react/{vote}/{scene_number}")
async def react_to_article(
    vote: str, scene_number: int, user: Optional[str] = None
) -> PlainTextResponse:
    dbu.inc_cthulhu_article_vote(scene_number, vote, user)
    logger.info(f"reacted to the article scene_number={scene_number} vote={vote} user={user}")
    new_vote_counts = dbu.get_cthulhu_article_votes(scene_number=scene_number)
    assert new_vote_counts is not None
    new_count = new_vote_counts[vote]
    return PlainTextResponse(f"""{new_count}""")


@app.post("/submit_comment/{scene_number}")
async def submit_comment(
    scene_number: int,
    request: Request,
    author: str = Form(...),
    comment: str = Form(...),
    user: Optional[str] = None,
):
    if len(author) == 0 or len(comment) == 0:
        return

    comment_json: mapping.Comment = {
        "author": author,
        "comment": comment,
        "created_at": datetime.now(),
        "hidden": False,
        "accepted": False,
        "votes": {"truth": 0, "lie": 0, "voted_by": []},
    }
    dbu.submit_cthulhu_article_comment(scene_number, comment_json, user)
    news_articles = _get_cthulhu_articles_cached(scene_number=scene_number)
    _assert_one_article_exists(news_articles, scene_number)
    _prepare_news_articles_for_html(news_articles)
    article = news_articles[0]
    # article["meta"]["comments"] = [{"author": author, "comment": comment}]

    context = {"request": request, "article": article}
    logger.info(f"commented the article scene_number={scene_number} comment='{comment[:15]}'")
    return templates.TemplateResponse("comments.html", context)

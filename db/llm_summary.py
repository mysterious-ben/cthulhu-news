import litellm
from dotenv import find_dotenv, load_dotenv
from envparse import env
from loguru import logger

from shared.llm_utils import get_llm_json_response

load_dotenv(find_dotenv())

OPENAI_API_KEY = env.str("OPENAI_API_KEY")
TEXT_MODEL_SUMMARIZER = env.str("TEXT_MODEL_SUMMARIZER")
TEXT_MODEL_MAX_TOKENS = env.int("TEXT_MODEL_SUMMARIZER_MAX_TOKENS")

litellm.openai_key = OPENAI_API_KEY


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
            try:
                response_json = get_llm_json_response(
                    gpt_role=gpt_role,
                    gpt_query=gpt_query.format(text=text),
                    gpt_model=TEXT_MODEL_SUMMARIZER,
                    gpt_max_tokens=TEXT_MODEL_MAX_TOKENS,
                )
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

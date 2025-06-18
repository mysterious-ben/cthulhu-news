import json

from envparse import env
from loguru import logger
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = env.str("OPENAI_API_KEY")
OPENAI_GPT_MODEL = env.str("TEXT_MODEL_SUMMARIZER")
OPENAI_GPT_MAX_TOKENS = env.int("TEXT_MODEL_SUMMARY_MAX_TOKENS")


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
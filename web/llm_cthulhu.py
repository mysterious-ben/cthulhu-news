import base64
import json
from pathlib import Path

from envparse import env
from loguru import logger
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

OPENAI_API_KEY = env.str("OPENAI_API_KEY")
OPENAI_GPT_MODEL = env.str("TEXT_CTHULHU_MODEL")
OPENAI_GPT_MAX_TOKENS = env.int("TEXT_MODEL_MAX_TOKENS")

CTHULHU_IMAGE_MODEL = "dall-e-3"
CTHULHU_IMAGE_DIR = Path("data", "images")
CTHULHU_IMAGE_DIR.mkdir(exist_ok=True, parents=True)


def _str_to_filename(string: str) -> str:
    return "".join(x for x in string.lower().replace(" ", "_") if x.isalnum() or x == "_")


def _parse_gpt_json_response(expected_fields: dict, response_json: dict) -> dict:
    formatted_gpt_json = {}
    for field, conditions in expected_fields.items():
        value_is_correct = True
        value = None
        if field in response_json:
            if conditions.get("is_int", False):
                value = int(response_json[field])
            else:
                value = response_json[field]
                assert isinstance(value, str)
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


def add_cthulhu_news(docs: list[dict]) -> None:
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


def add_cthulhu_images(docs: list[dict]) -> None:
    client = OpenAI(api_key=OPENAI_API_KEY)
    for doc in docs:
        dalle_prompt = (
            "Create a dark retro surrealism image that depicts this alarming news article:\n\n"
        )
        dalle_prompt += doc["gpt_summary"]
        dalle_prompt += " " + doc["cthulhu_truth"]
        title: str = doc["cthulhu_new_title"]
        image_name = _str_to_filename(title)

        response = client.images.generate(
            model=CTHULHU_IMAGE_MODEL,
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

        image_filename = f"{image_name}.png"
        with open(CTHULHU_IMAGE_DIR / image_filename, "wb") as f:
            f.write(img_bytes)

        # doc["cthulhu_image"] = img_bytes
        doc["meta"].update(
            {
                "cthulhu_image_prompt": dalle_prompt,
                "cthulhu_image_name": image_name,
                "cthulhu_image_filename": image_filename,
                "cthulhu_image_dir": str(CTHULHU_IMAGE_DIR),
            }
        )
        if revised_prompt is not None:
            doc["meta"].update(
                {
                    "cthulhu_image_revised_prompt": revised_prompt,
                }
            )

    logger.info(f"generated gpt cthulhu images count={len(docs)}")
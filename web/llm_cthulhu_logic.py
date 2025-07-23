import base64
import random
import time
from datetime import datetime

import litellm
import numpy as np
from dotenv import find_dotenv, load_dotenv
from envparse import env
from loguru import logger

import web.llm_cthulhu_prompts as prompts
from shared.llm_utils import get_llm_json_response
from shared.paths import CTHULHU_IMAGE_DIR
from web.mapping import NewsArticle, Scene, WinCounters

load_dotenv(find_dotenv())

OPENAI_API_KEY = env.str("OPENAI_API_KEY")
TEXT_MODEL_WRITER = env.str("TEXT_MODEL_WRITER")
TEXT_MODEL_SUMMARIZER = env.str("TEXT_MODEL_SUMMARIZER")
TEXT_MODEL_WRITER_MAX_TOKENS = env.int("TEXT_MODEL_WRITER_MAX_TOKENS")
TEXT_MODEL_SUMMARIZER_MAX_TOKENS = env.int("TEXT_MODEL_SUMMARIZER_MAX_TOKENS")

CTHULHU_IMAGE_MODEL = "dall-e-3"

litellm.openai_key = OPENAI_API_KEY


def _str_to_filename(string: str) -> str:
    return "".join(x for x in string.lower().replace(" ", "_") if x.isalnum() or x == "_")


def _parse_llm_json_response(
    expected_fields: dict, response_json: dict, raise_on_error: bool = True
) -> dict:
    formatted_gpt_json = {}
    for field, conditions in expected_fields.items():
        value_is_correct = True
        value = None
        if field in response_json:
            if conditions.get("is_int", False):
                value = int(response_json[field])
            elif conditions.get("is_bool", False):
                if isinstance(response_json[field], bool):
                    value = response_json[field]
                elif isinstance(response_json[field], str):
                    v = response_json[field].strip().lower()
                    if v in ["true", "yes", "1"]:
                        value = True
                    elif v in ["false", "no", "0"]:
                        value = False
                    else:
                        value_is_correct = False
                else:
                    value_is_correct = False
            else:
                value = response_json[field]
                if conditions["split"]:
                    if isinstance(value, str):
                        value = [v.strip() for v in value.split(",")]
                    elif isinstance(value, list):
                        value = [v.strip() for v in value]
                    else:
                        raise ValueError(
                            f"unexpected type for field '{field}': {type(response_json[field])}"
                        )
                    if conditions.get("force_lower", False):
                        value = [v.lower() for v in value]
                    if conditions.get("votes", None):
                        value_is_correct = set(value).issubset(set(conditions["votes"]))  # type: ignore
                else:
                    value = value.strip()
                    if conditions.get("force_lower", False):
                        value = value.lower()
                    if conditions.get("votes", None):
                        value_is_correct = value in set(conditions["votes"])  # type: ignore
            if value_is_correct:
                formatted_gpt_json[field] = value
            elif raise_on_error:
                raise ValueError(f"incorrect gpt value field={field} value={value}")
            else:
                logger.warning(f"incorrect gpt value field={field} value={value}")
    return formatted_gpt_json


def _change_protagonists(protagonists: str) -> str:
    if protagonists == "detectives":
        return "cultists"
    elif protagonists == "cultists":
        return "detectives"
    else:
        raise ValueError(f"unknown protagonists={protagonists}")


def get_truth_factor(truth: float, lie: float) -> float:
    assert truth >= 0 and lie >= 0, "truth and lie votes must be non-negative"
    if truth >= lie:
        truth_factor = (1 + truth) / (1 + lie)
        truth_factor = np.tanh(truth_factor - 1) + 1  # [1.0, 2.0]
    else:
        truth_factor = (1 + lie) / (1 + truth)
        truth_factor = np.tanh(truth_factor - 1) + 1
        truth_factor = 1 / truth_factor  # [0.5, 1.0]
    return truth_factor


def compute_scene_counters(scene: Scene) -> WinCounters:
    outcome = scene["scene_outcome"]
    protagonists = scene["scene_protagonists"]
    truth = scene["reactions"]["votes"]["truth"]
    lie = scene["reactions"]["votes"]["lie"]
    # comments = scene["reactions"]["comments"]
    truth_factor = get_truth_factor(truth, lie)
    counter_change_data: WinCounters = prompts.scene_outcomes[outcome]["counter_change"][
        protagonists
    ]
    scene_counters: WinCounters = {"cultists": 0.0, "detectives": 0.0}
    for group, counter in counter_change_data.items():
        scene_counters[group] += counter * truth_factor
    return scene_counters


def _create_new_scene_parameters(
    news_article: NewsArticle,
    scene_number: int,
    protagonists: str,
    win_counters: WinCounters,
    scene_timestamp: datetime,
) -> Scene:
    # if scene_timestamp is None:
    #     scene_timestamp = datetime.now(tz=timezone.utc)
    assert protagonists in ["detectives", "cultists"]
    n_characters = random.choice([1, 2])
    characters = random.sample(prompts.group_characters[protagonists], n_characters)
    scene_type = random.choice(prompts.scene_types)
    narrator = random.choice(prompts.witnesses)
    curr_protocol_steps = [
        x
        for x in prompts.group_protocol_steps[protagonists]
        if prompts.check_sign_conditions(x["conditions"], win_counters)
    ]
    curr_protocol = random.choice(curr_protocol_steps)
    outcome = random.choice([k for k in prompts.scene_outcomes.keys()])

    if curr_protocol["wins"] and (outcome == "success"):
        story_winner = protagonists
        scene_ends_story = True
    else:
        story_winner = "NA"
        scene_ends_story = False

    new_scene: Scene = {
        "scene_timestamp": scene_timestamp,
        "scene_number": scene_number,
        "news_title": news_article["title"],
        "news_summary": news_article["gpt_summary"],
        "news_url": news_article["url"],
        "news_source": news_article["media_source_name"],
        "news_published_at": news_article["published_at"],
        "scene_type": scene_type["name"],
        "scene_type_description": scene_type["description"],
        "scene_protagonists": protagonists,
        "scene_characters": [x["alias"] for x in characters],
        "scene_characters_description": [x["description"] for x in characters],
        "scene_narrator": narrator["alias"],
        "scene_narrator_description": narrator["description"],
        "scene_writing_style": narrator["writing_style"],
        "scene_protocol_step": curr_protocol["name"],
        "scene_protocol_step_description": curr_protocol["description"],
        "scene_subgoal": random.choice(curr_protocol["subgoals"]),
        "scene_outcome": outcome,
        "scene_outcome_description": prompts.scene_outcomes[outcome]["description"],
        "scene_first_sentence": narrator["first_sentence"],
        "scene_title": "",
        "scene_text": "",
        "scene_trustworthiness": 1,
        "scene_older_versions": [],
        "story_summary": "",
        "scene_counters": {"cultists": 0.0, "detectives": 0.0},
        "scene_ends_story": scene_ends_story,
        "story_winner": story_winner,
        "image_meta": {},
        "reactions": {
            "comments": [],
            "votes": {"truth": 0, "lie": 0, "voted_by": []},
        },
    }

    new_scene["scene_counters"] = compute_scene_counters(new_scene)

    return new_scene


def sum_scene_counters(
    win_counters_list: list[WinCounters],
) -> WinCounters:
    total_counters: WinCounters = {"cultists": 0.0, "detectives": 0.0}
    for counters in win_counters_list:
        for group, counter in counters.items():
            total_counters[group] += counter
    return total_counters


def generate_cthulhu_news(
    scenes_so_far: list[Scene],
    news_articles: list[NewsArticle],
    timestamps: list[datetime],
    gpt_model_writer: str = TEXT_MODEL_WRITER,
    gpt_model_summarizer: str = TEXT_MODEL_SUMMARIZER,
    gpt_writer_max_tokens: int = TEXT_MODEL_WRITER_MAX_TOKENS,
    gpt_summarizer_max_tokens: int = TEXT_MODEL_SUMMARIZER_MAX_TOKENS,
) -> list[Scene]:
    """Generate new Cthulhu scenes based on the news articles provided."""

    assert len(news_articles) > 0
    assert len(news_articles) == len(timestamps)
    scenes_so_far = scenes_so_far.copy()
    n_initial_scenes = len(scenes_so_far)

    scene_number = len(scenes_so_far) + 1

    curr_win_counters = sum_scene_counters([a["scene_counters"] for a in scenes_so_far])

    for news_article, timestamp in zip(news_articles, timestamps):
        if len(scenes_so_far) == 0:
            protagonists = "cultists"
        elif scenes_so_far[-1]["scene_ends_story"]:
            logger.info("the story has already ended (skip creating a new scene)...")
            return []
        else:
            protagonists = _change_protagonists(scenes_so_far[-1]["scene_protagonists"])

        scene = _create_new_scene_parameters(
            news_article=news_article,
            scene_number=scene_number,
            protagonists=protagonists,
            win_counters=curr_win_counters,
            scene_timestamp=timestamp,
        )

        scene_prompt = prompts.create_new_scene_prompt(
            scenes_so_far=scenes_so_far, new_scene=scene
        )

        response_json = get_llm_json_response(
            gpt_role=prompts.scene_role_prompt,
            gpt_query=scene_prompt,
            gpt_model=gpt_model_writer,
            gpt_max_tokens=gpt_writer_max_tokens,
        )
        scene_response_json = _parse_llm_json_response(
            expected_fields=prompts.scene_expected_json_fields,
            response_json=response_json,
            raise_on_error=True,
        )

        scene["scene_title"] = scene_response_json["scene_title"]
        scene["scene_text"] = scene_response_json["scene_text"]
        logger.debug(
            f"added gpt generated fields title='{scene['scene_title']}' & scene_text='{scene['scene_text'][:20]}...'"
        )

        summary_prompt = prompts.create_story_summary_prompt(scenes=scenes_so_far + [scene])

        response_json = get_llm_json_response(
            gpt_role=prompts.summary_role_prompt,
            gpt_query=summary_prompt,
            gpt_model=gpt_model_summarizer,
            gpt_max_tokens=gpt_summarizer_max_tokens,
        )
        summary_response_json = _parse_llm_json_response(
            expected_fields=prompts.summary_expected_json_fields,
            response_json=response_json,
            raise_on_error=True,
        )
        scene["story_summary"] = summary_response_json["story_summary"]
        logger.debug(
            f"added gpt generated fields story_summary='{scene['story_summary'][:20]}...'"
        )

        for k, v in scene.items():
            assert v is not None, f"scene parameter '{k}' is None"
            assert v != "", f"scene parameter '{k}' = ''"

        for k, _ in curr_win_counters.items():
            curr_win_counters[k] += scene["scene_counters"][k]

        scenes_so_far.append(scene)

        if scene["story_winner"] != "NA":
            logger.info(f"winner={scene['story_winner']}")
            break

        scene_number += 1
        time.sleep(0.5)

    logger.info(
        f"generated scenes count={len(scenes_so_far)} scene_ends_story={scenes_so_far[-1]['scene_ends_story']}"
    )
    new_scenes = scenes_so_far[n_initial_scenes:]
    return new_scenes


def add_cthulhu_images(scenes: list[Scene]) -> None:
    """Generate images for the Cthulhu scenes."""

    for scene in scenes:
        dalle_prompt = (
            "Create a dark retro surrealism image that depicts this alarming news article:\n\n"
        )
        dalle_prompt += scene["news_summary"] + "\n\n" + scene["scene_text"]
        title: str = scene["scene_title"]
        image_name = _str_to_filename(title)

        response = litellm.image_generation(
            model=CTHULHU_IMAGE_MODEL,  # e.g., "dall-e-3", "dall-e-2"
            prompt=dalle_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
        assert response.data is not None, "response is None"
        if hasattr(response.data[0], "revised_prompt"):
            revised_prompt = response.data[0].revised_prompt
            logger.debug(f"{revised_prompt=}")
        img_json = response.data[0].b64_json
        assert img_json is not None
        img_bytes = base64.b64decode(img_json)

        image_filename = f"{image_name}.png"
        with open(CTHULHU_IMAGE_DIR / image_filename, "wb") as f:
            f.write(img_bytes)

        # doc["cthulhu_image"] = img_bytes
        scene["image_meta"].update(
            {
                "cthulhu_image_prompt": dalle_prompt,
                "cthulhu_image_name": image_name,
                "cthulhu_image_filename": image_filename,
                "cthulhu_image_dir": str(CTHULHU_IMAGE_DIR),
            }
        )
        if revised_prompt is not None:
            scene["image_meta"].update(
                {
                    "cthulhu_image_revised_prompt": revised_prompt,
                }
            )

    logger.info(f"generated gpt cthulhu images count={len(scenes)}")


def censor_comment(
    comment: str,
    scene: Scene,
    gpt_model: str = TEXT_MODEL_WRITER,
    gpt_max_tokens: int = TEXT_MODEL_WRITER_MAX_TOKENS,
) -> prompts.CensoredComment:
    """Verify if the comment is valid for the given scene."""

    censorship_prompt = prompts.create_censorship_prompt(comment=comment, scene=scene)

    response_json = get_llm_json_response(
        gpt_role=prompts.censorship_role_prompt,
        gpt_query=censorship_prompt,
        gpt_model=gpt_model,
        gpt_max_tokens=gpt_max_tokens,
    )
    c_response_json = _parse_llm_json_response(
        expected_fields=prompts.censorship_expected_json_fields,
        response_json=response_json,
        raise_on_error=True,
    )
    preselected = {"pertinant", "matching_style"}.issubset(
        set(c_response_json["categories"])
    ) and ("unsafe" not in c_response_json["categories"])
    censored_comment: prompts.CensoredComment = {
        "censored_comment": c_response_json["censored_comment"],
        "categories": c_response_json["categories"],
        "preselected": preselected,
    }
    return censored_comment


# def _find_story_context(
#     text: str,
#     scenes: list[Scene],
# ) -> str:
#     """Find the relevant context in the story for the given text."""
#     ...

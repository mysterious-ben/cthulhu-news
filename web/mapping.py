import re
from datetime import datetime
from typing import Any, TypedDict


def _is_valid_sql_column(s):
    return bool(re.match(r"^[a-zA-Z_]+$", s))


def _is_valid_sql_column_type(s):
    return bool(re.match(r"^[a-zA-Z\s()'{}]+$", s))


class NewsArticle(TypedDict):
    title: str
    gpt_summary: str
    media_source_name: str
    url: str
    published_at: datetime
    gpt_mood: str
    gpt_sectors: list[str]
    gpt_breaking_news: bool
    gpt_like_a_hollywood_movie: bool
    gpt_trustworthy: bool
    gpt_economic_impact: str


# class WinCounters(TypedDict):
#     cultists: float
#     detectives: float


WinCounters = dict[str, float]


class TotalCounters(TypedDict):
    group_name: str
    counter: float
    limit_value: float


class Votes(TypedDict):
    truth: int
    lie: int
    voted_by: list[str]


class Comment(TypedDict):
    author: str
    comment: str
    created_at: datetime
    hidden: bool
    accepted: bool
    votes: Votes


class Reactions(TypedDict):
    comments: list[Comment]
    votes: Votes


class Scene(TypedDict):
    scene_timestamp: datetime
    scene_number: int
    news_title: str
    news_summary: str
    news_url: str
    news_source: str
    news_published_at: datetime
    scene_type: str
    scene_type_description: str
    scene_protagonists: str
    scene_characters: list[str]
    scene_characters_description: list[str]
    scene_narrator: str
    scene_narrator_description: str
    scene_writing_style: str
    scene_protocol_step: str
    scene_protocol_step_description: str
    scene_subgoal: str
    scene_outcome: str
    scene_outcome_description: str
    scene_first_sentence: str
    scene_title: str
    scene_text: str
    scene_trustworthiness: float
    scene_older_versions: list[dict]
    story_summary: str
    scene_ends_story: bool
    story_winner: str
    image_meta: dict
    reactions: Reactions
    scene_counters: WinCounters


sql_table_columns: dict[str, str] = {
    "id": "SERIAL PRIMARY KEY",  # auto
    "recorded_at": "TIMESTAMPTZ DEFAULT NOW()",  # auto
    "news_title": "TEXT NOT NULL UNIQUE",
    "news_summary": "TEXT NOT NULL",
    "news_published_at": "TIMESTAMPTZ NOT NULL",
    "scene_number": "INTEGER NOT NULL UNIQUE",
    "scene_timestamp": "TIMESTAMPTZ NOT NULL UNIQUE",
    "scene_title": "TEXT NOT NULL",
    "scene_text": "TEXT NOT NULL",
    "scene_vector": "VECTOR",
    "story_summary": "TEXT NOT NULL",
    "scene_ends_story": "BOOLEAN NOT NULL",
    "scene_older_versions": "JSONB NOT NULL",
    "news_meta": "JSONB NOT NULL",
    "scene_meta": "JSONB NOT NULL",
    "image_meta": "JSONB NOT NULL",
    "reactions": "JSONB NOT NULL",
    "scene_counters": "JSONB NOT NULL DEFAULT '{}'",
}

total_counters_table_columns: dict[str, str] = {
    "group_name": "TEXT PRIMARY KEY",
    "counter": "FLOAT NOT NULL",
    "limit_value": "FLOAT NOT NULL",
}


for k, v in sql_table_columns.items():
    assert _is_valid_sql_column(k), f"Invalid SQL column name: {k}"
    assert _is_valid_sql_column_type(v), f"Invalid SQL column type: {v}"

for k, v in total_counters_table_columns.items():
    assert _is_valid_sql_column(k), f"Invalid SQL column name: {k}"
    assert _is_valid_sql_column_type(v), f"Invalid SQL column type: {v}"


# Mapping
# Dict -> SQLite
dict_sql_mapping = {
    "scene_number": "scene_number",
    "scene_timestamp": "scene_timestamp",
    "news_title": "news_title",
    "news_summary": "news_summary",
    "news_published_at": "news_published_at",
    "scene_title": "scene_title",
    "scene_text": "scene_text",
    "story_summary": "story_summary",
    "scene_ends_story": "scene_ends_story",
    "scene_older_versions": "scene_older_versions",
    "news_url": ("news_meta", "news_url"),
    "news_source": ("news_meta", "news_source"),
    "scene_type": ("scene_meta", "scene_type"),
    "scene_type_description": ("scene_meta", "scene_type_description"),
    "scene_protagonists": ("scene_meta", "scene_protagonists"),
    "scene_characters": ("scene_meta", "scene_characters"),
    "scene_characters_description": ("scene_meta", "scene_characters_description"),
    "scene_narrator": ("scene_meta", "scene_narrator"),
    "scene_narrator_description": ("scene_meta", "scene_narrator_description"),
    "scene_writing_style": ("scene_meta", "scene_writing_style"),
    "scene_protocol_step": ("scene_meta", "scene_protocol_step"),
    "scene_protocol_step_description": (
        "scene_meta",
        "scene_protocol_step_description",
    ),
    "scene_subgoal": ("scene_meta", "scene_subgoal"),
    "scene_outcome": ("scene_meta", "scene_outcome"),
    "scene_outcome_description": ("scene_meta", "scene_outcome_description"),
    "scene_first_sentence": ("scene_meta", "scene_first_sentence"),
    "scene_trustworthiness": ("scene_meta", "scene_trustworthiness"),
    "scene_counters": "scene_counters",
    "story_winner": ("scene_meta", "story_winner"),
    "image_meta": "image_meta",
    "reactions": "reactions",
}


# SQLite -> Dict
sql_dict_mapping = {v: k for k, v in dict_sql_mapping.items()}

if (ks1 := set(dict_sql_mapping.keys())) != (ks2 := set(Scene.__annotations__.keys())):
    raise AssertionError(f"mapping keys error: key mismatch {ks1 - ks2} | {ks2 - ks1}")

if not (
    vs1 := set([v if isinstance(v, str) else v[0] for v in dict_sql_mapping.values()])
).issubset((vs2 := set(sql_table_columns.keys()))):
    raise AssertionError(f"mapping values error: not in a subset {vs1 - vs2}")


def sql_to_dict(db_scene: dict) -> Scene:
    scene: Scene = {}  # type: ignore
    for key_dict, key_sql in dict_sql_mapping.items():
        if isinstance(key_sql, str):
            scene[key_dict] = db_scene[key_sql]
        elif isinstance(key_sql, tuple) and len(key_sql) == 2:
            k1, k2 = key_sql
            scene[key_dict] = db_scene[k1][k2]
        else:
            raise ValueError(f"unexpected key_sql={key_sql}")
    return scene


def dict_to_sql(scene: Scene) -> dict[str, Any]:
    db_scene: dict[str, Any] = {}
    for key_dict, key_sql in dict_sql_mapping.items():
        if isinstance(key_sql, str):
            db_scene[key_sql] = scene[key_dict]
        elif isinstance(key_sql, tuple) and len(key_sql) == 2:
            k1, k2 = key_sql
            if k1 not in db_scene:
                db_scene[k1] = {}
            db_scene[k1][k2] = scene[key_dict]
        else:
            raise ValueError(f"unexpected key_sql={key_sql}")
    return db_scene

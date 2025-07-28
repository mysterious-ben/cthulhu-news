import atexit
import json
from datetime import datetime
from functools import partial

import psycopg
import psycopg.sql as sql
from envparse import env
from loguru import logger
from pgvector.psycopg import register_vector

# from psycopg_pool import AsyncConnectionPool
from psycopg.types.json import Jsonb, set_json_dumps, set_json_loads
from psycopg_pool import ConnectionPool

import web.llm_cthulhu_logic as logic
import web.llm_cthulhu_prompts as prompts
import web.mapping as mapping

POSTGRES_HOST = env.str("POSTGRES_HOST")
POSTGRES_PORT = env.int("POSTGRES_PORT")
POSTGRES_DB = env.str("POSTGRES_DB")
POSTGRES_USER = env.str("POSTGRES_USER")
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD")
POSTGRES_CONN_STR = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


# apgpool = AsyncConnectionPool(
#     POSTGRES_CONN_STR,
#     open=True,
#     check=AsyncConnectionPool.check_connection,
#     min_size=1,
#     max_size=5,
# )
# atexit.register(apgpool.close)


def configure(conn):
    register_vector(conn)


_pgpool = ConnectionPool(
    POSTGRES_CONN_STR,
    open=True,
    check=ConnectionPool.check_connection,
    min_size=1,
    max_size=5,
    configure=configure,
)
atexit.register(_pgpool.close)


def default_json_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


set_json_dumps(partial(json.dumps, default=default_json_converter))


set_json_loads(json.loads)  # This is the default behavior


def pg_connect() -> psycopg.Connection:
    return psycopg.connect(POSTGRES_CONN_STR, autocommit=True)


def _create_news_table() -> None:
    with _pgpool.connection() as conn:
        # conn.execute("""DROP TABLE news""")

        col_definitions = []
        for k, v in mapping.sql_table_columns.items():
            col_def = sql.SQL("{} {}").format(
                sql.Identifier(k),
                sql.SQL(v),  # type: ignore[arg-type]
            )
            col_definitions.append(col_def)

        query = sql.SQL("CREATE TABLE IF NOT EXISTS news ({})").format(
            sql.SQL(", ").join(col_definitions)
        )
        conn.execute(query)
        logger.info("initialized the local news db")


def _create_total_counters_table() -> None:
    """Create the total_counters table if it doesn't exist."""
    with _pgpool.connection() as conn:
        col_definitions = []
        for k, v in mapping.total_counters_table_columns.items():
            col_def = sql.SQL("{} {}").format(sql.Identifier(k), sql.SQL(v))  # type: ignore[arg-type]
            col_definitions.append(col_def)

        query = sql.SQL("CREATE TABLE IF NOT EXISTS total_counters ({})").format(
            sql.SQL(", ").join(col_definitions)
        )
        conn.execute(query)
        logger.info("created total_counters table")


def _init_total_counters(group_name: str, init_value: float, limit_value: float) -> None:
    """Initialize total_counters table with default values for cultists and detectives."""
    with _pgpool.connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO total_counters (group_name, counter, limit_value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (group_name) DO NOTHING""",
            (group_name, init_value, limit_value),
        )
        count = cursor.rowcount
        conn.commit()
        if count > 0:
            logger.info(f"initialized total_counters {group_name} with default values")


def init_local_news_db():
    """Internal function to initialize the local news database."""
    _create_news_table()
    _create_total_counters_table()
    for group_name, values in prompts.group_init_counters.items():
        _init_total_counters(group_name, values["init_value"], values["limit_value"])


def update_total_counter_limits() -> None:
    """Update the limit value for a specific group in the total_counters table."""
    with _pgpool.connection() as conn, conn.cursor() as cursor:
        for group_name, values in prompts.group_init_counters.items():
            new_limit = values["limit_value"]
            cursor.execute(
                """UPDATE total_counters SET limit_value = %s WHERE group_name = %s""",
                (new_limit, group_name),
            )
            conn.commit()
            logger.info(f"updated total limit for {group_name} to {new_limit}")


def _get_cthulhu_article(scene_number: int) -> list[dict]:
    """Get one Cthulhu article from the local db

    DANGER: Can be exposed to external API, so SQL injection is possible"""
    with _pgpool.connection() as conn, conn.cursor() as c:
        c.execute(
            "SELECT * FROM news WHERE scene_number = %s ORDER BY scene_timestamp DESC",
            (scene_number,),
        )
        row = c.fetchone()
        assert c.description is not None
        columns = [x[0] for x in c.description]
    if row is None:
        return []
    return [dict(zip(columns, row, strict=False))]


def _get_all_cthulhu_articles() -> list[dict]:
    """Get all the Cthulhu articles from the local db

    DANGER: Can be exposed to external API, so SQL injection is possible"""
    with _pgpool.connection() as conn, conn.cursor() as c:
        c.execute("SELECT * FROM news ORDER BY scene_number ASC")
        rows = c.fetchall()
        assert c.description is not None
        columns = [x[0] for x in c.description]
    articles = [dict(zip(columns, row, strict=False)) for row in rows]
    return articles


# def _process_if_json(value: str) -> bool:
#     if isinstance(value, str):
#         try:
#             json.loads(value)
#             return True
#         except json.JSONDecodeError:
#             return False
#     else:
#         return False


def load_formatted_cthulhu_articles(scene_number: int | None = None) -> list[mapping.Scene]:
    """Get and format Cthulhu article(s) from the local db

    DANGER: Can be exposed to external API, so SQL injection is possible
    """
    start = datetime.now()
    logger.debug(f"getting all Cthulhu articles from the local db scene_number={scene_number}...")
    if scene_number is None:
        db_cthulhu_articles = _get_all_cthulhu_articles()
    else:
        db_cthulhu_articles = _get_cthulhu_article(scene_number=scene_number)
    # for db_article in db_cthulhu_articles:
    #     for k, v in db_article.items():
    #         db_article[k] = _process_if_json(v)
    elapsed = (datetime.now() - start).total_seconds()
    logger.info(
        f"fetched and processed all Cthulhu articles from the local db scene_number={scene_number} "
        f"n={len(db_cthulhu_articles)} elapsed={elapsed:.2f}s"
    )

    cthulhu_articles: list[mapping.Scene] = []
    for db_article in db_cthulhu_articles:
        a = mapping.sql_to_dict(db_article)
        cthulhu_articles.append(a)
    return cthulhu_articles


def insert_cthulhu_articles(cthulhu_articles: list[mapping.Scene]) -> int:
    """Insert Cthulhu articles into the local db

    DANGER: Can be exposed to external API, so SQL injection is possible
    """

    if len(cthulhu_articles) == 0:
        return 0

    # Convert records to PostgreSQL format
    docs_to_insert: list[dict] = []
    for a in cthulhu_articles:
        if (sk1 := set(a.keys())) != (sk2 := set(mapping.dict_sql_mapping.keys())):
            raise AssertionError(f"inserted scene key mismatch: {sk1 - sk2} | {sk2 - sk1}")
        db_scene = mapping.dict_to_sql(a)
        for k, v in db_scene.items():
            if isinstance(v, dict):
                db_scene[k] = Jsonb(
                    v,
                )
        docs_to_insert.append(db_scene)

    # Insert records
    sql_keys = list(docs_to_insert[0].keys())
    columns = sql.SQL(", ").join(sql.Identifier(k) for k in sql_keys)
    placeholders = sql.SQL(", ").join(sql.Placeholder(k) for k in sql_keys)

    query = sql.SQL(
        "INSERT INTO news ({}) VALUES ({}) ON CONFLICT (scene_number) DO NOTHING"
    ).format(columns, placeholders)

    with _pgpool.connection() as conn:
        with conn.cursor() as c:
            c.executemany(query, docs_to_insert)
            n_inserted = c.rowcount
        conn.commit()
    logger.info(f"inserted Cthulhu articles into the local db n={n_inserted}")
    return n_inserted


def latest_scene_timestamp() -> datetime | None:
    with _pgpool.connection() as conn:
        row = conn.execute("""SELECT max(scene_timestamp) FROM news""").fetchone()
    if row is None or row[0] is None:
        return None
    return row[0]


def get_cthulhu_article_votes(scene_number: int) -> dict | None:
    """Get votes for an Chthulhu article

    DANGER: Can be exposed to external API, so SQL injection is possible
    """
    with (
        _pgpool.connection() as conn,
        conn.execute(
            """SELECT reactions->'votes' FROM news WHERE scene_number = %s""", (scene_number,)
        ) as c,
    ):
        rows = c.fetchone()
    if rows is None:
        return None
    return rows[0]


def upd_cthulhu_article_counters(
    scene_number: int, article: mapping.Scene, update_total_counters: bool
) -> None:
    """Update counters for an Chthulhu article

    Also updated the article object
    """

    assert scene_number == article["scene_number"]
    old_counters = article["scene_counters"].copy()
    new_counters = logic.compute_scene_counters(scene=article)
    article["scene_counters"] = new_counters
    with _pgpool.connection() as conn:
        query = sql.SQL("""\
UPDATE news
SET scene_counters = {counters}::jsonb
WHERE scene_number = {scene_number}
""").format(
            counters=Jsonb(new_counters),
            scene_number=sql.Placeholder(),
        )
        conn.execute(query, (scene_number,))
        conn.commit()
        logger.info(f"updated win counters for article {scene_number} with {new_counters}")

    if update_total_counters:
        counter_diff = {k: new_counters[k] - old_counters.get(k, 0) for k in new_counters}
        inc_total_counters([counter_diff])


def inc_cthulhu_article_vote(scene_number: int, vote: str, user: str | None = None):
    """Increment votes for an Chthulhu article

    DANGER: Can be exposed to external API, so SQL injection is possible
    """
    if user is not None:
        raise NotImplementedError

    with _pgpool.connection() as conn:
        query = sql.SQL("""\
UPDATE news
SET reactions = jsonb_set(
    reactions,
    {path},
    to_jsonb(COALESCE((reactions->'votes'->>{vote_key})::int, 0) + 1)
)
WHERE scene_number = {scene_number}
""").format(
            path=sql.Literal(["votes", vote]),
            vote_key=sql.Literal(vote),
            scene_number=sql.Placeholder(),
        )
        conn.execute(query, (scene_number,))
        conn.commit()


def submit_cthulhu_article_comment(
    scene_number: int, comment_json: mapping.Comment, user: str | None
) -> None:
    """Submit a comment for an Chthulhu article

    DANGER: Can be exposed to external API, so SQL injection is possible
    """
    if user is not None:
        raise NotImplementedError

    with _pgpool.connection() as conn:
        query = sql.SQL("""\
UPDATE news
SET reactions = jsonb_set(
    reactions,
    {comments_path},
    (reactions->'comments') || {comment_array}::jsonb
)
WHERE scene_number = {scene_number}
""").format(
            comments_path=sql.Literal(["comments"]),
            comment_array=sql.Placeholder(),
            scene_number=sql.Placeholder(),
        )
        conn.execute(query, (Jsonb([comment_json]), scene_number))
        conn.commit()


def add_cthulhu_scene_update(scene_number: int, scene_update: str) -> None:
    """Add a scene update to the scene_updates array for a specific scene.

    DANGER: Can be exposed to external API, so SQL injection is possible
    """
    with _pgpool.connection() as conn:
        query = sql.SQL("""\
UPDATE news
SET scene_updates = array_append(scene_updates, %s)
WHERE scene_number = %s
""")
        conn.execute(query, (scene_update, scene_number))
        conn.commit()
        logger.info(f"added scene update to scene {scene_number}: {scene_update[:50]}...")


def get_total_counters() -> dict[str, mapping.TotalCounters]:
    """Get current total counters for all groups."""
    with _pgpool.connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT group_name, counter, limit_value FROM total_counters")
        rows = cursor.fetchall()

        result = {}
        for row in rows:
            group_name, counter, limit_value = row
            result[group_name] = mapping.TotalCounters(
                group_name=group_name, counter=counter, limit_value=limit_value
            )
        return result


def inc_total_counters(win_counters_change_list: list[mapping.WinCounters]) -> None:
    """Update total counters by applying the differences from a scene."""
    win_counters_change = logic.sum_scene_counters(win_counters_change_list)
    with _pgpool.connection() as conn, conn.cursor() as cursor:
        query = sql.SQL("""
                UPDATE total_counters
                SET counter = counter + {counter}
                WHERE group_name = {group_name}
            """).format(
            counter=sql.Placeholder("counter"),
            group_name=sql.Placeholder("group_name"),
        )

        for group_name, group_counter in win_counters_change.items():
            cursor.execute(query, {"counter": group_counter, "group_name": group_name})
        conn.commit()
        logger.info(f"increased total counters: {win_counters_change}")


def set_total_counters(win_counters: mapping.WinCounters) -> None:
    """Update total counters by applying the differences from a scene."""
    with _pgpool.connection() as conn, conn.cursor() as cursor:
        query = sql.SQL("""
                UPDATE total_counters
                SET counter = {counter}
                WHERE group_name = {group_name}
            """).format(
            counter=sql.Placeholder("counter"),
            group_name=sql.Placeholder("group_name"),
        )

        for group_name, group_counter in win_counters.items():
            cursor.execute(query, {"counter": group_counter, "group_name": group_name})
        conn.commit()
        logger.info(f"set total counters: {win_counters}")


def upd_all_counters() -> None:
    """Update all counters in the total_counters table."""
    articles = load_formatted_cthulhu_articles()
    for article in articles:
        upd_cthulhu_article_counters(
            scene_number=article["scene_number"], article=article, update_total_counters=False
        )
    total_counters = logic.sum_scene_counters([a["scene_counters"] for a in articles])
    set_total_counters(total_counters)


def regenerate_all_embeddings() -> None:
    """Regenerate embeddings for all scenes."""
    articles = load_formatted_cthulhu_articles()
    logger.info(f"Regenerating embeddings for {len(articles)} scenes")

    for i, article in enumerate(articles):
        try:
            embedding = logic.generate_embedding_vector(article["scene_text"])
            with _pgpool.connection() as conn:
                conn.execute(
                    "UPDATE news SET scene_vector = %s::vector WHERE scene_number = %s",
                    (embedding.tolist(), article["scene_number"]),
                )
                conn.commit()
            if (i + 1) % 5 == 0:
                logger.info(f"Processed {i + 1}/{len(articles)} scenes")
        except Exception as e:
            logger.error(f"Failed to process scene {article['scene_number']}: {e}")

    logger.info("Embedding regeneration complete")

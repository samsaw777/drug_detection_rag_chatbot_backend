
from schemas.analyse_query import InteractionPair


def build_canonical_key(interactions: list[InteractionPair]) -> str:
    """
    Build a canonical cache key from interaction pairs.
    Sorts entity names alphabetically for consistent matching.
    """
    entities = set()
    for pair in interactions:
        entities.add(pair.drug.strip().lower())
        entities.add(pair.target.strip().lower())

    if not entities:
        return ""

    return "drug interaction: " + " ".join(sorted(entities))


async def check_cache(canonical_key: str, pool) -> dict | None:
    """
    Check if a canonical query exists in the cache.
    If found, increments hit_count and returns the cached response.
    """
    if not canonical_key:
        return None

    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT llm_response FROM frequent_queries
                    WHERE canonical_query = %s
                    LIMIT 1
                    """,
                    (canonical_key,),
                    prepare=False,
                )
                row = await cur.fetchone()

                if row:
                    await cur.execute(
                        """
                        UPDATE frequent_queries
                        SET hit_count = hit_count + 1,
                            last_asked_at = NOW()
                        WHERE canonical_query = %s
                        """,
                        (canonical_key,),
                        prepare=False,
                    )
                    return {"llm_response": row[0]}

    except Exception as e:
        print(f"Cache check error: {e}")

    return None


async def store_cache(
    canonical_key: str,
    llm_response: str,
    drug_names: list[str],
    intent_category: str,
    pool,
) -> None:
    if not canonical_key or not llm_response:
        print(f"Skipping cache store — empty key or response")
        return

    print(f"Attempting to store cache for: {canonical_key}")
    print(f"LLM response length: {len(llm_response)}")
    print(f"Drug names: {drug_names}")

    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO frequent_queries (
                        canonical_query,
                        llm_response,
                        drug_names,
                        intent_category
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (canonical_query)
                    DO UPDATE SET
                        hit_count = frequent_queries.hit_count + 1,
                        last_asked_at = NOW()
                    """,
                    (canonical_key, llm_response, drug_names, intent_category),
                    prepare=False,
                )
                print("Cache store query executed successfully")
    except Exception as e:
        print(f"Cache store error: {e}")
from schemas.analyse_query import InteractionPair


def build_query(interaction: InteractionPair) -> tuple[str | None, list, str | None]:
    """
    Takes a single InteractionPair and returns (sql, params, error).
    """

    if interaction.type == "drug-drug":
        sql = """
            SELECT DISTINCT
                dtd.drug1_name,
                dtd.drug2_name,
                dtd.interaction_description,
                di1.summary AS drug1_summary,
                di1.drug_type AS drug1_type,
                di2.summary AS drug2_summary,
                di2.drug_type AS drug2_type
            FROM dtd_interaction_information dtd
            JOIN drug_info di1 ON dtd.db_drug1_id = di1.db_drug_id
            JOIN drug_info di2 ON dtd.db_drug2_id = di2.db_drug_id
            WHERE (
                (LOWER(dtd.drug1_name) = LOWER(%s) OR dtd.db_drug1_id IN (
                    SELECT ds.db_drug_id FROM drug_synonyms ds WHERE LOWER(ds.drug_name) = LOWER(%s)
                ))
                AND
                (LOWER(dtd.drug2_name) = LOWER(%s) OR dtd.db_drug2_id IN (
                    SELECT ds.db_drug_id FROM drug_synonyms ds WHERE LOWER(ds.drug_name) = LOWER(%s)
                ))
            )
            OR
            (
                (LOWER(dtd.drug1_name) = LOWER(%s) OR dtd.db_drug1_id IN (
                    SELECT ds.db_drug_id FROM drug_synonyms ds WHERE LOWER(ds.drug_name) = LOWER(%s)
                ))
                AND
                (LOWER(dtd.drug2_name) = LOWER(%s) OR dtd.db_drug2_id IN (
                    SELECT ds.db_drug_id FROM drug_synonyms ds WHERE LOWER(ds.drug_name) = LOWER(%s)
                ))
            )
            LIMIT 1
        """
        params = [
            interaction.drug, interaction.drug,
            interaction.target, interaction.target,
            interaction.target, interaction.target,
            interaction.drug, interaction.drug,
        ]
        return sql, params, None

    if interaction.type == "drug-food":
        sql = """
            SELECT DISTINCT
                ii.drug_name,
                ii.food_herb_name,
                ii.f_h_type,
                ii.effect,
                ii.result,
                ii.conclusion,
                ii.relationship_classification,
                ii.experimental_species,
                ii.dosage_form,
                ii.potential_target,
                di.summary AS drug_summary,
                di.drug_type,
                fd.food_description,
                fd.food_group
            FROM interaction_information ii
            JOIN drug_info di ON ii.db_drug_id = di.db_drug_id
            JOIN food_data fd ON ii.db_food_herb_id = fd.db_food_id
            WHERE (
                LOWER(ii.drug_name) = LOWER(%s)
                OR ii.db_drug_id IN (
                    SELECT ds.db_drug_id FROM drug_synonyms ds WHERE LOWER(ds.drug_name) = LOWER(%s)
                )
            )
            AND (
                LOWER(ii.food_herb_name) = LOWER(%s)
                OR ii.db_food_herb_id IN (
                    SELECT db_food_id FROM food_data
                    WHERE LOWER(common_name) = LOWER(%s)
                    OR LOWER(scientific_name) = LOWER(%s)
                )
            )
            AND ii.f_h_type = 'F'
            LIMIT 1
        """
        params = [
            interaction.drug, interaction.drug,
            interaction.target, interaction.target, interaction.target,
        ]
        return sql, params, None

    if interaction.type == "drug-herb":
        sql = """
            SELECT DISTINCT
                ii.drug_name,
                ii.food_herb_name,
                ii.f_h_type,
                ii.effect,
                ii.result,
                ii.conclusion,
                ii.relationship_classification,
                ii.experimental_species,
                ii.dosage_form,
                ii.potential_target,
                di.summary AS drug_summary,
                di.drug_type,
                hd.herb_function,
                hd.indication,
                hd.toxicity,
                hd.therapeutic_class,
                hd.properties AS herb_properties
            FROM interaction_information ii
            JOIN drug_info di ON ii.db_drug_id = di.db_drug_id
            JOIN herb_data hd ON ii.db_food_herb_id = hd.db_herb_id
            WHERE (
                LOWER(ii.drug_name) = LOWER(%s)
                OR ii.db_drug_id IN (
                    SELECT ds.db_drug_id FROM drug_synonyms ds WHERE LOWER(ds.drug_name) = LOWER(%s)
                )
            )
            AND (
                LOWER(ii.food_herb_name) = LOWER(%s)
                OR ii.db_food_herb_id IN (
                    SELECT hd2.db_herb_id FROM herb_data hd2
                    JOIN herb_synonyms hs ON hd2.fhdi_herb_id = hs.fhdi_herb_id
                    WHERE LOWER(hs.herb_name) = LOWER(%s)
                )
            )
            AND ii.f_h_type = 'H'
            LIMIT 1
        """
        params = [
            interaction.drug, interaction.drug,
            interaction.target, interaction.target,
        ]
        return sql, params, None

    return None, [], f"Unknown interaction type: {interaction.type}"


async def execute_queries(interactions: list[InteractionPair], pool) -> list[dict]:
    """
    Takes a list of InteractionPairs and a connection pool.
    Builds and executes a query for each pair.
    """
    results = []

    for interaction in interactions:
        sql, params, error = build_query(interaction)

        result_entry = {
            "interaction": {
                "type": interaction.type,
                "drug": interaction.drug,
                "target": interaction.target,
            },
            "data": [],
            "error": error,
        }

        if error:
            results.append(result_entry)
            continue

        try:
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, params, prepare=False)
                    columns = [desc[0] for desc in cur.description]
                    rows = await cur.fetchall()
                    result_entry["data"] = [
                        dict(zip(columns, row)) for row in rows
                    ]
        except Exception as e:
            print(f"Query error: {e}")
            result_entry["error"] = f"Database query failed: {str(e)}"

        results.append(result_entry)

    return results
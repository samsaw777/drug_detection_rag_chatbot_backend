from schemas.analyse_query import InteractionPair

def build_query(interaction: InteractionPair) -> tuple[str | None, list, str | None]:
    if interaction.type == "drug-drug":
        return None, [], "Drug-to-drug interaction data is not yet available in our database. This feature is coming soon!"

    if interaction.type == "drug-food":
        sql = """
            SELECT 
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
            WHERE LOWER(ii.drug_name) = LOWER(%s)
              AND LOWER(ii.food_herb_name) = LOWER(%s)
              AND ii.f_h_type = 'F'
        """
        params = [interaction.drug, interaction.target]
        return sql, params, None

    if interaction.type == "drug-herb":
        sql = """
            SELECT 
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
            WHERE LOWER(ii.drug_name) = LOWER(%s)
              AND LOWER(ii.food_herb_name) = LOWER(%s)
              AND ii.f_h_type = 'H'
        """
        params = [interaction.drug, interaction.target]
        return sql, params, None

    return None, [], f"Unknown interaction type: {interaction.type}"


async def execute_queries(interactions: list[InteractionPair], pool) -> list[dict]:
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
                    print(f"Running SQL: {sql}")
                    print(f"With params: {params}")
                    await cur.execute(sql, params, prepare=False)
                    columns = [desc[0] for desc in cur.description]
                    rows = await cur.fetchall()
                    print(f"Rows returned: {len(rows)}")
                    result_entry["data"] = [
                        dict(zip(columns, row)) for row in rows
                    ]
        except Exception as e:
            print("Error", e)
            result_entry["error"] = f"Database query failed: {str(e)}"

        results.append(result_entry)

    return results

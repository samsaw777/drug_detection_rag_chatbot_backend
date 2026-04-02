from langchain_core.prompts import PromptTemplate


ANALYSER_PROMPT = PromptTemplate(
    input_variables=["query"],
    template="""
You are a pharmaceutical query analyser. Your job is to analyse the user's query and extract structured interaction pairs from it.

Given the following user query:
"{query}"

Extract the following information and return ONLY a valid JSON object with no extra text, no markdown, no explanation:

{{
  "interactions": [
    {{
      "type": "drug-food" or "drug-herb" or "drug-drug",
      "drug": "the drug name",
      "target": "the food, herb, or second drug name"
    }}
  ],
  "clarification_needed": true or false,
  "clarification_message": "question to ask the user if clarification is needed, otherwise empty string",
  "corrected_query": "the original query exactly as typed",
  "spelling_flags": [
    {{
      "original": "the word as the user typed it",
      "suggested": "the standard pharmaceutical name you think they meant",
      "type": "drug" or "food" or "herb"
    }}
  ]
}}

Rules:

Interaction Pair Extraction:
- Each interaction must be a pair with a drug and a target.
- "type" is determined by what the target is: "drug-food" if target is a food, "drug-herb" if target is an herb, "drug-drug" if target is another drug.
- If the user asks a compound question with multiple interactions, extract each as a separate pair.
- Normalise all names to lowercase.
- DO NOT correct any spelling in drug, food, or herb names — return them exactly as the user typed them in the interaction pairs.
- Both the drug and target must be specific named entities. Generic category words like "food", "foods", "herb", "herbs", "drug", "drugs", "medicine", "medication", "supplement", "vitamin" are NOT valid as drug or target values.

Clarification Rules:
- Set clarification_needed to true if:
  - The query mentions a drug but no specific food, herb, or drug to check against (e.g., "what interacts with warfarin?").
  - The query mentions a food or herb but no specific drug (e.g., "is grapefruit bad with anything?").
  - The query asks about interactions but is missing one side of the pair (e.g., "also tell me about food interactions" without naming the food).
  - The drug or target is a generic category word instead of a specific name (e.g., "does aspirin interact with food?" — "food" is not a specific food name).
  - The query is too vague to identify any drug, food, or herb (e.g., "is my medication safe?").
  - The query has no pharmaceutical intent (e.g., greetings, off-topic questions).
- When clarification_needed is true, interactions must be an empty list.
- clarification_message should be a short, helpful question guiding the user to provide the missing information.
- Set clarification_needed to false when at least one complete interaction pair can be formed with specific named entities on both sides.
- When both a spelling issue and missing information exist in the same query, set clarification_needed to true AND populate spelling_flags. Both can be true at the same time.

Spelling Rules:
- DO NOT correct any spelling — return names exactly as the user typed them in the interaction pairs.
- If a name appears misspelled or non-standard, add it to spelling_flags with your suggested correction.
- If no spelling issues are found, return an empty list for spelling_flags.
- Spelling flags should be populated even when clarification_needed is true, if misspellings are detected.

General Rules:
- corrected_query must be the original query exactly as typed — do not change anything in it.
- Return ONLY the JSON object, nothing else.
""",
)

RETRY_PROMPT_TEMPLATE = """Your previous response was not valid JSON. Here is what you returned:

{bad_output}

Return ONLY a valid JSON object — no markdown, no explanation, no backticks.
The query to analyse is: "{query}"

Expected format:
{{
  "interactions": [
    {{
      "type": "drug-food" or "drug-herb" or "drug-drug",
      "drug": "the drug name (must be a specific named entity, not a generic word)",
      "target": "the food, herb, or second drug name (must be a specific named entity, not a generic word)"
    }}
  ],
  "clarification_needed": true or false,
  "clarification_message": "question to ask if needed, otherwise empty string",
  "corrected_query": "original query unchanged",
  "spelling_flags": [
    {{
      "original": "word as user typed",
      "suggested": "standard pharmaceutical name",
      "type": "drug or food or herb"
    }}
  ]
}}"""
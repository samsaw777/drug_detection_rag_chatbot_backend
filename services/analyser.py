from schemas import QueryResponse
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
API_KEY = os.getenv('GOOGLE_API_KEY')

ANALYSER_PROMPT = PromptTemplate(
                    input_variables=["query"],
                    template =
                    """
                    You are a pharmaceutical query analyser. Your job is to analyse the user's query and extract structured information from it.

                    Given the following user query:
                    "{query}"

                    Extract the following information and return ONLY a valid JSON object with no extra text, no markdown, no explanation:

                    {{
                    "interaction_types": [list of applicable types from: "drug-drug", "drug-food", "drug-herb"],
                    "drugs": [list of drug names mentioned, spelling corrected],
                    "foods": [list of food items mentioned, spelling corrected],
                    "herbs": [list of herbal/medicinal herb names mentioned, spelling corrected],
                    "corrected_query": "the original query with all spelling corrections applied"
                    }}

                    Rules:
                    - interaction_types must only include types relevant to the query.
                    - If no drugs are mentioned, return an empty list for drugs.
                    - If no foods are mentioned, return an empty list for foods.
                    - If no herbs are mentioned, return an empty list for herbs.
                    - Normalise all names to lowercase.
                    - Correct any misspelled drug, food, or herb names to their standard names.
                    - In corrected_query, fix spelling of medical/pharmaceutical terms only, keep rest of the sentence as is.
                    - Return ONLY the JSON object, nothing else.
                    """
                    )

class QueryAnalyser:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model = model, 
            google_api_key = api_key,
            temperature = 0
        )
        self.prompt = ANALYSER_PROMPT
    
    def analyse(self, query: str) -> QueryResponse:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        formatted_prompt = self.prompt.format(query=query)
        response = self.llm.invoke(formatted_prompt)
        raw_output = str(response.content).strip()
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw output: {raw_output}")

        return QueryResponse(
            interactions=parsed.get("interactions", []),
            clarification_needed=parsed.get("clarification_needed", []),
            clarification_message=parsed.get("clarification_message", []),
            corrected_query=parsed.get("corrected_query", []),
            final_output=parsed.get("final_output", ""),
        )
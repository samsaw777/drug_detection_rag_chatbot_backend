from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import os
import json
from dotenv import load_dotenv
from typing import Optional, Literal

from schemas import FrequentQuery, CanonicalQuery
from config import get_settings
import psycopg2

settings= get_settings()

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

FETCHER_PROMPT=PromptTemplate(
    input_variables= ["query"],
    template="""
        You are an expert user query canonicalizer who generalizes frequently inputted user queries. Your task is to extract the core intent of the inputted user query on drug-drug, drug-food and drug-herb interactions and convert it into a generic, uniform format while following the given instructions:

        1. Rewrite the query in the canonical format: "action: [item1] [item2]...[itemN]". Ensure that the items are the key drugs, food or herbs present in the query outputted in alphabetical order.
        2. Do not include greetings, punctuation, conversational phrases such as 'hi', 'hello' in the output.
        3. In case user query consists of medically or drug irrelevant topics, output exactly "NIL".
        4. Do not alter the item names. Format them in lowercase as per requirement.
        5. Ensure that the output is in JSON format.
        The user query to convert is: {query}

        Extract the following information and return ONLY a valid JSON object with no extra text, no markdown, no explanation:

        {{
                    "canonical_query": "user query in canonical format,
                    "drug_names": [list of drug/food/herb names mentioned],
                    "intent_category": "interaction" | "other", 
        }}

                    Rules:
                    - canonical query must strictly follow the mentioned format.
                    - drug_names must include all interacting components that the user is asking about, return an empty list if nothing is mentioned.
                    - intent_category must categorize whether the user wants to know about an interaction or other information.
                    - Normalise all names to lowercase. 
                    - Return ONLY the JSON object, nothing else.
        

        Example:
        Inputted user query: "Is it safe to take Warfarin with Advil?"
        Output: {{"canonical_query": "drug interaction: advil warfarin",
                  "drug_names" : ['advil', 'warfarin'],
                  "intent_category": "interaction"
          }}

        Inputted user query: "What side effects do Warfarin cause when taken with Advil?"
        Output: {{"canonical_query": "drug interaction: advil warfarin",
                  "drug_names" : ['advil', 'warfarin'],
                  "intent_category": "interaction"
          }}

        Inputted user query: "Is it a sunday today?"
        Output: {{"canonical_query": "NIL",
                  "drug_names" : [],
                  "intent_category": "other"
          }}
    """
)

from psycopg2.extras import RealDictCursor

class FrequentFetcherCapture:

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):  
        self.llm = ChatGoogleGenerativeAI(
            model = model, 
            google_api_key = api_key,
            temperature = 0
        )
        self.prompt = FETCHER_PROMPT
        self.conn = psycopg2.connect(settings.DATABASE_URL)

    async def canonicalize(self, user_query: str) -> str:
        if not user_query:
            raise ValueError("Empty query received..")
    
        formatted_prompt = self.prompt.format(query=user_query)

        response =await self.llm.ainvoke(formatted_prompt)
        raw_output = str(response.content).strip()
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(raw_output)
            return CanonicalQuery(
            canonical_query=  parsed.get("canonical_query", ""),
            drug_names= parsed.get("drug_names", []),
            intent_category= parsed.get("intent_category","")
        )
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw output: {raw_output}")

        

    def check_frequent_prompts(self, query: CanonicalQuery): 
        """
        Check if canonical query exists in the db
        """ 
        if query.canonical_query == "NIL":
            return None

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM frequent_queries
                WHERE canonical_query = %s 
                LIMIT 1
            """, (query.canonical_query,))
            row = cur.fetchone()

        if row:
            cached = FrequentQuery(**row) 
            self.add_frequent_query(query, llm_response=cached.llm_response )
            return cached.llm_response
         

        return None

    def add_frequent_query(self, data: CanonicalQuery, llm_response: str) :
        """
        Inserts a record or updates hit_count if it already exists.
        Returns the saved record as a dictionary.
        """ 
        
        sql = """
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
            RETURNING *;
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur: 
                cur.execute(sql, (
                    data.canonical_query, 
                    llm_response, 
                    data.drug_names, 
                    data.intent_category
                ))
                self.conn.commit()

                print("Inserted recording into database!")

                return cur.fetchone()
        except Exception as e:
            self.conn.rollback()
            print(f"Error saving: {e}")
            return None
    

import asyncio

async def main():
    f = FrequentFetcherCapture(api_key=settings.GEMINI_API_KEY)
    mock_data =await f.canonicalize("is it alright to take warfarin with morphine?")
    
    # result = f.add_frequent_query(mock_data, llm_response="Is there anything else I can assist you with?")
    print(mock_data)

if __name__ == "__main__":
    asyncio.run(main()) 

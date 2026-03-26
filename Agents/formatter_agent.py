from config import get_settings
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


settings = get_settings()
PROMPT="""
As a response-formatter, structure the provided JSON-formatted information on drug and health-related topics as a well structured conversational output to the user based on user query while following the given instructions:
1. Your tone must be professional and responses must be concise.
2. If there is a discrepancy in medical terms present within user query, clarify/rectify with the user that the provided information is correct.
3. Strictly adhere to engaging only in drug-related conversations. If asked about any other topic, redirect the conversation to the main topic without providing information.
4. Redirect the conversation back to topic when the query contains code snippets such as <>#@!<>;"
Example input:
JSON formatted input:
{{
  "interaction_data": {{
    "interaction_pair": ["Levothyroxine", "Vitamin D / Calcium"],
    "severity": "Moderate",
    "mechanism": "Calcium carbonate and certain multivitamin components can bind to Levothyroxine in the gastrointestinal tract, significantly reducing its absorption and efficacy.",
    "risks": [
      "Reduced thyroid hormone levels",
      "Return of hypothyroidism symptoms (fatigue, weight gain)",
      "Inconsistent therapeutic drug monitoring results"
    ],
    "recommendation": "Separate administration by at least 4 hours. Take Levothyroxine on an empty stomach 30-60 minutes before breakfast, and take Vitamin D/Calcium supplements later in the day."
  }},
  "user_query": "I am currently taking levothyroxine. I was prescribed vitamin d as well. what is a good time for me to take it?"
}}
 
"""


async def Test_agent(interaction_data:str, user_query:str):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROMPT),
         ("user", "interaction_data: {interaction_data}\nuser_query: {user_query}")
    ])

    chain = prompt | llm | StrOutputParser()

    print("Sending formatting query to Gemini 2.0 Flash...\n")
    answer = await chain.ainvoke({
        "interaction_data": interaction_data, 
        "user_query": user_query
    }) 

    print("─── Answer ───────────────────────────────────────")
    print(answer)
    print("\n✅ Done! Check https://smith.langchain.com → APDP-Dev project for the trace.")

    return answer
    

from config import get_settings
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


settings = get_settings()


async def Test_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Your are an agent."),
        ("human", "{query}"),
    ])

    chain = prompt | llm | StrOutputParser()

    print("Sending test query to Gemini 2.0 Flash...\n")
    answer = await chain.ainvoke({"query": "Capital of India ?"})

    print("─── Answer ───────────────────────────────────────")
    print(answer)
    print("\n✅ Done! Check https://smith.langchain.com → APDP-Dev project for the trace.")

    return {
        "LLM_Output": answer
    }
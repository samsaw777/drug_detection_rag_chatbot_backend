import pytest
from config import get_settings
from services import FrequentFetcherCapture, QueryAnalyser
import os
from dotenv import load_dotenv
import asyncio
from schemas import CanonicalQuery
load_dotenv()
"""
Test cases for testing services
"""


settings= get_settings()

@pytest.fixture(scope="session")
def fetcher():
    return FrequentFetcherCapture(
        api_key= settings.GEMINI_API_KEY
    )


@pytest.fixture(scope="session")
def query_analyzer():
    return QueryAnalyser(
        api_key=settings.GEMINI_API_KEY
    )
 

def test_freq_fetch_capture(fetcher):
    """Confirm that the Frequent fetch object has been created"""
    
    assert fetcher is not None
 
@pytest.mark.anyio
async def test_canonicalize_manual(fetcher):
    """
    Check if user query is being converted to expected canonical form
    """
    result1 = await fetcher.canonicalize("can i take aspirin and warfarin together")
    canonical_query1= CanonicalQuery(
                                    canonical_query= "drug interaction: aspirin warfarin",
                                    drug_names= ["aspirin","warfarin"],
                                    intent_category= "interaction"
    )

    result2 = await fetcher.canonicalize("what is the weather like today?")
    canonical_query2= CanonicalQuery(
        canonical_query='NIL',
          drug_names=[] ,
          intent_category='other'
    )
    print("RESULT", result2)
    assert result1 == canonical_query1
    assert result2==canonical_query2

def test_check_frequent_prompts(fetcher ):
    """
        Check if canonical query exists in the db
    """ 

    canonical_query1= CanonicalQuery(
        canonical_query='NIL',
          drug_names=[] ,
          intent_category='other'
    )
    result1= fetcher.check_frequent_prompts(canonical_query1)

    canonical_query2= CanonicalQuery(
        canonical_query= "drug interaction: aspirin warfarin",
        drug_names= ["aspirin","warfarin"],
        intent_category= "interaction"
    )
    result2= fetcher.check_frequent_prompts(canonical_query2)

    assert result1 == None
    assert result2 ==  """I couldn't find interaction data for that combination in our database. Drug-to-drug interaction data is not yet available in our system, but this feature is coming soon!"""



import os
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException
import psycopg2
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# Define your database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize the database connection
conn = psycopg2.connect(DATABASE_URL)

model = SentenceTransformer('all-MiniLM-L6-v2')

# Define a Pydantic model for the response
class Mission(BaseModel):
    ein: int
    name: str
    mission: str
    revenue: int
    city: str
    state: str
    zip: str

    # is_foundation BOOLEAN DEFAULT FALSE,
    # phone TEXT,
    # officer_name TEXT,
    # officer_title TEXT,
    # officer_phone TEXT,
    # cy_total_revenue_amount BIGINT,
    # cy_contributions_grants_amount BIGINT,
    # cy_revenues_less_expenses_amount BIGINT,
    # all_other_contributions_amount BIGINT,
    # total_contributions_amount BIGINT,
    # total_program_service_expenses_amount BIGINT,
    # donated_services_and_use_fclts_amount BIGINT,
    # cy_program_service_revenue_amount BIGINT,
    # gross_receipts_amount BIGINT,


# Create an instance of APIRouter
router = APIRouter()

# keep deprecated function until lifespan is supported in APIRouter
@router.on_event("shutdown")
async def shutdown():
    conn.close()
    #await database.disconnect()

class MatchesRequest(BaseModel):
    mission: str

"""
To get similar missions, you can use something like the following curl command:
curl -X GET "http://localhost:8000/similar_missions?mission=End%20world%20hunger" -H "accept: application/json"
"""
@router.get("/similar_missions", response_model=List[Mission])
async def get_similar_missions(mission: str):
    embedding = model.encode(mission).tolist()
    cur=conn.cursor()
    query = "SELECT ein, name, mission, revenue, city, state, zip FROM nonprofits ORDER BY mission_vector <-> %s::vector LIMIT %s"
    try:
        cur.execute(query, (list(embedding), 30))
        results = cur.fetchall()
        return [Mission(ein=result[0], name=result[1], mission=result[2], revenue=result[3], city=result[4], state=result[5], zip=result[6]) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()


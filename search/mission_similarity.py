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
    query = "SELECT ein, name, mission FROM nonprofits ORDER BY mission_vector <-> %s::vector LIMIT %s"
    try:
        cur.execute(query, (list(embedding), 3));
        results = cur.fetchall()
        return [Mission(ein=result[0], name=result[1], mission=result[2]) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()

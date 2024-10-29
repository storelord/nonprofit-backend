#!/usr/bin/env python3

from datetime import datetime
from sentence_transformers import SentenceTransformer, util
import numpy as np
import psycopg2
import csv

file_path = 'nonprofits3.tsv'

# Define the list of charity mission summaries
charity_missions = [
    "Charity focused on providing clean water access globally.",
    "Organization granting wishes to critically ill children worldwide.",
    "Emergency relief provider during natural disasters globally.",
    "Housing charity building homes for underserved communities worldwide.",
    "Advocacy group promoting life rights from conception to natural death globally.",
    "Healthcare provider focused on comprehensive medical care globally.",
    "Group promoting holistic development through sports worldwide.",
    "Resort offering vacations to families with critically ill children globally.",
    "Pediatric health organization ensuring children's well-being globally.",
    "Christian organization fostering faith development among athletes worldwide."
]

# Load a pre-trained SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode both foundation and charity mission summaries
charity_embeddings = model.encode(charity_missions)

'''
CREATE TABLE nonprofits (
    ein BIGINT PRIMARY KEY,
    is_foundation BOOLEAN DEFAULT FALSE,
    revenue BIGINT,
    name TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    officer_name TEXT,
    officer_title TEXT,
    officer_phone TEXT,
    cy_total_revenue_amount BIGINT,
    cy_contributions_grants_amount BIGINT,
    cy_revenues_less_expenses_amount BIGINT,
    all_other_contributions_amount BIGINT,
    total_contributions_amount BIGINT,
    total_program_service_expenses_amount BIGINT,
    donated_services_and_use_fclts_amount BIGINT,
    gross_receipts_amount BIGINT,
    cy_program_service_revenue_amount BIGINT,
    mission TEXT,
    mission_vector VECTOR(384)  -- Adjust the dimension as needed based on your embeddings
);
CREATE INDEX ON nonprofits USING hnsw (mission_vector vector_l2_ops);
'''

# Connect to PostgreSQL
conn = psycopg2.connect("dbname=day1 user=pivie password=postgres")
cur = conn.cursor()

cnt = 0
cnt1 = 0
last = datetime.now()
# Open the file and read its contents
with open(file_path, mode='r', newline='', encoding='utf-8') as file:
    # Create a CSV reader object with tab delimiter
    reader = csv.DictReader(file, delimiter='\t')

    # Iterate over each row in the TSV file
    for row in reader:
        mission = row['Summary']  # Adjust based on your actual column name

        if mission and len(mission) > 0:
            ein = row['ein']
            is_foundation = row['is_foundation']
            revenue = row['revenue']
            name = row['name']
            city = row['city']
            state = row['state']
            zip_code = row['zip']
            phone = row['phone']
            officer_name = row['officer_name']
            officer_title = row['officer_title']
            officer_phone = row['officer_phone']
            cy_total_revenue_amount = row['CYTotalRevenueAmt']
            cy_contributions_grants_amount = row['CYContributionsGrantsAmt']
            cy_revenues_less_expenses_amount = row['CYRevenuesLessExpensesAmt']
            all_other_contributions_amount = row['AllOtherContributionsAmt']
            total_contributions_amount = row['TotalContributionsAmt']
            total_program_service_expenses_amount = row['TotalProgramServiceExpensesAmt']
            donated_services_and_use_fclts_amount = row['DonatedServicesAndUseFcltsAmt']
            gross_receipts_amount = row['GrossReceiptsAmt']
            cy_program_service_revenue_amount = row['CYProgramServiceRevenueAmt']

            embedding = model.encode(mission).tolist()

            cur.execute(
                """
                INSERT INTO nonprofits (
                    ein, is_foundation, revenue, name, city, state, zip, phone, 
                    officer_name, officer_title, officer_phone, 
                    cy_total_revenue_amount, cy_contributions_grants_amount, 
                    cy_revenues_less_expenses_amount, all_other_contributions_amount, 
                    total_contributions_amount, total_program_service_expenses_amount, 
                    donated_services_and_use_fclts_amount, gross_receipts_amount, 
                    cy_program_service_revenue_amount, 
                    mission, mission_vector
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s
                ) ON CONFLICT (ein) DO UPDATE SET 
                    is_foundation=EXCLUDED.is_foundation, 
                    revenue=EXCLUDED.revenue, 
                    name=EXCLUDED.name, 
                    city=EXCLUDED.city, 
                    state=EXCLUDED.state, 
                    zip=EXCLUDED.zip, 
                    phone=EXCLUDED.phone, 
                    officer_name=EXCLUDED.officer_name, 
                    officer_title=EXCLUDED.officer_title, 
                    officer_phone=EXCLUDED.officer_phone, 
                    cy_total_revenue_amount=EXCLUDED.cy_total_revenue_amount, 
                    cy_contributions_grants_amount=EXCLUDED.cy_contributions_grants_amount, 
                    cy_revenues_less_expenses_amount=EXCLUDED.cy_revenues_less_expenses_amount, 
                    all_other_contributions_amount=EXCLUDED.all_other_contributions_amount, 
                    total_contributions_amount=EXCLUDED.total_contributions_amount, 
                    total_program_service_expenses_amount=EXCLUDED.total_program_service_expenses_amount, 
                    donated_services_and_use_fclts_amount=EXCLUDED.donated_services_and_use_fclts_amount, 
                    gross_receipts_amount=EXCLUDED.gross_receipts_amount, 
                    cy_program_service_revenue_amount=EXCLUDED.cy_program_service_revenue_amount, 
                    mission=EXCLUDED.mission, 
                    mission_vector=EXCLUDED.mission_vector;
                """,
                (
                    ein, is_foundation, revenue, name, city, state, zip_code, phone, officer_name, officer_title, officer_phone,
                    cy_total_revenue_amount, cy_contributions_grants_amount, cy_revenues_less_expenses_amount, all_other_contributions_amount, total_contributions_amount,
                    total_program_service_expenses_amount, donated_services_and_use_fclts_amount, gross_receipts_amount, cy_program_service_revenue_amount,
                    mission, list(embedding)
                )
            )
            
            cnt += 1

        if cnt > 1000:
            cnt=0
            conn.commit()
            cnt1 += 1
            print(f"Batch {cnt1} committed at {datetime.now()}. Diff: {datetime.now() - last} for 1000")


charity_embeddings=[embedding.tolist() for embedding in charity_embeddings]
# Calculate similarity scores between each charity mission and foundation missions
for i, charity_embedding in enumerate(charity_embeddings):
    cur=conn.cursor()

    cur.execute("SELECT ein, mission FROM nonprofits ORDER BY mission_vector <-> %s::vector LIMIT 3", (list(charity_embedding),))
    results=cur.fetchall()

    print(f"Charity: {charity_missions[i]} - Top Matches:")
    # Print results
    for result in results:
        print(f"EIN: {result[0]}, Text: {result[1]}")

    print(' ')

conn.commit()
cur.close()
conn.close()
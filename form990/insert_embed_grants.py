#!/usr/bin/env python3

from datetime import datetime
from sentence_transformers import SentenceTransformer, util
import numpy as np
import psycopg2
import csv

file_path = 'grants.tsv'

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
# foundation_embeddings = model.encode(foundation_missions)
charity_embeddings = model.encode(charity_missions)

'''
CREATE TABLE grants2 (
    source VARCHAR(50),
    year INT,
    donor_ein VARCHAR(20),
    mission TEXT,
    recipient_ein VARCHAR(20),
    recipient_name VARCHAR(100),
    recipient_city VARCHAR(50),
    recipient_state VARCHAR(50),
    recipient_zip VARCHAR(10),
    granted_amount BIGINT,
    granted_purpose TEXT,
    purpose_vectors VECTOR(384)
);

CREATE INDEX idx_recipient_ein ON grants2 (recipient_ein, donor_ein);

CREATE INDEX ON grants2 USING hnsw (purpose_vectors vector_l2_ops);
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
        source = row['source']
        year = row['year']
        mission = row['mission']
        donor_ein = row['donor_ein']
        recipient_ein = row['recipient_ein']
        recipient_name = row['recipient_name']
        recipient_city = row['recipient_city']
        recipient_state = row['recipient_state']
        recipient_zip = row['recipient_zip']
        granted_purpose = row['granted_purpose']
        granted_amount = -1
        if row['granted_amount'] != 'None' and int(row['granted_amount']) > 0:
            granted_amount = int(row['granted_amount'])

        # purpose_vectors VECTOR(384) USING VARBINARY
        embedding = model.encode(granted_purpose).tolist()

        cur.execute("INSERT INTO grants2 (source, year, mission, donor_ein, recipient_ein, recipient_name, recipient_city, recipient_state, recipient_zip, granted_amount, granted_purpose, purpose_vectors) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (source, year, mission, donor_ein, recipient_ein, recipient_name, recipient_city, recipient_state, recipient_zip, granted_amount, granted_purpose, list(embedding)))
        cnt += 1

        if cnt > 1000:
            cnt = 0
            conn.commit()
            # cur.close()
            # cur = conn.cursor()
            cnt1 += 1
            print(f"Batch {cnt1} committed at {datetime.now()}. Diff: {datetime.now() - last} for 1000")

charity_embeddings = [embedding.tolist() for embedding in charity_embeddings]
# Calculate similarity scores between each charity mission and foundation missions
for i, charity_embedding in enumerate(charity_embeddings):

    cur = conn.cursor()

    cur.execute("SELECT donor_ein, recipient_ein, granted_purpose, granted_amount, recipient_name, recipient_city, recipient_state, recipient_zip FROM grants2 ORDER BY purpose_vectors <-> %s::vector LIMIT 3", (list(charity_embedding),))
    results = cur.fetchall()

    print(f"Charity: {charity_missions[i]} - Top Matches:")
    # Print results
    for result in results:
        # print(result)
        if result[1]:
            print(f"Donor EIN: {result[0]}, Recipient EIN: {result[1]}, Purpose: {result[2]}, Amount: {result[3]}")
        else:
            print(f"Donor EIN: {result[0]}, Recipient EIN: None, Purpose: {result[2]}, Amount: {result[3]}")
    print(' ')

conn.commit()
cur.close()
conn.close()

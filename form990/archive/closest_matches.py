#!/usr/bin/env python3

import json
import pandas as pd
from transformers import BertTokenizer, BertModel
import hashlib
import torch
import mysql
import numpy as np
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

import mysql.connector
from mysql.connector import Error

def fetch_rows_by_ids(table_name, key, ids):
    try:
        # Establish the database connection
        mysqldb = mysql.connector.connect(
          host='localhost',
          database='day1ai',
          user='root',
          password='@N~]]mUB#>uA|zqVSmV0'
        )
        print(mysqldb.is_connected())
        if mysqldb.is_connected():
            cursor = mysqldb.cursor(dictionary=True)
            
            # Create a string of placeholders for the IDs
            format_strings = ','.join(['%s'] * len(ids))
            
            # Construct the SQL query
            query = f"SELECT * FROM {table_name} WHERE {key} IN ({format_strings})"
            print(query, tuple(ids))
            
            # Execute the query
            cursor.execute(query, tuple(ids))
            
            # Fetch all the matching rows
            rows = cursor.fetchall()
            
            return rows
        else:
           print("Not connected")

    except Error as e:
        print(f"Error: {e}")
        return None


print('Connect to Milvus (vector database)...')
connections.connect("default", host="localhost", port="19530")

# Check if the collection exists
collection_name = "grants"
if not utility.has_collection(collection_name):
  # Define the schema for the collection
  fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="foundation_ein", dtype=DataType.INT64),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768)
  ]
  schema = CollectionSchema(fields, "Grants collection")

  print('Create the collection...')
  collection = Collection(collection_name, schema)
else:
  collection = Collection(collection_name)

# Load the collection
print('Load the collection...')
collection.load()


# Load pre-trained BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def text_to_vector(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=128)
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).detach().numpy()


# Define search parameters
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

def find_closest_matches(mission, limit=200):
    mission_vector = text_to_vector(mission).flatten()
    search_result = collection.search(
      data=[mission_vector],
      anns_field="vector",
      param=search_params,
      limit=limit,
      expr=None,
      output_fields=["id", "foundation_ein"]
    )
    return search_result

# Perform the search
print('Perform the search...')
results = {}
foundation_eins = []
grant_ids = []
search_result = find_closest_matches("Opera", limit=100)
for hits in search_result:
    for hit in hits:
      foundation_ein = hit.entity.get("foundation_ein")
      grant_id = hit.entity.get("id")
      distance = hit.distance
      grant_ids.append(grant_id)
      if foundation_ein not in results:
        results[foundation_ein] = []
        foundation_eins.append(foundation_ein)

      results[foundation_ein].append((distance, grant_id))

rows = fetch_rows_by_ids('organizations', 'ein', foundation_eins)
nonprofits_info = {item['ein']: item for item in rows if 'ein' in item}

rows = fetch_rows_by_ids('grants', 'id', grant_ids)
grants_info = {item['id']: item for item in rows if 'id' in item}
# print(json.dumps(grant_info, indent=2))


for foundation_ein in foundation_eins:
  if foundation_ein in nonprofits_info:
    nonprofit_info = nonprofits_info[foundation_ein]
    if nonprofit_info:
      print(f"DONOR\t{foundation_ein}\t{nonprofit_info['name']}\t{nonprofit_info['city']}\t{nonprofit_info['state']}\t{nonprofit_info['zip']}\t{nonprofit_info['revenue']}\t{nonprofit_info['description']}")
    else:
      print(f"DONOR\t{foundation_ein}")
  else:
    print(f"DONOR\t{foundation_ein}")
  for distance, grant_id in results[foundation_ein]:
    grant_info = grants_info[grant_id]
    data = json.loads(grant_info['recipient_data'])
    print(f"RECIPIENT\t{distance}\t{grant_info['recipient_ein']}\t{data['name']}\t{data['city']}\t{data['state']}\t{data['zip']}\t{grant_info['granted_amount']}\t{grant_info['granted_purpose']}")
  print("")
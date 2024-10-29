#!/usr/bin/env python3

import pandas as pd
from transformers import BertTokenizer, BertModel
import hashlib
import torch
import numpy as np
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

# Load the data
grants = pd.read_csv('grants.tsv', sep='\t', header=None, usecols=[0, 1, 2, 4, 7], names=['foundation_ein', 'foundation_name', 'recipient_name', 'recipient_state', 'grant_purpose'])
nonprofits = pd.read_csv('nonprofits.input.tsv', sep='\t', header=None, usecols=[0, 1, 3, 6], names=['nonprofit_ein', 'nonprofit_name', 'nonprofit_state', 'mission'])
print('Data loaded...')
grant_index = {}

# Ensure all entries in 'mission' and 'grant_purpose' are strings and handle missing values
nonprofits['mission'] = nonprofits['mission'].fillna('').astype(str)
grants['grant_purpose'] = grants['grant_purpose'].fillna('').astype(str)

# Load pre-trained BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def text_to_vector(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=128)
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).detach().numpy()

print('Connect to Milvus...')
connections.connect("default", host="localhost", port="19530")

# Check if the collection exists
collection_name = "grant_purposes"
if not utility.has_collection(collection_name):
    # Define the schema for the collection
    fields = [
        FieldSchema(name="key", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768)
    ]
    schema = CollectionSchema(fields, "Grant purposes collection")

    print('Create the collection...')
    collection = Collection(collection_name, schema)
else:
    collection = Collection(collection_name)

# Create an index for the collection if it does not exist
if not collection.has_index():
    print('Create an index...')
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="vector", index_params=index_params)

# Load the collection
print('Load the collection...')
collection.load()

# Function to convert the grant description into a key
def hash_dict_to_int64(input_dict):
    sorted_keys = sorted(input_dict.keys())
    ordered_values = [input_dict[key] for key in sorted_keys]
    input_string = ''.join(map(str, ordered_values))
    sha256_hash = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
    hash_int = int(sha256_hash, 16)
    int64_max = 2**63 - 1
    int64_min = -2**63
    int64_hash = (hash_int % (int64_max - int64_min + 1)) + int64_min
    return int64_hash

# Function to check if an embedding already exists
def embedding_exists(key):
    expr = f'key == {key}'
    results = collection.query(expr, output_fields=["key"])
    return len(results) > 0

print('Vectorize the missions and grant purposes...')
# nonprofits['mission_vector'] = nonprofits['mission'].apply(lambda x: text_to_vector(x).flatten())
nonprofits['mission_vector'] = nonprofits.apply(lambda row: text_to_vector(f"{row['mission']}; State: {row['nonprofit_state']}").flatten(), axis=1)

# Vectorize grant purposes only if the embedding does not already exist
count = 0
grant_vectors = []
lookup_grant = {}
it = grants.iterrows()
print('Iterating')
for index, row in it:
    key = hash_dict_to_int64(row)
    lookup_grant[key] = row
    if not embedding_exists(key):
        vector = text_to_vector(f"{row['recipient_name']}: {row['grant_purpose']}; State: {row['recipient_state']}").flatten()
        grant_vectors.append((key, vector))
        count += 1
    if len(grant_vectors) > 1000:
        print(f'Inserting the grant purpose vectors up to {count}...')
        keys, vectors = zip(*grant_vectors)
        collection.insert([list(keys), np.vstack(vectors)])
        grant_vectors = []
if len(grant_vectors)>0:
    print(f'Inserting the last grant purpose vectors up to {count}...')
    keys, vectors = zip(*grant_vectors)
    collection.insert([list(keys), np.vstack(vectors)])


# # Function to insert vectors in batches
# def insert_in_batches(collection, keys, vectors, batch_size=500):
#     for i in range(0, len(keys), batch_size):
#         batch_keys = keys[i:i + batch_size]
#         batch_vectors = vectors[i:i + batch_size]
#         collection.insert([list(batch_keys), np.vstack(batch_vectors)])

# print('Insert the grant purpose vectors...')
# if grant_vectors:
#     keys, vectors = zip(*grant_vectors)
#     insert_in_batches(collection, keys, vectors)

# Define search parameters
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

# Perform the search
print('Perform the search...')
results = []
for mission_vector in nonprofits['mission_vector']:
    search_result = collection.search(
        data=[mission_vector],
        anns_field="vector",
        param=search_params,
        limit=100,
        expr=None
    )
    results.append(search_result)

# Process the results
with open('matches.tsv', 'w') as output_fh:
    output_fh.write(f"NonProfit EIN\tNonProfit Name\tNonProfit Mission\tDistance\tRank\tFoundation EIN\tFoundation Name\tGrant Recipient\tGrant Purpose\n")
    for i, result in enumerate(results):
        nonprofit_ein = nonprofits['nonprofit_ein'][i]
        nonprofit_name = nonprofits['nonprofit_name'][i]
        nonprofit_mission = nonprofits['mission'][i]
        for rank, match in enumerate(result[0]):
            grant_info = lookup_grant[match.id]
            foundation_ein = grant_info['foundation_ein']
            foundation_name = grant_info['foundation_name']
            recipient_name = grant_info['recipient_name']
            grant_purpose = grant_info['grant_purpose']
            output_fh.write(f"{nonprofit_ein}\t{nonprofit_name}\t{nonprofit_mission}\t{match.distance}\t{rank+1}\t{foundation_ein}\t{foundation_name}\t{recipient_name}\t{grant_purpose}\n")

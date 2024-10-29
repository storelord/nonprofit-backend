#!/usr/bin/env python3

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Load the model and tokenizer
model_name = "t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Function to get embeddings using T5
def get_embedding(text):
    text = str(text)  # Ensure the input is a string
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model.encoder(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
    return embeddings[0]

# Read the nonprofit data from the file
nonprofits = pd.read_csv('nonprofits.in.txt', sep='\t', header=None, usecols=[0, 5], names=['nonprofit_ein', 'mission'])

# Read the grants data from the file
grants = pd.read_csv('grants.in.txt', sep='\t', header=None, usecols=[0, 7], names=['foundation_ein', 'grant_purpose'])

# Get embeddings for missions
nonprofits['mission_embedding'] = nonprofits['mission'].apply(get_embedding)

# Get embeddings for grant purposes
grants['grant_purpose_embedding'] = grants['grant_purpose'].apply(get_embedding)

# Function to calculate cosine similarity
def calculate_similarity(embedding1, embedding2):
    return cosine_similarity([embedding1], [embedding2])[0][0]

# Aggregate similarities for each foundation_ein
foundation_embeddings = grants.groupby('foundation_ein')['grant_purpose_embedding'].apply(list).reset_index()

# Find top 100 foundation_eins for each nonprofit_ein
top_foundations = {}

for _, nonprofit in nonprofits.iterrows():
    similarities = []
    for _, foundation in foundation_embeddings.iterrows():
        # Calculate the average similarity for all grant purposes of the foundation
        avg_similarity = np.mean([calculate_similarity(nonprofit['mission_embedding'], purpose_embedding) for purpose_embedding in foundation['grant_purpose_embedding']])
        similarities.append((foundation['foundation_ein'], avg_similarity))
    
    # Sort by similarity and get top 100
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_foundations[nonprofit['nonprofit_ein']] = [ein for ein, _ in similarities[:100]]

# Print the results
for nonprofit_ein, foundation_eins in top_foundations.items():
    print(f"Top 100 foundations for nonprofit {nonprofit_ein}: {foundation_eins}")
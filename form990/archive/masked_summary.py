#!/usr/bin/env python3

#Python script to mask the giver organization's name, location, EIN, and recipient EIN with the following placeholders: [Masked Organization Name], [Masked Location], [Masked EIN], and [Masked Recipient Name], respectively.
#importing the required libraries
import pandas as pd
from openai import OpenAI
from api_key import api_key

#Function Declaration
def openai_call(row_dict):
    # Set your OpenAI API key
    client = OpenAI(api_key=f'{api_key}')

    # Define your prompt
    prompt = f"""
        Provide detailed information about the organization associated with the given EIN. Include the givers organization's name, mission, key areas of focus, and any relevant details about its activities with funding non-profits.
        Giver EIN: {row_dict['giver_ein']}
        """
    user_input = """
        Using the following details, provide information about the giver organization in a concise manner.
        Mask the giver organization's name, location, EIN, and recipient EIN with the following placeholders: [Masked Organization Name], [Masked Location], [Masked EIN], and [Masked Recipient Name], respectively.
        Avoid including any information that could identify the giver organization or the recipient organization.
        """
    # Set your OpenAI API key
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"{prompt}"},
            {
                "role": "user",
                "content": f"{user_input}"
            }
        ]
    )
    return completion.choices[0].message.content

# Main function
def main(): 
    
    # Define the path to your .tsv file
    file_path = 'grants2_sample.tsv'

    # Read the first 5 rows of the .tsv file into a DataFrame
    df = pd.read_csv(file_path, sep='\t', nrows=10)

    # Assign column names based on the fields you provided
    # id	source	year	giver_ein	granted_amount	granted_purpose	recipient_ein	recipient_name	recipient_city	recipient_state	recipient_zip

    df.columns = [
        'id', 'source', 'year', 'giver_ein',
        'granted_amount', 'granted_purpose', 'recipient_ein',
        'recipient_name', 'recipient_city', 'recipient_state', 'recipient_zip'
    ]
    

    # Convert each row to a dictionary and store them in a list
    rows_as_dicts = df.to_dict(orient='records')

    # Example of how to use one of these dictionaries in a prompt
    for row_dict in rows_as_dicts:
        response = openai_call(row_dict)
        print(row_dict)
        print("-----------------------------------")
        print(response)
        exit()
        
if __name__ == '__main__':
    main()

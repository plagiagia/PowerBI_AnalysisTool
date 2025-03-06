import os
from dotenv import load_dotenv
from openai import OpenAI
import sys

def test_openai_connection():
    """
    Test the connection to OpenAI API using the GPT-4o model.
    This script verifies that:
    1. The API key is correctly loaded from the .env file
    2. We can successfully make a call to the OpenAI API
    3. We receive a valid response from the model
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the API key from environment variables
    api_key = os.environ.get('OPENAI_API_KEY')
    model = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please make sure you have set the API key in your .env file.")
        sys.exit(1)
    
    print(f"Testing OpenAI connection with model: {model}")
    
    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Make a simple request to the API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Can you confirm this is the GPT-4o model?"}
            ],
            max_tokens=100
        )
        
        # Print the response
        print("\nAPI Response:")
        print("-" * 50)
        print(f"Model used: {response.model}")
        print(f"Response: {response.choices[0].message.content}")
        print("-" * 50)
        print("\nSuccess! The OpenAI API connection is working correctly.")
        
        return True
    
    except Exception as e:
        print(f"\nError: Failed to connect to OpenAI API: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai_connection()

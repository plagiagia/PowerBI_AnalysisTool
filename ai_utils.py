import os
from dotenv import load_dotenv
from openai import OpenAI
from config import Config

# Load environment variables
load_dotenv()

class AIService:
    """
    Service class for AI-related functionality using OpenAI API.
    This class provides methods to interact with OpenAI's models
    for various AI capabilities in the PowerBI Analysis Tool.
    """
    
    def __init__(self):
        """Initialize the AI service with configuration from environment variables."""
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o')
        self.temperature = float(os.environ.get('AI_TEMPERATURE', 0.7))
        self.max_tokens = int(os.environ.get('AI_MAX_TOKENS', 2000))
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please check your .env file.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_text(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """
        Generate text using the OpenAI API.
        
        Args:
            prompt (str): The user prompt to send to the model
            system_prompt (str, optional): System prompt to guide the model's behavior
            temperature (float, optional): Controls randomness (0.0-1.0)
            max_tokens (int, optional): Maximum tokens in the response
            
        Returns:
            str: The generated text response
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": "You are a helpful assistant for Power BI analysis."})
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Use provided parameters or fall back to defaults
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            return f"Error: {str(e)}"
    
    def analyze_dax(self, dax_expression):
        """
        Analyze a DAX expression and provide insights.
        
        Args:
            dax_expression (str): The DAX expression to analyze
            
        Returns:
            str: Analysis and suggestions for the DAX expression
        """
        system_prompt = """
        You are a Power BI DAX expert. Analyze the given DAX expression and provide:
        1. A clear explanation of what the expression does
        2. Potential performance issues or inefficiencies
        3. Suggestions for improvement
        4. Best practices that could be applied
        Be concise but thorough in your analysis.
        """
        
        return self.generate_text(dax_expression, system_prompt=system_prompt)
    
    def suggest_measures(self, table_schema, business_question):
        """
        Suggest DAX measures based on a business question and table schema.
        
        Args:
            table_schema (str): Description of the table schema
            business_question (str): The business question to address
            
        Returns:
            str: Suggested DAX measures with explanations
        """
        prompt = f"""
        Table Schema:
        {table_schema}
        
        Business Question:
        {business_question}
        
        Please suggest appropriate DAX measures that would help answer this business question.
        """
        
        system_prompt = """
        You are a Power BI DAX expert. Based on the provided table schema and business question:
        1. Suggest relevant DAX measures that would help answer the business question
        2. Provide the complete DAX code for each measure
        3. Explain how each measure helps address the business question
        4. Consider performance and best practices in your suggestions
        """
        
        return self.generate_text(prompt, system_prompt=system_prompt)
    
    def explain_model_relationships(self, model_json):
        """
        Analyze and explain the relationships in a Power BI data model.
        
        Args:
            model_json (str): JSON representation of the data model
            
        Returns:
            str: Analysis of the model relationships
        """
        system_prompt = """
        You are a Power BI data modeling expert. Analyze the provided data model and:
        1. Identify all relationships between tables
        2. Evaluate the relationship types (one-to-many, many-to-many, etc.)
        3. Highlight potential issues or improvements in the relationship structure
        4. Suggest optimizations for better performance and usability
        """
        
        return self.generate_text(model_json, system_prompt=system_prompt)

# Create a singleton instance for use throughout the application
ai_service = AIService()

def get_ai_service():
    """Return the singleton AI service instance."""
    return ai_service

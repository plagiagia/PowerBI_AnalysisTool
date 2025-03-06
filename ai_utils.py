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
    
    def analyze_m_query(self, m_query):
        """
        Analyze an M query and provide insights and explanations.
        
        Args:
            m_query (str): The M query to analyze
            
        Returns:
            dict: Analysis containing explanation and renamed steps
        """
        system_prompt = """
        You are a Power BI M language (Power Query) expert. Analyze the given M query and provide:
        1. A clear explanation of what the query does, step by step
        2. Potential performance issues or inefficiencies
        3. Suggestions for improvement
        4. A version of the same code with steps renamed to clearly reflect what each step accomplishes
        
        You MUST format your response as a valid JSON object with exactly two keys:
        - "explanation": A string containing a detailed explanation of the query with markdown formatting
        - "renamed_code": A string containing the full M query with renamed steps that better describe their purpose
        
        IMPORTANT: Make sure your response is valid JSON. Escape any special characters in the strings properly.
        Do not include any text outside of the JSON structure. The explanation should be a plain string with markdown 
        formatting, not a nested JSON object.
        
        For the "explanation" field, structure your response as follows:
        
        1. Start with a brief overview paragraph: "This M query performs the following steps:"
        
        2. For each step in the query, use a strong (bold) formatting with a colon at the end, followed by the explanation:
           **Source Connection:** Connects to a SQL database...
           **Table Reference:** Retrieves the 'Sales' table...
           
        3. Include a separate paragraph starting with "Potential performance issues or inefficiencies include..."
        
        4. End with a paragraph starting with "Suggestions for improvement include..."
        
        Example of correct format:
        {
          "explanation": "This M query performs the following steps:\\n\\n**Source Connection:** Connects to a SQL database hosted at 'server' and accesses the 'db' database.\\n**Table Reference:** Retrieves the 'Sales' table from the database.\\n**Filter Data:** Filters the rows to include only records from the current year.\\n\\nPotential performance issues or inefficiencies include the use of a direct filter rather than using query folding, which could be optimized.\\n\\nSuggestions for improvement include leveraging query folding by pushing the filter to the database level.",
          "renamed_code": "let\\n    DatabaseConnection = Sql.Database(\\"server\\", \\"db\\"),\\n    SalesTable = DatabaseConnection{\\"Sales\\"},\\n    FilteredToCurrentYear = Table.SelectRows(SalesTable, each [Year] = Date.Year(DateTime.LocalNow()))\\nin\\n    FilteredToCurrentYear"
        }
        
        Be thorough in your analysis but ensure the renamed code is valid M syntax.
        """
        
        response = self.generate_text(m_query, system_prompt=system_prompt)
        
        # Handle case where response might be None
        if not response:
            return {
                "explanation": "Failed to generate analysis.",
                "renamed_code": m_query
            }
        
        try:
            # Try to parse the response as JSON
            import json
            
            # First, try to parse the response directly
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                # Sometimes the model might add extra text before or after the JSON
                import re
                json_match = re.search(r'({[\s\S]*})', response)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                        return result
                    except json.JSONDecodeError:
                        pass
                
                # If all parsing attempts fail, return a formatted response
                return {
                    "explanation": "The AI generated a non-JSON response. Here's the raw analysis:\n\n" + str(response),
                    "renamed_code": m_query  # Return original code if parsing fails
                }
        except Exception as e:
            # Catch any other exceptions
            print(f"Error processing AI response: {str(e)}")
            return {
                "explanation": f"Error processing AI response: {str(e)}\n\nRaw response:\n\n{str(response)}",
                "renamed_code": m_query  # Return original code if processing fails
            }

# Create a singleton instance for use throughout the application
ai_service = AIService()

def get_ai_service():
    """Return the singleton AI service instance."""
    return ai_service

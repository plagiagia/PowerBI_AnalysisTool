from ai_utils import get_ai_service

def test_ai_service():
    """
    Test the AIService functionality.
    This script verifies that:
    1. The AIService can be initialized correctly
    2. We can generate text using the OpenAI API
    3. We can use the specialized methods for Power BI analysis
    """
    print("Testing AI Service...")
    
    try:
        # Get the AI service instance
        ai_service = get_ai_service()
        
        # Test basic text generation
        print("\n1. Testing basic text generation:")
        prompt = "What are the key benefits of using Power BI for data analysis?"
        response = ai_service.generate_text(prompt, max_tokens=150)
        print(f"Response: {response}")
        
        # Test DAX analysis
        print("\n2. Testing DAX analysis:")
        dax_expression = """
        Total Sales = 
        CALCULATE(
            SUM(Sales[SalesAmount]),
            ALL(Sales[Date])
        )
        """
        response = ai_service.analyze_dax(dax_expression)
        print(f"Response: {response}")
        
        # Test measure suggestion
        print("\n3. Testing measure suggestion:")
        table_schema = """
        Sales Table:
        - Date (datetime)
        - ProductID (integer)
        - CustomerID (integer)
        - SalesAmount (decimal)
        - Quantity (integer)
        
        Product Table:
        - ProductID (integer)
        - ProductName (string)
        - Category (string)
        - UnitPrice (decimal)
        """
        business_question = "What is the year-over-year growth in sales by product category?"
        response = ai_service.suggest_measures(table_schema, business_question)
        print(f"Response: {response}")
        
        print("\nAll tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nError testing AI service: {str(e)}")
        return False

if __name__ == "__main__":
    test_ai_service()

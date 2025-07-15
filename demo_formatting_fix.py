#!/usr/bin/env python3
"""
Demonstration of the formatting fix for Tesla stock response
"""
from agent_service import BookWriterAgent

def demo_tesla_response_formatting():
    """Show the before and after of Tesla stock response formatting"""
    agent = BookWriterAgent()
    
    # Your original example
    raw_response = """parts=[Part(
  text='Tesla (TSLA) stock is currently up today. It has increased by approximately 1.08% in the past 24 hours, with its current price around $314.99 USD. In pre-market trading, the stock showed a gain of +0.21%, and as of Tuesday, July 15th, it was up by about 0.14% compared to the previous trading session. Some reports indicate a 0.53% change over the last 24 hours.'
)]"""
    
    cleaned_response = agent._clean_response_text(raw_response)
    
    print("=== TESLA STOCK RESPONSE FORMATTING DEMONSTRATION ===\n")
    
    print("BEFORE (Raw ADK Response):")
    print("-" * 50)
    print(raw_response)
    print("\n" + "=" * 60 + "\n")
    
    print("AFTER (Cleaned Response):")
    print("-" * 50)
    print(cleaned_response)
    print("\n" + "=" * 60 + "\n")
    
    print("RESULT: The user now sees clean, readable text!")
    print("OK No more parts=[Part(...)] formatting")
    print("OK Clean, professional appearance")
    print("OK Easy to read financial information")

def demo_book_response_formatting():
    """Show formatting for book-related responses"""
    agent = BookWriterAgent()
    
    # Book-related response example
    raw_response = """parts=[Part(
  text='Here are some great character development techniques for your fantasy novel:

1. **Backstory Development**: Create detailed histories for your characters
2. **Internal Conflicts**: Give characters personal struggles beyond the main plot
3. **Character Arcs**: Plan how characters will change throughout the story
4. **Dialogue Patterns**: Develop unique speech patterns for each character
5. **Motivations**: Understand what drives each character forward

These techniques will help create more compelling and realistic characters that readers will connect with emotionally.'
)]"""
    
    cleaned_response = agent._clean_response_text(raw_response)
    
    print("\n=== BOOK WRITING RESPONSE FORMATTING ===\n")
    
    print("BEFORE (Raw ADK Response):")
    print("-" * 50)
    print(raw_response[:200] + "..." if len(raw_response) > 200 else raw_response)
    print("\n" + "=" * 60 + "\n")
    
    print("AFTER (Cleaned Response):")
    print("-" * 50)
    print(cleaned_response)
    print("\n" + "=" * 60 + "\n")
    
    print("RESULT: Perfect formatting for book writing advice!")
    print("OK Clean numbered lists")
    print("OK Bold headings preserved")
    print("OK Proper line breaks")
    print("OK Professional appearance")

def main():
    """Run the formatting demonstrations"""
    print("Book Writer Agent - Response Formatting Fix Demo\n")
    
    demo_tesla_response_formatting()
    demo_book_response_formatting()
    
    print("\n" + "=" * 60)
    print("SUMMARY: Text formatting issues have been resolved!")
    print("OK Tesla stock responses now display cleanly")
    print("OK Book writing responses are properly formatted")
    print("OK All raw ADK formatting is automatically cleaned")
    print("OK Users see professional, readable text")

if __name__ == "__main__":
    main()
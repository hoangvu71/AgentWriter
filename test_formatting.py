#!/usr/bin/env python3
"""
Test script for text formatting functionality
"""
import asyncio
from agent_service import BookWriterAgent

def test_text_cleaning():
    """Test the text cleaning functionality"""
    agent = BookWriterAgent()
    
    # Test cases for text cleaning
    test_cases = [
        {
            "input": 'parts=[Part( text="""Based on the search results, here are some of the top romance books on Amazon right now: 1. **These Summer Storms** by Sarah MacLean. 2. **Rose in Chains** by Julie Soto.""" )] role=\'model\'',
            "expected": "Based on the search results, here are some of the top romance books on Amazon right now: 1. **These Summer Storms** by Sarah MacLean. 2. **Rose in Chains** by Julie Soto."
        },
        {
            "input": "Content(parts=[Part(text=\"Hello world\")], role='model')",
            "expected": "Hello world"
        },
        {
            "input": "Normal text without formatting",
            "expected": "Normal text without formatting"
        },
        {
            "input": "Text with\n\n\n\nmultiple newlines",
            "expected": "Text with\n\nmultiple newlines"
        },
        {
            "input": "parts=[Part(\n  text='Tesla (TSLA) stock is currently up today. It has increased by approximately 1.08% in the past 24 hours, with its current price around $314.99 USD. In pre-market trading, the stock showed a gain of +0.21%, and as of Tuesday, July 15th, it was up by about 0.14% compared to the previous trading session. Some reports indicate a 0.53% change over the last 24 hours.'\n)]",
            "expected": "Tesla (TSLA) stock is currently up today. It has increased by approximately 1.08% in the past 24 hours, with its current price around $314.99 USD. In pre-market trading, the stock showed a gain of +0.21%, and as of Tuesday, July 15th, it was up by about 0.14% compared to the previous trading session. Some reports indicate a 0.53% change over the last 24 hours."
        }
    ]
    
    print("Testing text cleaning functionality...")
    
    for i, test_case in enumerate(test_cases):
        result = agent._clean_response_text(test_case["input"])
        print(f"\nTest case {i+1}:")
        print(f"Input: {test_case['input'][:100]}...")
        print(f"Expected: {test_case['expected']}")
        print(f"Result: '{result}'")
        print(f"Pass: {result == test_case['expected']}")
        if result != test_case['expected']:
            print(f"Length difference: expected {len(test_case['expected'])}, got {len(result)}")
            print(f"Result repr: {repr(result)}")

def test_example_response():
    """Test formatting of the example response"""
    agent = BookWriterAgent()
    
    example_response = '''parts=[Part( text="""Based on the search results, here are some of the top romance books on Amazon right now: 

1. **These Summer Storms** by Sarah MacLean. 
2. **Rose in Chains** by Julie Soto. 
3. **A Witch's Guide to Magical Innkeeping** by Sangu Mandanna. 
4. **The View From Lake Como** by Adriana Trigiani. 
5. **Love Is a War Song** by Danica Nava. 
6. **The Summer I Turned Pretty** by Jenny Han. 
7. **Happy Place** by Emily Henry. 
8. **Funny Story** by Emily Henry. 
9. **The Love Of My Afterlife** by Kirsty Greenwood. 
10. **Better Than The Movies** by Lynn Painter. 

Please note that Amazon's best-seller lists can fluctuate frequently, so this is just a snapshot of what's currently popular. """ )] role='model' '''
    
    print("\nTesting example response formatting...")
    result = agent._clean_response_text(example_response)
    print("Cleaned result:")
    print(result)

if __name__ == "__main__":
    test_text_cleaning()
    test_example_response()
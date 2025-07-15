#!/usr/bin/env python3
"""
Demonstration script for the Book Writer Agent
"""
import asyncio
from agent_service import BookWriterAgent

async def demo_text_formatting():
    """Demonstrate text formatting capabilities"""
    print("=== Book Writer Agent Text Formatting Demo ===\n")
    
    agent = BookWriterAgent()
    
    # Example of raw ADK response
    raw_response = '''parts=[Part( text="""Based on the search results, here are some of the top romance books on Amazon right now: 

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
    
    print("Raw ADK Response:")
    print(raw_response[:200] + "..." if len(raw_response) > 200 else raw_response)
    print("\n" + "="*50 + "\n")
    
    # Clean the response
    cleaned = agent._clean_response_text(raw_response)
    
    print("Cleaned & Formatted Response:")
    print(cleaned)
    print("\n" + "="*50 + "\n")
    
    # Show what the user would see
    print("What the user sees in the web interface:")
    print("(With proper HTML formatting applied)")
    print("\nTop 10 Romance Books on Amazon:")
    
    # Simulate what the frontend would display
    lines = cleaned.split('\n')
    for line in lines:
        if line.strip():
            # Simulate bold formatting
            if '**' in line:
                line = line.replace('**', '')
                print(f"• {line}")
            else:
                print(f"  {line}")
    
    print("\nDemo completed successfully!")

def demo_features():
    """Demonstrate the key features of the Book Writer Agent"""
    print("\n=== Key Features Demo ===\n")
    
    features = [
        "• **Web Search Integration**: Real-time Google Search for research",
        "• **Conversation Memory**: Remembers context across the entire chat session",
        "• **Task Planning**: Breaks down complex writing projects into steps",
        "• **Writing Assistance**: Plot development, character creation, editing help",
        "• **Real-time Streaming**: WebSocket-based chat with live response streaming",
        "• **Session Management**: Multiple users, isolated conversations",
        "• **Clean Formatting**: Automatically formats responses for readability"
    ]
    
    for feature in features:
        print(feature)
    
    print("\nExample Use Cases:")
    use_cases = [
        "\"Help me develop a fantasy character with magical abilities\"",
        "\"Search for information about Victorian era architecture for my novel\"",
        "\"Break down the steps to write a compelling mystery plot\"",
        "\"What are the current bestselling romance novels for market research?\""
    ]
    
    for case in use_cases:
        print(f"  - {case}")

def demo_architecture():
    """Show the technical architecture"""
    print("\n=== Technical Architecture ===\n")
    
    print("System Components:")
    components = [
        "Google Agent Development Kit (ADK) - Core AI agent framework",
        "FastAPI - Web server with WebSocket support",
        "Gemini 2.0 Flash - Large language model",
        "Google Search API - Real-time web search",
        "InMemoryRunner - Session and conversation management",
        "HTML/CSS/JavaScript - Clean, responsive web interface"
    ]
    
    for component in components:
        print(f"  • {component}")
    
    print("\nData Flow:")
    flow = [
        "User sends message via WebSocket",
        "FastAPI receives and routes to agent service",
        "ADK agent processes with Gemini model",
        "Agent can call Google Search tool if needed",
        "Response streams back through WebSocket",
        "Frontend formats and displays cleaned text"
    ]
    
    for i, step in enumerate(flow, 1):
        print(f"  {i}. {step}")

def main():
    """Run the complete demonstration"""
    print("Book Writer Agent - Complete Demonstration\n")
    
    # Run text formatting demo
    asyncio.run(demo_text_formatting())
    
    # Show features
    demo_features()
    
    # Show architecture
    demo_architecture()
    
    print("\n** Ready to Use! **")
    print("To start the application:")
    print("1. Ensure Google Cloud credentials are configured")
    print("2. Run: python main.py")
    print("3. Open: http://localhost:8000")
    print("4. Start chatting with your AI book writing assistant!")

if __name__ == "__main__":
    main()
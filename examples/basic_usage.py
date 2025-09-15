#!/usr/bin/env python3
"""
Basic usage example for Where Was Eye.

This example shows how to use the timeline database and AI agent
to query location history.
"""

import os
from dotenv import load_dotenv
from where_was_eye import MyTimelineDB, create_agent

# Load environment variables
load_dotenv()

def main():
    # Get timeline database path from environment
    db_path = os.getenv("LOCATION_HISTORY_PATH")
    if not db_path:
        print("Error: LOCATION_HISTORY_PATH environment variable not set")
        print("Please set it to the path of your Google Timeline JSON file")
        return
    
    print("🔍 Where Was Eye - Basic Usage Example")
    print("=" * 50)
    
    # Example 1: Direct database query
    print("\n1. Direct Timeline Database Query")
    print("-" * 30)
    
    try:
        # Initialize timeline database
        db = MyTimelineDB(db_path)
        print("✅ Timeline database loaded successfully")
        
        # Query a specific time
        location = db.get_location_at_time(2024, 8, 20, 15, 30)
        print(f"📍 Location on Aug 20, 2024 at 3:30 PM: {location}")
        
    except Exception as e:
        print(f"❌ Error loading timeline database: {e}")
        return
    
    # Example 2: AI Agent with OpenAI
    print("\n2. AI Agent with OpenAI")
    print("-" * 30)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            agent = create_agent(
                provider="openai",
                model="gpt-4.1",
                timeline_db_path=db_path
            )
            
            questions = [
                "Where was I on August 20, 2024 at 3:30 PM?",
                "What was my location last Tuesday around 2 PM?",
                "Where was I on Christmas day 2023?"
            ]
            
            for i, question in enumerate(questions, 1):
                print(f"\nQ{i}: {question}")
                try:
                    response = agent.run(question)
                    print(f"A{i}: {response}")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
        except Exception as e:
            print(f"❌ OpenAI agent error: {e}")
    else:
        print("ℹ️  OpenAI API key not found. Skipping OpenAI examples.")
        print("Set OPENAI_API_KEY environment variable to enable OpenAI integration")
    
    # Example 3: AI Agent with Ollama
    print("\n3. AI Agent with Ollama")
    print("-" * 30)
    
    try:
        agent = create_agent(
            provider="ollama",
            model="llama3.1",
            timeline_db_path=db_path
        )
        
        question = "Where was I on August 20, 2024 at 3:30 PM?"
        print(f"Q: {question}")
        
        try:
            response = agent.run(question)
            print(f"A: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("ℹ️  Make sure Ollama is running: ollama serve")
            
    except Exception as e:
        print(f"❌ Ollama agent error: {e}")
        print("ℹ️  Install Ollama: pip install ollama")
    
    print("\n" + "=" * 50)
    print("🎉 Example completed!")

if __name__ == "__main__":
    main()
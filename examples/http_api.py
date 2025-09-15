#!/usr/bin/env python3
"""
HTTP API usage example for Where Was Eye.

This example shows how to use the HTTP API server and make requests to it.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🌐 Where Was Eye - HTTP API Example")
    print("=" * 50)
    
    # Server configuration
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = os.getenv("SERVER_PORT", "8000")
    base_url = f"http://{host}:{port}"
    
    print(f"Server URL: {base_url}")
    print("Make sure the server is running with: python -m where_was_eye.server")
    print()
    
    # Example API requests
    endpoints = [
        ("GET", "/", "API information"),
        ("GET", "/health", "Health check"),
        ("POST", "/get_location_at_time", "Get location at specific time")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"{method} {endpoint} - {description}")
    
    print("\n" + "=" * 50)
    
    # Test health endpoint
    print("\n1. Testing Health Endpoint")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check successful")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to server: {e}")
        print("ℹ️  Start the server with: python -m where_was_eye.server")
        return
    
    # Test location query
    print("\n2. Testing Location Query")
    print("-" * 30)
    
    # Example time: August 20, 2024 at 3:30 PM
    payload = {
        "year": 2024,
        "month": 8,
        "day": 20,
        "hour": 15,
        "minute": 30
    }
    
    try:
        response = requests.post(
            f"{base_url}/get_location_at_time",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Location query successful")
            print(f"Request: {json.dumps(payload, indent=2)}")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result["success"] and result["latitude"] is not None:
                print(f"📍 Location found: {result['latitude']}, {result['longitude']}")
            else:
                print("ℹ️  No location found for the specified time")
        else:
            print(f"❌ Location query failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    
    # Example using Python requests with error handling
    print("\n3. Advanced Usage Example")
    print("-" * 30)
    
    def query_location(year, month, day, hour, minute):
        """Helper function to query location with error handling."""
        payload = {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute
        }
        
        try:
            response = requests.post(
                f"{base_url}/get_location_at_time",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    # Query multiple times
    times_to_query = [
        (2024, 8, 20, 12, 0),   # Noon
        (2024, 8, 20, 18, 30),  # Evening
        (2024, 8, 21, 9, 0),    # Next morning
    ]
    
    for year, month, day, hour, minute in times_to_query:
        result = query_location(year, month, day, hour, minute)
        
        time_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        
        if result["success"]:
            if result["latitude"] is not None:
                print(f"📍 {time_str}: {result['latitude']}, {result['longitude']}")
            else:
                print(f"❓ {time_str}: No location data available")
        else:
            print(f"❌ {time_str}: Error - {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    print("🎉 HTTP API example completed!")
    print("\nNext steps:")
    print("1. Use the API in your applications")
    print("2. Integrate with other services")
    print("3. Build custom clients for different platforms")

if __name__ == "__main__":
    main()
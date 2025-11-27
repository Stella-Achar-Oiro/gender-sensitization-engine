#!/usr/bin/env python3
"""
API testing script - tests the FastAPI server
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_single_rewrite():
    """Test single text rewrite"""
    print("🧪 Testing Single Rewrite API")
    
    payload = {
        "id": "test-001",
        "lang": "en",
        "text": "The chairman will discuss this with his secretary"
    }
    
    try:
        response = requests.post(f"{API_BASE}/rewrite", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Original: {result['original_text']}")
            print(f"✅ Rewrite: {result['rewrite']}")
            print(f"✅ Source: {result['source']}")
            print(f"✅ Confidence: {result['confidence']}")
            print(f"✅ Edits: {len(result['edits'])}")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Start with: uvicorn api.main:app --reload")

def test_batch_rewrite():
    """Test batch processing"""
    print("\n🧪 Testing Batch Rewrite API")
    
    batch_payload = [
        {"id": "batch-001", "lang": "en", "text": "The businessman met his client"},
        {"id": "batch-002", "lang": "en", "text": "The nurse checked her patient"},
        {"id": "batch-003", "lang": "sw", "text": "Mwalimu mkuu anafundisha"}
    ]
    
    try:
        response = requests.post(f"{API_BASE}/rewrite/batch", json=batch_payload)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Processed {len(results)} items")
            for result in results:
                print(f"   {result['id']}: {result['source']} -> {len(result['edits'])} edits")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")

def test_api_health():
    """Test API health"""
    print("🧪 Testing API Health")
    
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code == 200:
            print("✅ API server is running")
            print(f"✅ Docs available at: {API_BASE}/docs")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")

if __name__ == "__main__":
    print("🚀 JuaKali API Testing")
    print("=" * 40)
    
    test_api_health()
    test_single_rewrite()
    test_batch_rewrite()
    
    print("\n✨ API Testing Complete!")
    print("\nTo start API server:")
    print("uvicorn api.main:app --reload")
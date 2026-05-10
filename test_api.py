import requests
import json
import sys

# Set stdout encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Test 1: Create a trip
response = requests.post(
    'http://localhost:8000/api/chat',
    json={'message': '我要去海南三亚旅游，5天', 'user_id': 'default'}
)

print("Test 1 - Create Trip:")
if response.status_code == 200:
    data = response.json()
    print(f"Response: {data.get('response', '')}")
    print(f"Intent: {data.get('intent', '')}")
    if data.get('trip'):
        print(f"Trip created: {data['trip']['destination']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

print("\n" + "="*50 + "\n")

# Test 2: Check completeness
response2 = requests.post(
    'http://localhost:8000/api/chat',
    json={'message': '检查一下有没有遗漏', 'user_id': 'default'}
)

print("Test 2 - Check Completeness:")
if response2.status_code == 200:
    data2 = response2.json()
    print(f"Response: {data2.get('response', '')}")
else:
    print(f"Error: {response2.status_code}")
    print(response2.text)

# debug_aws_response.py
import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
calculator = os.getenv('AWS_ROUTE_CALCULATOR', 'LogisticsRouteCalculator')

print(f"🔧 Testing AWS Location Service")
print(f"Region: {region}")
print(f"Calculator: {calculator}")

try:
    # Initialize client
    location_client = boto3.client('location', region_name=region)
    
    # Test 1: List all calculators first
    print("\n📋 Step 1: Listing all calculators...")
    try:
        response = location_client.list_route_calculators(MaxResults=10)
        print(f"✅ List successful. Found {len(response.get('Entries', []))} calculators:")
        for calc in response.get('Entries', []):
            print(f"  - {calc['CalculatorName']}")
    except Exception as e:
        print(f"❌ List failed: {e}")
    
    # Test 2: Try describe_route_calculator
    print(f"\n📋 Step 2: Describing calculator '{calculator}'...")
    try:
        response = location_client.describe_route_calculator(
            CalculatorName=calculator
        )
        
        print(f"✅ Describe successful!")
        print(f"Full response structure:")
        print("-" * 50)
        for key, value in response.items():
            print(f"{key}: {value}")
        print("-" * 50)
        
        # Check what keys are available
        print(f"\nAvailable keys in response:")
        for key in response.keys():
            print(f"  • {key}")
            
    except Exception as e:
        print(f"❌ Describe failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        if hasattr(e, 'response'):
            print(f"Error response: {e.response}")
            
except Exception as e:
    print(f"❌ Overall error: {e}")
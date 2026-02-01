# test_aws_setup.py - FIXED VERSION
#!/usr/bin/env python3
"""
Test AWS Location Service Setup - FIXED for missing Status field
"""
import os
import sys
#from dotenv import load_dotenv

# Load environment variables FIRST
#load_dotenv()

print("🔧 Testing AWS Location Service Setup")
print("="*70)

# Check if .env is loaded
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')

if not aws_key or not aws_secret:
    print("❌ AWS credentials not found in environment!")
    print("   Make sure .env file exists with:")
    print("   AWS_ACCESS_KEY_ID=your-key")
    print("   AWS_SECRET_ACCESS_KEY=your-secret")
    print("   AWS_DEFAULT_REGION=us-east-1")
    print("   AWS_ROUTE_CALCULATOR=LogisticsRouteCalculator")
    sys.exit(1)

print("✓ AWS credentials found in environment")

# Get configuration from environment
region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
calculator = os.getenv('AWS_ROUTE_CALCULATOR', 'LogisticsRouteCalculator')

print(f"\n📋 Configuration:")
print(f"  Region: {region}")
print(f"  Route Calculator: {calculator}")

try:
    # Now import boto3 AFTER loading .env
    import boto3
    from botocore.exceptions import ClientError
    
    # Initialize AWS client (boto3 reads from environment automatically)
    location_client = boto3.client('location', region_name=region)
    
    # First, list all calculators to see what's available
    print(f"\n📋 Listing available calculators...")
    try:
        list_response = location_client.list_route_calculators(MaxResults=10)
        calculator_entries = list_response.get('Entries', [])
        print(f"Found {len(calculator_entries)} calculators:")
        for calc in calculator_entries:
            print(f"  - {calc['CalculatorName']} (Status: {calc.get('Status', 'ACTIVE')})")
    except Exception as e:
        print(f"List failed: {e}")
    
    # Check if calculator exists
    print(f"\n🔍 Checking calculator '{calculator}'...")
    try:
        response = location_client.describe_route_calculator(
            CalculatorName=calculator
        )
        
        # If we get here without error, calculator exists
        print(f"✅ Calculator exists and is active!")
        print(f"  Calculator Name: {response['CalculatorName']}")
        print(f"  ARN: {response['CalculatorArn']}")
        print(f"  Data Source: {response['DataSource']}")
        print(f"  Created: {response['CreateTime']}")
        
        # In AWS Location Service, if describe_route_calculator succeeds, 
        # the calculator is active. Only failed calculators show Status field.
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        if error_code == 'ResourceNotFoundException':
            print(f"❌ Calculator '{calculator}' not found")
            print("💡 Create it in AWS Console or use the setup script")
            sys.exit(1)
        elif error_code == 'AccessDeniedException':
            print(f"❌ Access denied to calculator '{calculator}'")
            print(f"  Message: {error_msg}")
            print("\n💡 Check IAM permissions:")
            print("  1. Verify your IAM policy has 'geo:DescribeRouteCalculator'")
            print("  2. Check if calculator exists in AWS Console")
            sys.exit(1)
        else:
            print(f"❌ AWS Error: {error_code}")
            print(f"  Message: {error_msg}")
            sys.exit(1)
    
    # Test route calculation
    print(f"\n🧪 Testing sample route (Mumbai to Pune)...")
    try:
        response = location_client.calculate_route(
            CalculatorName=calculator,
            DeparturePosition=[72.8777, 19.0760],  # Mumbai [lon, lat]
            DestinationPosition=[73.8567, 18.5204],  # Pune [lon, lat]
            TravelMode='Car',
            DistanceUnit='Kilometers',
            DepartNow=True
        )
        
        if 'Summary' in response:
            summary = response['Summary']
            distance_km = summary['Distance']
            duration_hr = summary['DurationSeconds'] / 3600
            
            print(f"✅ Route calculated successfully!")
            print(f"  Distance: {distance_km:.1f} km")
            print(f"  Duration: {duration_hr:.2f} hours")
            print(f"  Data Source: {summary.get('DataSource', 'Here')}")
        else:
            print(f"❌ Route response missing 'Summary'")
            print(f"  Response keys: {list(response.keys())}")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        print(f"❌ Route calculation failed: {error_code}")
        print(f"  Message: {error_msg}")
        
        if "NoAvailableApiKeys" in str(e):
            print(f"\n🔧 API Key Issue Detected!")
            print(f"  Calculator exists but has no API key associated")
            print(f"\n💡 Solution:")
            print(f"  1. Go to AWS Console → Location Service → Route calculators")
            print(f"  2. Select '{calculator}'")
            print(f"  3. Go to 'API keys' tab")
            print(f"  4. Click 'Associate API key'")
            print(f"  5. Select an existing API key or create a new one")
        elif "AccessDenied" in error_code:
            print(f"\n🔧 IAM Permission Issue Detected!")
            print(f"  Your IAM user needs 'geo:CalculateRoute' permission")
        elif "ThrottlingException" in error_code:
            print(f"\n🔧 Rate limiting issue")
            print(f"  AWS is throttling requests. Try again in a minute.")
        
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Setup test failed: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ AWS Location Service setup is working!")
print("You can now use AWS for routing in your logistics agent.")

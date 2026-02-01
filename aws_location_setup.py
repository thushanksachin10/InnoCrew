#aws_location_setup.py

"""
Complete AWS Location Service Setup with API Key
"""
import boto3
import time
from botocore.exceptions import ClientError

def setup_aws_location_complete():
    """Complete setup: Calculator + API Key + Association"""
    region = "us-east-1"
    client = boto3.client('location', region_name=region)
    
    calculator_name = "LogisticsRouteCalculator"
    api_key_name = "LogisticsAPIKey"
    
    print("🚀 AWS Location Service Complete Setup\n")
    
    # Step 1: Create or get API Key
    print("🔑 Step 1: Setting up API Key...")
    api_key_arn = create_or_get_api_key(client, api_key_name)
    
    if not api_key_arn:
        print("❌ API Key setup failed. Exiting.")
        return False
    
    # Step 2: Create Route Calculator
    print(f"\n🗺️ Step 2: Setting up Route Calculator...")
    calculator_arn = create_or_get_calculator(client, calculator_name, api_key_arn)
    
    if not calculator_arn:
        print("❌ Calculator setup failed.")
        return False
    
    # Step 3: Test the setup
    print(f"\n🧪 Step 3: Testing setup...")
    test_result = test_calculator(client, calculator_name)
    
    if test_result:
        print(f"\n{'='*60}")
        print("✅ SETUP COMPLETE!")
        print(f"✅ API Key: {api_key_name}")
        print(f"✅ Calculator: {calculator_name}")
        print(f"✅ Region: {region}")
        print(f"{'='*60}")
        
        # Save API key value (you'll only see this once!)
        save_api_key_value(client, api_key_name)
        
        return True
    else:
        print("\n❌ Setup completed but testing failed.")
        return False

def create_or_get_api_key(client, api_key_name):
    """Create or retrieve API key"""
    try:
        # Check if API key exists
        print(f"  Checking API key: {api_key_name}")
        response = client.describe_key(KeyName=api_key_name)
        print(f"  ✅ API Key exists (ARN: {response['KeyArn']})")
        return response['KeyArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  Creating new API key: {api_key_name}")
            
            try:
                # Create API key for Location Service
                create_response = client.create_key(
                    KeyName=api_key_name,
                    Restrictions={
                        'AllowActions': [
                            'geo:CalculateRoute',
                            'geo:CalculateRouteMatrix'
                        ],
                        'AllowResources': ['*'],
                        'AllowReferers': ['*']
                    },
                    Description='API key for logistics route calculations',
                    ExpireTime=None  # Never expire (or set a date)
                )
                
                print(f"  ✅ API Key created!")
                print(f"    Key ARN: {create_response['KeyArn']}")
                print(f"    Key created: {create_response['CreateTime']}")
                
                return create_response['KeyArn']
                
            except ClientError as create_error:
                print(f"  ❌ Failed to create API key: {create_error}")
                return None
        else:
            print(f"  ❌ Error: {e}")
            return None

def create_or_get_calculator(client, calculator_name, api_key_arn):
    """Create or retrieve route calculator"""
    try:
        # Check if calculator exists
        print(f"  Checking calculator: {calculator_name}")
        response = client.describe_route_calculator(
            CalculatorName=calculator_name
        )
        
        print(f"  ✅ Calculator exists")
        print(f"    Status: {response['Status']}")
        print(f"    Data Source: {response['DataSource']}")
        
        # If calculator exists but not active, wait
        if response['Status'] != 'ACTIVE':
            print(f"  ⏳ Waiting for calculator to become ACTIVE...")
            return wait_for_active_calculator(client, calculator_name)
        
        return response['CalculatorArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  Creating calculator: {calculator_name}")
            
            try:
                # Create calculator with API key association
                create_response = client.create_route_calculator(
                    CalculatorName=calculator_name,
                    DataSource='Here',
                    Description='For logistics route calculation in India',
                    # No direct API key parameter in create, will associate later
                    Tags={
                        'Purpose': 'Logistics',
                        'Environment': 'Production'
                    }
                )
                
                print(f"  ✅ Calculator created!")
                print(f"    Calculator ARN: {create_response['CalculatorArn']}")
                
                # Associate API key with calculator
                print(f"  🔗 Associating API key with calculator...")
                client.associate_tracker_consumer(
                    ConsumerArn=api_key_arn,
                    TrackerName=calculator_name
                )
                print(f"  ✅ API Key associated!")
                
                # Wait for calculator to become active
                return wait_for_active_calculator(client, calculator_name)
                
            except ClientError as create_error:
                print(f"  ❌ Failed to create calculator: {create_error}")
                
                # Check if error mentions API key
                if "API key" in str(create_error).lower():
                    print("\n💡 Note: In some regions, you might need to:")
                    print("  1. Create calculator first")
                    print("  2. Associate API key separately")
                    print("  3. Or use 'Esri' instead of 'Here' as data source")
                
                return None
        else:
            print(f"  ❌ Error: {e}")
            return None

def wait_for_active_calculator(client, calculator_name, max_wait=120):
    """Wait for calculator to become active"""
    print(f"  ⏳ Waiting for calculator to become ACTIVE (max {max_wait}s)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = client.describe_route_calculator(
                CalculatorName=calculator_name
            )
            status = response['Status']
            
            if status == 'ACTIVE':
                print(f"  ✅ Calculator is now ACTIVE!")
                print(f"    Created: {response.get('CreateTime', 'N/A')}")
                print(f"    Updated: {response.get('UpdateTime', 'N/A')}")
                return response['CalculatorArn']
            elif status == 'FAILED':
                print(f"  ❌ Calculator creation FAILED")
                return None
            else:
                print(f"  Current status: {status} ({(time.time()-start_time):.0f}s)")
                time.sleep(10)
                
        except ClientError as e:
            print(f"  Error checking status: {e}")
            time.sleep(10)
    
    print(f"  ⚠️ Calculator not active after {max_wait} seconds")
    return None

def test_calculator(client, calculator_name):
    """Test the calculator with actual route"""
    try:
        print(f"  Testing Mumbai to Pune route...")
        
        response = client.calculate_route(
            CalculatorName=calculator_name,
            DeparturePosition=[72.8777, 19.0760],  # Mumbai [lon, lat]
            DestinationPosition=[73.8567, 18.5204],  # Pune [lon, lat]
            TravelMode='Car',
            DistanceUnit='Kilometers',
            DepartNow=True
        )
        
        summary = response['Summary']
        print(f"  ✅ Test successful!")
        print(f"    Distance: {summary['Distance']:.1f} km")
        print(f"    Duration: {summary['DurationSeconds']/3600:.2f} hours")
        print(f"    Data Source: {summary.get('DataSource', 'Here')}")
        
        return True
        
    except ClientError as e:
        print(f"  ❌ Test failed: {e.response['Error']['Code']}")
        print(f"    Message: {e.response['Error']['Message']}")
        
        # Provide specific troubleshooting
        if "NoAvailableApiKeys" in str(e):
            print("\n💡 Solution: Associate API key with calculator in AWS Console")
        elif "AccessDenied" in str(e):
            print("\n💡 Solution: Check IAM permissions for geo:CalculateRoute")
        
        return False

def save_api_key_value(client, api_key_name):
    """Retrieve and display API key value (only once!)"""
    try:
        # List API keys to get the value
        keys_response = client.list_keys()
        
        for key in keys_response.get('Entries', []):
            if key['KeyName'] == api_key_name:
                # Get the API key value
                key_response = client.describe_key(KeyName=api_key_name)
                
                # Note: AWS doesn't return the key value after creation
                # You need to save it when first created
                print("\n⚠️ IMPORTANT: API Key Value")
                print("The API key value is only shown ONCE during creation.")
                print("If you didn't save it, you need to:")
                print("1. Go to AWS Console → Location Service → API Keys")
                print("2. Find your key and copy the value")
                print("3. Store it securely")
                
                # Alternative: Create a new key and save the value
                print("\n💡 To get a new key value:")
                print("aws location create-key \\")
                print(f"  --key-name {api_key_name}_new \\")
                print("  --no-expire \\")
                print("  --region us-east-1")
                
                break
                
    except Exception as e:
        print(f"Note: {e}")

def get_api_key_from_console():
    """Instructions to get API key from console"""
    print("\n📋 Manual API Key Setup:")
    print("1. Go to AWS Console → Location Service → API keys")
    print("2. Click 'Create API key'")
    print("3. Name: 'LogisticsAPIKey'")
    print("4. Key restrictions: Select 'Location' service")
    print("5. Actions: Allow 'CalculateRoute' and 'CalculateRouteMatrix'")
    print("6. Resources: 'All resources'")
    print("7. Click 'Create'")
    print("8. COPY THE KEY VALUE (you won't see it again!)")
    print("9. Store it in your config.py as AWS_LOCATION_API_KEY")
    print("\n10. Associate with calculator:")
    print("    - Go to 'Route calculators'")
    print("    - Click on 'LogisticsRouteCalculator'")
    print("    - Go to 'API keys' tab")
    print("    - Click 'Associate API key'")
    print("    - Select 'LogisticsAPIKey'")

def main():
    print("="*60)
    print("AWS LOCATION SERVICE COMPLETE SETUP")
    print("="*60)
    
    # Ask user if they have API key
    print("\nDo you already have an API key for Location Service?")
    print("1. Yes, I have the key value")
    print("2. No, need to create one")
    print("3. Don't know")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # User has API key
        api_key_value = input("Enter your API key value: ").strip()
        print(f"\n✅ Save this in config.py as:")
        print(f"AWS_LOCATION_API_KEY = '{api_key_value}'")
        
        # Continue with calculator setup
        setup_aws_location_complete()
        
    elif choice == "2" or choice == "3":
        # Need to create API key
        print("\n📝 API Key Creation Required")
        print("You need to create an API key in AWS Console first.")
        get_api_key_from_console()
        
        print("\nAfter creating API key, run this script again.")
        api_key_value = input("\nIf you created it, enter the API key value (or press Enter to skip): ").strip()
        
        if api_key_value:
            print(f"\n✅ Save this in config.py as:")
            print(f"AWS_LOCATION_API_KEY = '{api_key_value}'")
            setup_aws_location_complete()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
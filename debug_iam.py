#!/usr/bin/env python3
"""
Debug IAM permissions for AWS Location Service
"""
import boto3
import json
from botocore.exceptions import ClientError

def debug_iam_permissions():
    print("🔍 Debugging IAM Permissions\n")
    
    # Create clients
    sts_client = boto3.client('sts')
    iam_client = boto3.client('iam')
    
    # Get current user/role
    try:
        identity = sts_client.get_caller_identity()
        print(f"👤 Current AWS Identity:")
        print(f"   UserId: {identity['UserId']}")
        print(f"   Account: {identity['Account']}")
        print(f"   Arn: {identity['Arn']}")
        
        user_name = identity['Arn'].split('/')[-1] if 'user/' in identity['Arn'] else None
        print(f"   User Name: {user_name}")
        
        if user_name:
            # Get attached policies
            print(f"\n📋 IAM Policies for user '{user_name}':")
            
            # Get inline policies
            inline_policies = iam_client.list_user_policies(UserName=user_name)
            if inline_policies['PolicyNames']:
                print(f"   Inline Policies: {', '.join(inline_policies['PolicyNames'])}")
                
                # Get each inline policy
                for policy_name in inline_policies['PolicyNames']:
                    policy_doc = iam_client.get_user_policy(
                        UserName=user_name,
                        PolicyName=policy_name
                    )
                    print(f"\n   📄 Policy '{policy_name}':")
                    print(json.dumps(policy_doc['PolicyDocument'], indent=4))
            
            # Get attached managed policies
            attached_policies = iam_client.list_attached_user_policies(UserName=user_name)
            if attached_policies['AttachedPolicies']:
                print(f"\n   Managed Policies:")
                for policy in attached_policies['AttachedPolicies']:
                    print(f"      - {policy['PolicyName']} ({policy['PolicyArn']})")
                    
                    # Try to get policy document
                    try:
                        # For AWS managed policies
                        if 'arn:aws:iam::aws' in policy['PolicyArn']:
                            # Get default version
                            policy_response = iam_client.get_policy(PolicyArn=policy['PolicyArn'])
                            version_response = iam_client.get_policy_version(
                                PolicyArn=policy['PolicyArn'],
                                VersionId=policy_response['Policy']['DefaultVersionId']
                            )
                            print(f"        Document: {json.dumps(version_response['PolicyVersion']['Document'], indent=8)}")
                    except:
                        pass
        
        print("\n" + "="*60)
        
        # Test Location Service permissions
        print("\n🧪 Testing Location Service permissions...")
        location_client = boto3.client('location', region_name='us-east-1')
        
        tests = [
            ("List calculators", lambda: location_client.list_route_calculators(MaxResults=5)),
            ("Describe calculator", lambda: location_client.describe_route_calculator(CalculatorName='LogisticsRouteCalculator')),
            ("Calculate route", lambda: location_client.calculate_route(
                CalculatorName='LogisticsRouteCalculator',
                DeparturePosition=[72.8777, 19.0760],
                DestinationPosition=[73.8567, 18.5204],
                TravelMode='Car'
            ))
        ]
        
        for test_name, test_func in tests:
            print(f"\n   Testing: {test_name}")
            try:
                result = test_func()
                print(f"   ✅ SUCCESS")
                if test_name == "List calculators":
                    if 'Entries' in result:
                        print(f"      Found {len(result['Entries'])} calculator(s)")
                        for calc in result['Entries']:
                            print(f"      - {calc['CalculatorName']} ({calc.get('Status', 'UNKNOWN')})")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']
                print(f"   ❌ FAILED: {error_code}")
                print(f"      {error_msg}")
                
                # Check for explicit deny
                if "explicit deny" in error_msg.lower():
                    print(f"      🔴 EXPLICIT DENY DETECTED!")
                    print(f"      This means an IAM policy is explicitly denying this action.")
                    print(f"      Check for policies with 'Effect': 'Deny'")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def create_fix_script():
    """Create a script to fix the IAM policy"""
    print("\n" + "="*60)
    print("🔧 CREATING FIX SCRIPT")
    print("="*60)
    
    fix_script = """
#!/usr/bin/env python3
"""
    fix_script += '''
# Fix IAM policy for AWS Location Service
import boto3
import json

def create_location_policy():
    """Create a proper IAM policy for Location Service"""
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "geo:CalculateRoute",
                    "geo:CalculateRouteMatrix",
                    "geo:CreateRouteCalculator",
                    "geo:DescribeRouteCalculator",
                    "geo:ListRouteCalculators",
                    "geo:CreateKey",
                    "geo:DescribeKey",
                    "geo:ListKeys",
                    "geo:AssociateTrackerConsumer"
                ],
                "Resource": "*"
            }
        ]
    }
    
    print("📋 Recommended IAM Policy:")
    print(json.dumps(policy_document, indent=2))
    
    print("\\n💡 To apply this policy:")
    print("1. Go to AWS Console → IAM → Policies")
    print("2. Click 'Create policy'")
    print("3. Choose 'JSON' tab")
    print("4. Paste the policy above")
    print("5. Name it: 'LocationServiceFullAccess'")
    print("6. Click 'Create policy'")
    print("7. Go to Users → locationaccessuser")
    print("8. Attach the new policy")
    print("9. Remove any conflicting policies with 'Deny' statements")

if __name__ == "__main__":
    create_location_policy()
'''
    
    with open('fix_iam.py', 'w') as f:
        f.write(fix_script)
    
    print("✅ Created 'fix_iam.py'")
    print("   Run: python3 fix_iam.py")
    print("   Then follow the instructions to update IAM policy")

if __name__ == "__main__":
    debug_iam_permissions()
    create_fix_script()
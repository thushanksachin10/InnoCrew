
#!/usr/bin/env python3

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
    
    print("\n💡 To apply this policy:")
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

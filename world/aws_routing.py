# world/aws_routing.py - FIXED
import boto3
import os
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def get_aws_config():
    """Get AWS configuration from environment"""
    return {
        'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        'calculator': os.getenv('AWS_ROUTE_CALCULATOR', 'LogisticsRouteCalculator')
    }

class AWSCalculator:
    def __init__(self):
        self.initialized = False
        self.client = None
        
        try:
            config = get_aws_config()
            self.calculator_name = config['calculator']
            
            # Initialize client - boto3 automatically reads from environment
            self.client = boto3.client('location', region_name=config['region'])
            
            # Verify calculator exists (no need to check status - if it exists, it's active)
            try:
                response = self.client.describe_route_calculator(
                    CalculatorName=self.calculator_name
                )
                
                logger.info(f"AWS Calculator '{self.calculator_name}' is ready")
                logger.info(f"  Data Source: {response.get('DataSource', 'N/A')}")
                logger.info(f"  ARN: {response.get('CalculatorArn', 'N/A')}")
                self.initialized = True
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    logger.error(f"AWS Calculator '{self.calculator_name}' not found")
                else:
                    logger.error(f"AWS Error: {e}")
                self.initialized = False
                
        except Exception as e:
            logger.error(f"Failed to initialize AWS Calculator: {e}")
            self.initialized = False
    
    def calculate_route(self, start, end):
        """Calculate route using AWS Location Service"""
        if not self.initialized:
            raise Exception("AWS Calculator not initialized")
        
        try:
            # AWS expects [longitude, latitude] format
            response = self.client.calculate_route(
                CalculatorName=self.calculator_name,
                DeparturePosition=[start[1], start[0]],  # [lon, lat]
                DestinationPosition=[end[1], end[0]],
                TravelMode='Car',  # Options: Car, Truck, Walking
                DistanceUnit='Kilometers',
                DepartNow=True
            )
            
            summary = response['Summary']
            distance_km = summary['Distance']
            duration_hr = summary['DurationSeconds'] / 3600
            
            logger.debug(f"AWS Route: {distance_km:.1f} km, {duration_hr:.2f} hrs")
            return distance_km, duration_hr
            
        except ClientError as e:
            error_msg = e.response['Error']['Message']
            error_code = e.response['Error']['Code']
            
            if error_code == 'AccessDeniedException':
                logger.error(f"AWS Access Denied: {error_msg}")
                raise Exception(f"AWS Access Denied: Check permissions for {self.calculator_name}")
            elif error_code == 'ResourceNotFoundException':
                logger.error(f"Calculator '{self.calculator_name}' not found")
                raise Exception(f"Calculator {self.calculator_name} not found")
            elif error_code == 'NoAvailableApiKeys':
                logger.error(f"No API key associated with calculator '{self.calculator_name}'")
                raise Exception(f"No API key for calculator. Associate an API key in AWS Console.")
            else:
                logger.error(f"AWS routing error ({error_code}): {error_msg}")
                raise Exception(f"AWS Routing Error: {error_msg}")

# Initialize calculator
aws_calculator = AWSCalculator()

def get_aws_route(start, end):
    """Wrapper function for AWS route calculation"""
    return aws_calculator.calculate_route(start, end)
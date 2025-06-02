import json
import boto3
import base64
import os

def lambda_handler(event, context):
    # Initialize SageMaker runtime client
    runtime_client = boto3.client('runtime.sagemaker')
    
    try:
        # Get the endpoint name from environment variable
        endpoint_name = os.environ['SAGEMAKER_ENDPOINT_NAME']
        
        # Get the image data from the event
        # Assuming the image is passed as base64 encoded string
        print(event)
        body = json.loads(event.get("body",""))
        image_data = body.get('image',"")
        if not image_data:
            return {
                'statusCode': 400,
                'body': json.dumps('No image data provided')
            }
            
        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Invoke the SageMaker endpoint
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/x-image',
            Body=image_bytes,
            Accept='application/json'
        )
        
        # Get the prediction results
        prediction = json.loads(response['Body'].read().decode())
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'prediction': prediction
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

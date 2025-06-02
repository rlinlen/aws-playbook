# API Gateway to SageMaker CDK Project

This project creates an API Gateway that invokes a Lambda function, which in turn calls a SageMaker endpoint. The API Gateway is secured with an API key and usage plan.

## Architecture

```
API Gateway (with API Key) → Lambda Function → SageMaker Endpoint
```

## Prerequisites

- AWS CDK installed
- Python 3.9 or later
- AWS CLI configured with appropriate credentials
- A deployed SageMaker endpoint

## Setup

1. Install dependencies using uv:

```bash
uv pip install -r requirements.txt
```

2. Deploy the stack with your SageMaker endpoint name as a context variable:

```bash
cdk deploy --context SAGEMAKER_ENDPOINT_NAME=your-sagemaker-endpoint-name
```

3. After deployment, note the API endpoint URL and API Key ID from the outputs.

4. Retrieve the API key value using AWS CLI:

```bash
aws apigateway get-api-key --api-key YOUR_API_KEY_ID --include-value
```

## Usage

To call the API, send a POST request to the endpoint with the API key in the header:

```bash
curl -X POST \
  https://your-api-id.execute-api.region.amazonaws.com/prod/predict \
  -H 'x-api-key: YOUR_API_KEY_VALUE' \
  -H 'Content-Type: application/json' \
  -d '{"image": "base64_encoded_image_data"}'
```

## Lambda Function

The Lambda function (`sample_lambda.py`) expects a JSON payload with an `image` field containing a base64-encoded image. It decodes the image and sends it to the SageMaker endpoint for inference.

## Security

- API Gateway is secured with an API key
- Usage plan limits API calls to prevent abuse
- Lambda has minimal IAM permissions to invoke the SageMaker endpoint

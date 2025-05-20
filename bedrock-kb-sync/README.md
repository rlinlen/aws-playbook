# Bedrock Knowledge Base Sync

This CDK project sets up an automated sync for your Amazon Bedrock Knowledge Bases on a configurable schedule.

## Prerequisites

- AWS CLI installed and configured
- Python 3.9 or later
- AWS CDK installed (`npm install -g aws-cdk`)
- uv (optional, for Python dependency management)
- jq (required for setup script)

## Setup

1. Clone this repository
2. Set up a Python virtual environment:
   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   
   # Or using standard venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Run the setup script to store your Bedrock Knowledge Base IDs securely:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   The setup script will:
   - Prompt for your AWS region if not set
   - Ask for the parameter name to store your KB IDs (default: `/bedrock/kb/ids`)
   - Allow you to enter multiple Knowledge Base IDs
   - Store the KB IDs as a JSON array in SSM Parameter Store as a SecureString
   
   Example usage:
   ```
   $ ./setup.sh
   Enter your AWS region: us-east-1
   Enter parameter name for storing KB IDs [/bedrock/kb/autosync/ids]: 
   You need to add at least one Knowledge Base ID.
   Enter a Bedrock Knowledge Base ID: kb1-abc123
   Do you want to add another Knowledge Base ID? (y/n): y
   Enter a Bedrock Knowledge Base ID: kb2-def456
   Do you want to add another Knowledge Base ID? (y/n): n
   Parameter stored successfully in SSM Parameter Store at /bedrock/kb/ids
   Knowledge Base IDs stored: ["kb1-abc123","kb2-def456"]
   You can now deploy the CDK stack with: cdk deploy
   To customize the schedule, use: cdk deploy --context schedule_expression="rate(12 hours)"
   ```

4. Deploy the CDK stack:
   ```bash
   cdk deploy
   ```

## Configuration

You can customize the deployment using CDK context parameters:

```bash
# Deploy with a custom schedule (every 12 hours)
cdk deploy --context schedule_expression="rate(12 hours)"

# Deploy with a custom parameter name
cdk deploy --context kb_ids_parameter_name="/my/custom/path/kb-ids"
```

## How it works

1. The CDK stack creates a Lambda function that triggers Bedrock Knowledge Base syncs
2. An EventBridge rule runs on your specified schedule to invoke the Lambda
3. The Lambda retrieves your KB IDs from SSM Parameter Store and starts the sync process for each KB
4. No sensitive information is stored in the code repository

## Security

- The KB IDs are stored in AWS Systems Manager Parameter Store as a SecureString
- IAM permissions are scoped to the minimum required access
- No credentials or sensitive data are stored in the code

## Schedule Expression Examples

- `cron(0 0 * * ? *)` - Daily at midnight UTC
- `cron(0 12 * * ? *)` - Daily at noon UTC
- `rate(1 day)` - Every day
- `rate(12 hours)` - Every 12 hours
- `rate(30 minutes)` - Every 30 minutes (not recommended for production)

## Troubleshooting

If you encounter issues:

1. Check CloudWatch Logs for the Lambda function
2. Verify that the KB IDs parameter exists in SSM Parameter Store
3. Ensure your IAM permissions allow access to Bedrock and SSM Parameter Store
4. Check that the Knowledge Base IDs are valid and accessible

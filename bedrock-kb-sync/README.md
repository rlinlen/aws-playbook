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

3. Run the setup script to store your Bedrock Knowledge Base configurations securely:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   The setup script will:
   - Prompt for your AWS region if not set
   - Ask for the parameter name to store your KB configurations (default: `/bedrock/kb/autosync/ids`)
   - Allow you to enter multiple Knowledge Base IDs with their corresponding Data Source IDs
   - Store the configurations as a JSON array in SSM Parameter Store as a SecureString
   
   Example usage:
   ```
   $ ./setup.sh
   Enter your AWS region: us-east-1
   Enter parameter name for storing KB configurations [/bedrock/kb/autosync/ids]: 
   You need to add at least one Knowledge Base configuration.
   Enter a Bedrock Knowledge Base ID: kb1-abc123
   Enter the Data Source ID for this Knowledge Base: ds1-xyz789
   Do you want to add another Knowledge Base configuration? (y/n): y
   Enter a Bedrock Knowledge Base ID: kb2-def456
   Enter the Data Source ID for this Knowledge Base: ds2-uvw321
   Do you want to add another Knowledge Base configuration? (y/n): n
   Parameter stored successfully in SSM Parameter Store at /bedrock/kb/autosync/ids
   Knowledge Base configurations stored: [{"knowledgeBaseId":"kb1-abc123","dataSourceId":"ds1-xyz789"},{"knowledgeBaseId":"kb2-def456","dataSourceId":"ds2-uvw321"}]
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
cdk deploy --context kb_ids_parameter_name="/my/custom/path/kb-configs"
```

## How it works

1. The CDK stack creates a Lambda function that triggers Bedrock Knowledge Base syncs
2. An EventBridge rule runs on your specified schedule to invoke the Lambda
3. The Lambda retrieves your KB configurations from SSM Parameter Store and starts the sync process for each KB and data source pair
4. No sensitive information is stored in the code repository

## Security

- The KB configurations are stored in AWS Systems Manager Parameter Store as a SecureString
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
2. Verify that the KB configurations parameter exists in SSM Parameter Store
3. Ensure your IAM permissions allow access to Bedrock and SSM Parameter Store
4. Check that the Knowledge Base IDs and Data Source IDs are valid and accessible

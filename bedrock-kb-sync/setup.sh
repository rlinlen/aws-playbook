#!/bin/bash
# setup.sh - Configure parameters for Bedrock KB Sync

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Prompt for the AWS region if not set
if [ -z "$AWS_REGION" ]; then
    read -p "Enter your AWS region: " aws_region
    export AWS_REGION=$aws_region
fi

# Prompt for parameter name or use default
read -p "Enter parameter name for storing KB IDs [/bedrock/kb/autosync/ids]: " kb_ids_param_name
kb_ids_param_name=${kb_ids_param_name:-/bedrock/kb/autosync/ids}

# Initialize an empty array for KB IDs
kb_ids=()

# Function to add a KB ID
add_kb_id() {
    read -p "Enter a Bedrock Knowledge Base ID: " kb_id
    if [ -n "$kb_id" ]; then
        kb_ids+=("$kb_id")
        return 0
    else
        return 1
    fi
}

# Add at least one KB ID
echo "You need to add at least one Knowledge Base ID."
add_kb_id

# Ask if user wants to add more KB IDs
while true; do
    read -p "Do you want to add another Knowledge Base ID? (y/n): " add_more
    if [[ $add_more == "y" || $add_more == "Y" ]]; then
        add_kb_id
    else
        break
    fi
done

# Convert the array to a JSON array
kb_ids_json=$(printf '%s\n' "${kb_ids[@]}" | jq -R . | jq -s .)

# Store the KB IDs in SSM Parameter Store
aws ssm put-parameter \
    --name "$kb_ids_param_name" \
    --value "$kb_ids_json" \
    --type "SecureString" \
    --overwrite

if [ $? -eq 0 ]; then
    echo "Parameter stored successfully in SSM Parameter Store at $kb_ids_param_name"
    echo "Knowledge Base IDs stored: $kb_ids_json"
    echo "You can now deploy the CDK stack with: cdk deploy"
    echo "To customize the schedule, use: cdk deploy --context schedule_expression=\"rate(12 hours)\""
else
    echo "Failed to store parameter. Please check your AWS credentials and permissions."
    exit 1
fi

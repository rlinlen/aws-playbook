#!/bin/bash
# setup.sh - Configure parameters for Bedrock KB Sync

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq is not installed. Please install it first."
    exit 1
fi

# Prompt for the AWS region if not set
if [ -z "$AWS_REGION" ]; then
    read -p "Enter your AWS region: " aws_region
    export AWS_REGION=$aws_region
fi

# Prompt for parameter name or use default
read -p "Enter parameter name for storing KB configurations [/bedrock/kb/autosync/ids]: " kb_ids_param_name
kb_ids_param_name=${kb_ids_param_name:-/bedrock/kb/autosync/ids}

# Initialize an empty array for KB configs
kb_configs=()

# Function to add a KB configuration
add_kb_config() {
    read -p "Enter a Bedrock Knowledge Base ID: " kb_id
    if [ -z "$kb_id" ]; then
        return 1
    fi
    
    read -p "Enter the Data Source ID for this Knowledge Base: " data_source_id
    if [ -z "$data_source_id" ]; then
        echo "Data Source ID is required. Please try again."
        return 1
    fi
    
    # Create a JSON object with both IDs
    kb_config=$(jq -n \
                  --arg kb_id "$kb_id" \
                  --arg ds_id "$data_source_id" \
                  '{knowledgeBaseId: $kb_id, dataSourceId: $ds_id}')
    
    kb_configs+=("$kb_config")
    return 0
}

# Add at least one KB configuration
echo "You need to add at least one Knowledge Base configuration."
add_kb_config

# Ask if user wants to add more KB configurations
while true; do
    read -p "Do you want to add another Knowledge Base configuration? (y/n): " add_more
    if [[ $add_more == "y" || $add_more == "Y" ]]; then
        add_kb_config
    else
        break
    fi
done

# Combine the JSON objects into a JSON array
kb_configs_json=$(printf '%s\n' "${kb_configs[@]}" | jq -s .)

# Store the KB configurations in SSM Parameter Store
aws ssm put-parameter \
    --name "$kb_ids_param_name" \
    --value "$kb_configs_json" \
    --type "SecureString" \
    --overwrite

if [ $? -eq 0 ]; then
    echo "Parameter stored successfully in SSM Parameter Store at $kb_ids_param_name"
    echo "Knowledge Base configurations stored: $kb_configs_json"
    echo "You can now deploy the CDK stack with: cdk deploy"
    echo "To customize the schedule, use: cdk deploy --context schedule_expression=\"rate(12 hours)\""
else
    echo "Failed to store parameter. Please check your AWS credentials and permissions."
    exit 1
fi

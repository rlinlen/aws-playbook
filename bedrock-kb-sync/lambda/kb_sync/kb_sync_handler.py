import os
import json
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
ssm_client = boto3.client('ssm')
bedrock_agent_client = boto3.client('bedrock-agent')

def handler(event, context):
    """
    Lambda handler to trigger Bedrock Knowledge Base sync for specific KB and data source pairs.
    
    This function retrieves a list of KB and data source pairs from SSM Parameter Store
    and initiates a sync job for each specific pair.
    """
    try:
        # Get the KB config from SSM Parameter Store
        kb_ids_param_name = os.environ.get('KB_IDS_PARAMETER_NAME', '/bedrock/kb/autosync/ids')
        logger.info(f"Retrieving KB config from parameter: {kb_ids_param_name}")
        
        response = ssm_client.get_parameter(
            Name=kb_ids_param_name,
            WithDecryption=True
        )
        
        # Parse the JSON array of KB configs
        kb_configs = json.loads(response['Parameter']['Value'])
        logger.info(f"Retrieved {len(kb_configs)} Knowledge Base configurations")
        
        results = []
        
        # Start ingestion jobs for each knowledge base and data source pair
        for kb_config in kb_configs:
            # Check if the config is in the new format (object with knowledgeBaseId and dataSourceId)
            if isinstance(kb_config, dict) and 'knowledgeBaseId' in kb_config and 'dataSourceId' in kb_config:
                kb_id = kb_config['knowledgeBaseId']
                data_source_id = kb_config['dataSourceId']
                
                try:
                    logger.info(f"Starting ingestion job for KB: {kb_id}, Data Source: {data_source_id}")
                    
                    response = bedrock_agent_client.start_ingestion_job(
                        knowledgeBaseId=kb_id,
                        dataSourceId=data_source_id
                    )
                    
                    logger.info(f"Successfully started KB sync job for {kb_id}, Data Source: {data_source_id}, Job ID: {response['ingestionJobId']}")
                    
                    results.append({
                        'knowledgeBaseId': kb_id,
                        'dataSourceId': data_source_id,
                        'jobId': response['ingestionJobId'],
                        'status': 'started'
                    })
                    
                except Exception as kb_error:
                    logger.error(f"Error syncing KB {kb_id}, Data Source {data_source_id}: {str(kb_error)}")
                    results.append({
                        'knowledgeBaseId': kb_id,
                        'dataSourceId': data_source_id,
                        'status': 'error',
                        'error': str(kb_error)
                    })
            
            # Handle legacy format (just KB ID string)
            elif isinstance(kb_config, str):
                kb_id = kb_config
                logger.warning(f"Legacy KB ID format detected for {kb_id}. Please update to new format with dataSourceId.")
                
                results.append({
                    'knowledgeBaseId': kb_id,
                    'status': 'skipped',
                    'reason': 'Missing dataSourceId. Please update parameter store with new format.'
                })
            
            else:
                logger.error(f"Invalid KB configuration format: {kb_config}")
                results.append({
                    'config': kb_config,
                    'status': 'error',
                    'reason': 'Invalid configuration format'
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Knowledge base sync process completed for {len(kb_configs)} configurations',
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Error in sync process: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error in knowledge base sync process',
                'error': str(e)
            })
        }

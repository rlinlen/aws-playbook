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
    Lambda handler to trigger Bedrock Knowledge Base sync for multiple KBs.
    
    This function retrieves a list of Knowledge Base IDs from SSM Parameter Store
    and initiates a sync job for each knowledge base.
    """
    try:
        # Get the KB IDs from SSM Parameter Store
        kb_ids_param_name = os.environ.get('KB_IDS_PARAMETER_NAME', '/bedrock/kb/autosync/ids')
        logger.info(f"Retrieving KB IDs from parameter: {kb_ids_param_name}")
        
        response = ssm_client.get_parameter(
            Name=kb_ids_param_name,
            WithDecryption=True
        )
        
        # Parse the JSON array of KB IDs
        kb_ids = json.loads(response['Parameter']['Value'])
        logger.info(f"Retrieved {len(kb_ids)} Knowledge Base IDs")
        
        results = []
        
        # Start ingestion jobs for each knowledge base
        for kb_id in kb_ids:
            try:
                logger.info(f"Starting ingestion job for Knowledge Base: {kb_id}")
                
                response = bedrock_agent_client.start_ingestion_job(
                    knowledgeBaseId=kb_id
                )
                
                logger.info(f"Successfully started KB sync job for {kb_id}: {response['ingestionJobId']}")
                
                results.append({
                    'knowledgeBaseId': kb_id,
                    'jobId': response['ingestionJobId'],
                    'status': 'started'
                })
                
            except Exception as kb_error:
                logger.error(f"Error syncing knowledge base {kb_id}: {str(kb_error)}")
                results.append({
                    'knowledgeBaseId': kb_id,
                    'status': 'error',
                    'error': str(kb_error)
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Knowledge base sync process completed for {len(kb_ids)} knowledge bases',
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

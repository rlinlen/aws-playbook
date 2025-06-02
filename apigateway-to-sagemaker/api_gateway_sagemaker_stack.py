from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_iam as iam,
    Duration,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

class ApiGatewaySagemakerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Get SageMaker endpoint name from context
        sagemaker_endpoint_name = self.node.try_get_context("SAGEMAKER_ENDPOINT_NAME")
        if not sagemaker_endpoint_name:
            raise ValueError("SAGEMAKER_ENDPOINT_NAME must be provided in CDK context")

        # Create Lambda function that will invoke SageMaker endpoint
        sagemaker_lambda = lambda_.Function(
            self, "SageMakerLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="sample_lambda.lambda_handler",
            code=lambda_.Code.from_asset(".", exclude=["cdk.out", ".venv"]),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "SAGEMAKER_ENDPOINT_NAME": sagemaker_endpoint_name
            }
        )

        # Grant Lambda permission to invoke SageMaker endpoint
        sagemaker_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sagemaker:InvokeEndpoint"],
                resources=["*"]  # For production, scope this down to specific endpoint ARN
            )
        )

        # Create API Gateway
        api = apigateway.RestApi(
            self, "SageMakerAPI",
            rest_api_name="SageMaker Inference API",
            description="API Gateway to invoke SageMaker endpoint via Lambda",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )

        # Create API key
        api_key = apigateway.ApiKey(
            self, "SageMakerApiKey",
            api_key_name="SageMakerApiKey",
            enabled=True
        )

        # Create usage plan
        usage_plan = apigateway.UsagePlan(
            self, "SageMakerUsagePlan",
            name="SageMakerUsagePlan",
            api_stages=[
                apigateway.UsagePlanPerApiStage(
                    api=api,
                    stage=api.deployment_stage
                )
            ],
            # Define throttling limits
            throttle=apigateway.ThrottleSettings(
                rate_limit=10,
                burst_limit=20
            ),
            # Define quota limits (optional)
            quota=apigateway.QuotaSettings(
                limit=1000,
                period=apigateway.Period.MONTH
            )
        )

        # Add API key to usage plan
        usage_plan.add_api_key(api_key)

        # Create API resource and method
        predict_resource = api.root.add_resource("predict")
        
        # Integration with Lambda
        lambda_integration = apigateway.LambdaIntegration(
            sagemaker_lambda,
            proxy=True,
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                )
            ]
        )

        # Add POST method with API key required
        predict_resource.add_method(
            "POST", 
            lambda_integration,
            api_key_required=True,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    }
                )
            ]
        )

        # Outputs
        CfnOutput(
            self, "ApiEndpoint",
            value=f"{api.url}predict",
            description="API Gateway endpoint URL for the predict resource"
        )
        
        CfnOutput(
            self, "ApiKeyId",
            value=api_key.key_id,
            description="API Key ID (use AWS CLI to retrieve the actual key value)"
        )

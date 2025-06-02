#!/usr/bin/env python3
import os
from aws_cdk import App, Environment

from api_gateway_sagemaker_stack import ApiGatewaySagemakerStack

app = App()

ApiGatewaySagemakerStack(
    app, 
    "ApiGatewaySagemakerStack",
    env=Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION")
    )
)

app.synth()

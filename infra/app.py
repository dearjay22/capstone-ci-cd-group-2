#!/usr/bin/env python3
import aws_cdk as cdk
from deployment_stack import DeploymentStack

app = cdk.App()

DeploymentStack(app, "CapstoneStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1"
    ),
    description="Capstone CI/CD Project - Complete Deployment"
)

app.synth()
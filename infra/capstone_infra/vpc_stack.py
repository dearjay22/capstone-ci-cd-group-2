from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct

class VpcStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        # Create a small VPC with two AZs but minimal nat gateways to reduce costs
        self.vpc = ec2.Vpc(self, "CapstoneVpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(name="private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24)
            ]
        )
        # Export VPC id as CloudFormation output
        from aws_cdk import CfnOutput
        CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
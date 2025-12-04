#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import App
from capstone_infra.vpc_stack import VpcStack
from capstone_infra.rds_stack import RdsStack
from capstone_infra.ec2_stack import Ec2Stack

app = App()

vpc_stack = VpcStack(app, "CapstoneVpcStack")
rds_stack = RdsStack(app, "CapstoneRdsStack", vpc=vpc_stack.vpc)
ec2_stack = Ec2Stack(app, "CapstoneEc2Stack", vpc=vpc_stack.vpc)

app.synth()
print('CDK app ready - NOTE: stacks will create AWS resources that may incur charges. Use with caution.')
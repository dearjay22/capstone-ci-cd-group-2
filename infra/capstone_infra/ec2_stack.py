from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

class Ec2Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, vpc, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        # Create security group
        sg = ec2.SecurityGroup(self, "CapstoneSG", vpc=vpc, allow_all_outbound=True)
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP")
        # Minimal EC2 instance (t3.micro) - for demo only
        ami = ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)
        instance = ec2.Instance(self, "CapstoneInstance",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            machine_image=ami,
            vpc=vpc,
            security_group=sg
        )
        # Give instance permissions to read SSM parameters if needed
        instance.role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
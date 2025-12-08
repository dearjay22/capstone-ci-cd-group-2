from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    aws_secretsmanager as secrets,
    CfnOutput,
    Duration,
)
from constructs import Construct


class DeploymentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(
            self,
            "CapstoneVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # Bandit-safe Secret Manager configuration
        db_secret = secrets.Secret(
            self,
            "DbCredentials",
            generate_secret_string=secrets.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                password_length=16,
                generate_string_key="username",
            ),
        )

        # RDS Security Group
        rds_sg = ec2.SecurityGroup(
            self,
            "RdsSecurityGroup",
            vpc=vpc,
            description="Security group for RDS MySQL",
            allow_all_outbound=False,
        )

        database = rds.DatabaseInstance(
            self,
            "CapstoneDB",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_35
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            credentials=rds.Credentials.from_secret(db_secret),
            database_name="capstone",
            allocated_storage=20,
            max_allocated_storage=20,
            security_groups=[rds_sg],
            backup_retention=Duration.days(0),
            deletion_protection=False,
            removal_policy=Stack.of(self).node.try_get_context("retain_resources")
            and Stack.of(self).RETAIN
            or Stack.of(self).DESTROY,
        )

        # EC2 SG
        ec2_sg = ec2.SecurityGroup(
            self,
            "EC2SecurityGroup",
            vpc=vpc,
            description="Security group for EC2 instance",
            allow_all_outbound=True,
        )

        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP")
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH")
        rds_sg.add_ingress_rule(ec2_sg, ec2.Port.tcp(3306), "MySQL From EC2")

        ec2_role = iam.Role(
            self,
            "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
            ],
        )

        db_secret.grant_read(ec2_role)

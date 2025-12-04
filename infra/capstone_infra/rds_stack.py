from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secrets,
)
from constructs import Construct

class RdsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, vpc, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        # Create a Secrets Manager secret for DB credentials
        secret = secrets.Secret(self, "DbCredentials",
            generate_secret_string=secrets.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                password_length=16,
                secret_string_template='{"username":"admin"}',
                generate_string_key="password"
            )
        )
        # Minimal RDS instance (free-tier eligible type) - NOTE: check free-tier eligibility
        db = rds.DatabaseInstance(self, "CapstoneRds",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_28
            ),
            # WARNING: storage, instance type may incur cost. Use only for demo and destroy after.
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            credentials=rds.Credentials.from_secret(secret),
            allocated_storage=20,
            max_allocated_storage=20,
            removal_policy=Stack.of(self).RETAIN
        )
        from aws_cdk import CfnOutput
        CfnOutput(self, "RdsEndpoint", value=db.db_instance_endpoint_address)
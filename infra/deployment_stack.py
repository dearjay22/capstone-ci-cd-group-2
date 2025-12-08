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

# Note: removed unused 'base64' import


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

        # Database credentials secret
        db_secret = secrets.Secret(
            self,
            "DbCredentials",
            generate_secret_string=secrets.SecretStringGenerator(
                exclude_punctuation=True,
                include_space=False,
                password_length=16,
                secret_string_template='{"username":"admin"}',
                generate_string_key="password",
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

        # RDS MySQL Database
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
            backup_retention=Duration.days(0),  # No backups for demo
            deletion_protection=False,
            removal_policy=Stack.of(self).node.try_get_context("retain_resources")
            and Stack.of(self).RETAIN
            or Stack.of(self).DESTROY,
        )

        # EC2 Security Group
        ec2_sg = ec2.SecurityGroup(
            self,
            "EC2SecurityGroup",
            vpc=vpc,
            description="Security group for EC2 instance",
            allow_all_outbound=True,
        )

        # Allow HTTP from anywhere
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")

        # Allow SSH from anywhere (restrict to your IP in production)
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH")

        # Allow EC2 to access RDS
        rds_sg.add_ingress_rule(ec2_sg, ec2.Port.tcp(3306), "Allow MySQL from EC2")

        # IAM Role for EC2
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

        # Allow EC2 to read the DB secret
        db_secret.grant_read(ec2_role)

        # User data script to setup EC2
        user_data = ec2.UserData.for_linux()

        # Build the user-data commands as a list of reasonably short strings.
        # Use normal strings where there are no Python placeholders.
        user_data.add_commands(
            "#!/bin/bash",
            "set -e",
            "exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1",
            "echo '=== Updating system ==='",
            "yum update -y",
            "echo '=== Installing Docker ==='",
            "yum install -y docker",
            "systemctl start docker",
            "systemctl enable docker",
            "usermod -aG docker ec2-user",
            "echo '=== Installing Docker Compose ==='",
            "curl -L https://github.com/docker/compose/releases/latest/download/"
            "docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose",
            "chmod +x /usr/local/bin/docker-compose",
            "ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose",
            "echo '=== Installing Git ==='",
            "yum install -y git",
            "echo '=== Installing AWS CLI ==='",
            "curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip",
            "yum install -y unzip",
            "unzip awscliv2.zip",
            "./aws/install",
            "yum install -y jq",
            "echo '=== Cloning repository ==='",
            "cd /home/ec2-user",
            "git clone https://github.com/YOUR-USERNAME/capstone-ci-cd-group-2.git app",
            "chown -R ec2-user:ec2-user app",
            "cd app",
            "echo '=== Fetching database credentials ==='",
            # Use Python f-strings only when inserting Python values (db_secret.secret_arn and self.region)
            "DB_SECRET=$(aws secretsmanager get-secret-value "
            f"--secret-id {db_secret.secret_arn} --query SecretString --output text --region {self.region})",
            "DB_USER=$(echo $DB_SECRET | jq -r .username)",
            "DB_PASS=$(echo $DB_SECRET | jq -r .password)",
            f"DB_HOST={database.db_instance_endpoint_address}",
            "DB_NAME=capstone",
            "echo '=== Waiting for database to be ready ==='",
            "for i in {1..30}; do",
            "  if timeout 5 bash -c 'cat < /dev/null > /dev/tcp/$DB_HOST/3306' 2>/dev/null; then",
            "    echo 'Database is ready!'",
            "    break",
            "  fi",
            "  echo 'Waiting for database... attempt $i'",
            "  sleep 10",
            "done",
            "echo '=== Creating production docker-compose.yml ==='",
            "cat > docker-compose.prod.yml << 'EOFCOMPOSE'",
            "version: '3.8'",
            "services:",
            "  users:",
            "    build: ./users-service",
            "    environment:",
            "      DB_HOST: ${DB_HOST}",
            "      DB_USER: ${DB_USER}",
            "      DB_PASS: ${DB_PASS}",
            "      DB_NAME: ${DB_NAME}",
            "    restart: always",
            "    ports:",
            "      - '5001:5001'",
            "",
            "  products:",
            "    build: ./products-service",
            "    environment:",
            "      DB_HOST: ${DB_HOST}",
            "      DB_USER: ${DB_USER}",
            "      DB_PASS: ${DB_PASS}",
            "      DB_NAME: ${DB_NAME}",
            "    restart: always",
            "    ports:",
            "      - '5002:5002'",
            "",
            "  orders:",
            "    build: ./orders-service",
            "    environment:",
            "      DB_HOST: ${DB_HOST}",
            "      DB_USER: ${DB_USER}",
            "      DB_PASS: ${DB_PASS}",
            "      DB_NAME: ${DB_NAME}",
            "    restart: always",
            "    ports:",
            "      - '5003:5003'",
            "",
            "  frontend:",
            "    build: ./frontend",
            "    environment:",
            "      USERS_HOST: http://users:5001",
            "      PRODUCTS_HOST: http://products:5002",
            "      ORDERS_HOST: http://orders:5003",
            "    restart: always",
            "    ports:",
            "      - '80:3000'",
            "    depends_on:",
            "      - users",
            "      - products",
            "      - orders",
            "EOFCOMPOSE",
            "echo '=== Creating .env file ==='",
            "cat > .env << EOFENV",
            "DB_HOST=$DB_HOST",
            "DB_USER=$DB_USER",
            "DB_PASS=$DB_PASS",
            "DB_NAME=$DB_NAME",
            "EOFENV",
            "echo '=== Installing MySQL client ==='",
            "yum install -y mysql",
            "echo '=== Initializing database ==='",
            "mysql -h $DB_HOST -u $DB_USER -p$DB_PASS < scripts/init_db.sql || "
            "echo 'Database init failed, may already be initialized'",
            "echo '=== Building and starting services ==='",
            "docker-compose -f docker-compose.prod.yml build",
            "docker-compose -f docker-compose.prod.yml up -d",
            "echo '=== Setting up log rotation ==='",
            "cat > /etc/logrotate.d/docker-compose << 'EOFLOG'",
            "/home/ec2-user/app/logs/*.log {",
            "    daily",
            "    rotate 7",
            "    compress",
            "    delaycompress",
            "    missingok",
            "    notifempty",
            "}",
            "EOFLOG",
            "echo '=== Creating systemd service ==='",
            "cat > /etc/systemd/system/capstone-app.service << 'EOFSVC'",
            "[Unit]",
            "Description=Capstone Application",
            "Requires=docker.service",
            "After=docker.service",
            "",
            "[Service]",
            "Type=oneshot",
            "RemainAfterExit=yes",
            "WorkingDirectory=/home/ec2-user/app",
            "ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d",
            "ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down",
            "User=root",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "EOFSVC",
            "systemctl daemon-reload",
            "systemctl enable capstone-app.service",
            "echo '=== Deployment complete! ==='",
            "docker-compose -f docker-compose.prod.yml ps",
        )

        # Create EC2 instance
        instance = ec2.Instance(
            self,
            "CapstoneInstance",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL
            ),  # t3.small for better performance
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=ec2_sg,
            role=ec2_role,
            user_data=user_data,
            user_data_causes_replacement=True,
        )

        # Outputs
        CfnOutput(
            self,
            "InstancePublicIP",
            value=instance.instance_public_ip,
            description="Public IP of EC2 instance",
        )

        CfnOutput(
            self,
            "ApplicationURL",
            value=f"http://{instance.instance_public_ip}",
            description="Access your application here",
        )

        CfnOutput(
            self,
            "DatabaseEndpoint",
            value=database.db_instance_endpoint_address,
            description="RDS Database Endpoint",
        )

        CfnOutput(
            self,
            "SSHCommand",
            value=f"ssh -i your-key.pem ec2-user@{instance.instance_public_ip}",
            description="SSH into the instance",
        )

        CfnOutput(
            self,
            "DatabaseSecretArn",
            value=db_secret.secret_arn,
            description="ARN of the database credentials secret",
        )

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    aws_secretsmanager as secrets,
    CfnOutput,
    Duration,
    RemovalPolicy,
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

        # Secret Manager
        db_secret = secrets.Secret(
            self,
            "DbCredentials",
            generate_secret_string=secrets.SecretStringGenerator(
                secret_string_template='{"username": "admin"}',
                generate_string_key="password",
                exclude_punctuation=True,
                include_space=False,
                password_length=16,
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

        # RDS Instance
        database = rds.DatabaseInstance(
            self,
            "CapstoneDB",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_39
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
            removal_policy=(
                RemovalPolicy.RETAIN
                if Stack.of(self).node.try_get_context("retain_resources")
                else RemovalPolicy.DESTROY
            ),
        )

        CfnOutput(
            self,
            "DatabaseEndpoint",
            value=database.db_instance_endpoint_address,
            description="RDS Database Endpoint",
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


        # User data script to setup EC2
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "#!/bin/bash",
            "set -e",
            "exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1",
            # Update system
            "echo '=== Updating system ==='",
            "yum update -y",
            # Install Docker
            "echo '=== Installing Docker ==='",
            "yum install -y docker",
            "systemctl start docker",
            "systemctl enable docker",
            "usermod -aG docker ec2-user",
            # Install Docker Compose
            "echo '=== Installing Docker Compose ==='",
            "curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose",
            "chmod +x /usr/local/bin/docker-compose",
            "ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose",
            # Install Git
            "echo '=== Installing Git ==='",
            "yum install -y git",
            # Install AWS CLI v2
            "echo '=== Installing AWS CLI ==='",
            "curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip",
            "yum install -y unzip",
            "unzip awscliv2.zip",
            "./aws/install",
            # Install jq for JSON parsing
            "yum install -y jq",
            # Clone repository
            "echo '=== Cloning repository ==='",
            "cd /home/ec2-user",
            "git clone https://github.com/dearjay22/capstone-ci-cd-group-2.git app",
            "chown -R ec2-user:ec2-user app",
            "cd app",
            # Get RDS credentials from Secrets Manager
            f"echo '=== Fetching database credentials ==='",
            f"DB_SECRET=$(aws secretsmanager get-secret-value --secret-id {db_secret.secret_arn} --query SecretString --output text --region {self.region})",
            "DB_USER=$(echo $DB_SECRET | jq -r .username)",
            "DB_PASS=$(echo $DB_SECRET | jq -r .password)",
            f"DB_HOST={database.db_instance_endpoint_address}",
            "DB_NAME=capstone",
            # Wait for RDS to be ready
            "echo '=== Waiting for database to be ready ==='",
            "for i in {1..30}; do",
            "  if timeout 5 bash -c 'cat < /dev/null > /dev/tcp/$DB_HOST/3306' 2>/dev/null; then",
            "    echo 'Database is ready!'",
            "    break",
            "  fi",
            "  echo 'Waiting for database... attempt $i'",
            "  sleep 10",
            "done",
            # Create production docker-compose file
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
            "    healthcheck:",
            "      test: ['CMD', 'curl', '-f', 'http://localhost:5001/health']",
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 40s",
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
            "    healthcheck:",
            "      test: ['CMD', 'curl', '-f', 'http://localhost:5002/health']",
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 40s",
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
            "    healthcheck:",
            "      test: ['CMD', 'curl', '-f', 'http://localhost:5003/health']",
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 40s",
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
            "      users:",
            "        condition: service_healthy",
            "      products:",
            "        condition: service_healthy",
            "      orders:",
            "        condition: service_healthy",
            "    healthcheck:",
            "      test: ['CMD', 'curl', '-f', 'http://localhost:3000/health']",
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 60s",
            "EOFCOMPOSE",
            # Create .env file with database credentials
            "echo '=== Creating .env file ==='",
            "cat > .env << EOFENV",
            "DB_HOST=$DB_HOST",
            "DB_USER=$DB_USER",
            "DB_PASS=$DB_PASS",
            "DB_NAME=$DB_NAME",
            "EOFENV",
            # Install mysql client and initialize database
            "echo '=== Installing MySQL client ==='",
            "yum install -y mysql",
            "echo '=== Initializing database ==='",
            "mysql -h $DB_HOST -u $DB_USER -p$DB_PASS < scripts/init_db.sql || echo 'Database init failed, may already be initialized'",
            # Build and start services
            "echo '=== Building and starting services ==='",
            "docker-compose -f docker-compose.prod.yml build",
            "docker-compose -f docker-compose.prod.yml up -d",
            # Create systemd service for auto-restart
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
            "docker-compose -f docker-compose.prod.yml ps"
        )
        # Create EC2 instance
        instance = ec2.Instance(
            self,
            "CapstoneInstance",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.SMALL  # t3.small for better performance
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=ec2_sg,
            role=ec2_role,
            user_data=user_data,
            user_data_causes_replacement=True
        )
        # Outputs
        CfnOutput(
            self,
            "InstancePublicIP",
            value=instance.instance_public_ip,
            description="Public IP of EC2 instance"
        )
        CfnOutput(
            self,
            "ApplicationURL",
            value=f"http://{instance.instance_public_ip}",
            description="Access your application here"
        )
        CfnOutput(
            self,
            "SSHCommand",
            value=f"ssh -i your-key.pem ec2-user@{instance.instance_public_ip}",
            description="SSH into the instance"
        )
        CfnOutput(
            self,
            "DatabaseSecretArn",
            value=db_secret.secret_arn,
            description="ARN of the database credentials secret"
        )

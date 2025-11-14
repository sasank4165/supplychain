"""CDK Stack for Supply Chain Agentic AI Application - Production Ready"""
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Tags,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_logs as logs,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_wafv2 as waf,
    aws_backup as backup,
    aws_events as events,
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,
    aws_glue as glue,
)
from constructs import Construct

class NetworkStack(Stack):
    """VPC and networking infrastructure"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # VPC with public and private subnets across 3 AZs
        self.vpc = ec2.Vpc(
            self, "SupplyChainVPC",
            vpc_name="supply-chain-vpc",
            max_azs=3,
            nat_gateways=3,  # High availability
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        
        # VPC Flow Logs for security monitoring
        log_group = logs.LogGroup(
            self, "VPCFlowLogsGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        ec2.FlowLog(
            self, "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group)
        )
        
        # Security Groups
        self.lambda_sg = ec2.SecurityGroup(
            self, "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions",
            allow_all_outbound=True
        )
        
        self.vpc_endpoint_sg = ec2.SecurityGroup(
            self, "VPCEndpointSecurityGroup",
            vpc=self.vpc,
            description="Security group for VPC endpoints",
            allow_all_outbound=False
        )
        
        self.vpc_endpoint_sg.add_ingress_rule(
            peer=self.lambda_sg,
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS from Lambda"
        )
        
        # VPC Endpoints for AWS services (cost optimization & security)
        self.vpc.add_interface_endpoint(
            "DynamoDBEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.DYNAMODB,
            security_groups=[self.vpc_endpoint_sg]
        )
        
        self.vpc.add_interface_endpoint(
            "BedrockRuntimeEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
            security_groups=[self.vpc_endpoint_sg]
        )
        
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        
        # Outputs
        CfnOutput(self, "VPCId", value=self.vpc.vpc_id)
        CfnOutput(self, "LambdaSecurityGroupId", value=self.lambda_sg.security_group_id)

class SecurityStack(Stack):
    """Security infrastructure - KMS, Secrets Manager, IAM"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # KMS Keys for encryption
        self.data_key = kms.Key(
            self, "DataEncryptionKey",
            description="KMS key for data encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
            pending_window=Duration.days(30)
        )
        
        self.data_key.add_alias("alias/supply-chain-data")
        
        # Secrets Manager for sensitive configuration
        self.db_config_secret = secretsmanager.Secret(
            self, "DatabaseConfig",
            description="Database configuration",
            secret_object_value={
                "athena_database": secretsmanager.SecretValue.unsafe_plain_text("aws-gpl-cog-sc-db"),
                "athena_catalog": secretsmanager.SecretValue.unsafe_plain_text("AwsDataCatalog")
            },
            encryption_key=self.data_key
        )
        
        # Outputs
        CfnOutput(self, "DataKeyId", value=self.data_key.key_id)
        CfnOutput(self, "DataKeyArn", value=self.data_key.key_arn)
        CfnOutput(self, "SecretArn", value=self.db_config_secret.secret_arn)

class DataStack(Stack):
    """Data infrastructure - S3, Glue, Athena"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        kms_key: kms.Key,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # S3 Buckets with versioning and encryption
        self.data_bucket = s3.Bucket(
            self, "DataBucket",
            bucket_name=f"supply-chain-data-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToIA",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(180)
                        )
                    ],
                    enabled=True
                )
            ],
            server_access_logs_bucket=None  # Create separate logging bucket in production
        )
        
        self.athena_results_bucket = s3.Bucket(
            self, "AthenaResultsBucket",
            bucket_name=f"supply-chain-athena-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldResults",
                    expiration=Duration.days(30),
                    enabled=True
                )
            ]
        )
        
        # Glue Database
        self.glue_database = glue.CfnDatabase(
            self, "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="aws-gpl-cog-sc-db",
                description="Supply chain data catalog"
            )
        )
        
        # Glue Crawler for automatic schema discovery
        crawler_role = iam.Role(
            self, "GlueCrawlerRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ]
        )
        
        self.data_bucket.grant_read(crawler_role)
        
        # Outputs
        CfnOutput(self, "DataBucketName", value=self.data_bucket.bucket_name)
        CfnOutput(self, "AthenaResultsBucketName", value=self.athena_results_bucket.bucket_name)
        CfnOutput(self, "GlueDatabaseName", value=self.glue_database.ref)

class SupplyChainAgentStack(Stack):
    """Main application stack - Lambda, DynamoDB, API Gateway"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        vpc: ec2.Vpc,
        lambda_sg: ec2.SecurityGroup,
        kms_key: kms.Key,
        data_bucket: s3.Bucket,
        athena_results_bucket: s3.Bucket,
        db_config_secret: secretsmanager.Secret,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # S3 Bucket for Athena results
        athena_results_bucket = s3.Bucket(
            self, "AthenaResultsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(30),
                    enabled=True
                )
            ]
        )
        
        # DynamoDB Tables
        session_table = dynamodb.Table(
            self, "SessionTable",
            table_name="supply-chain-agent-sessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            time_to_live_attribute="ttl"
        )
        
        memory_table = dynamodb.Table(
            self, "MemoryTable",
            table_name="supply-chain-agent-memory",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True
        )
        
        # IAM Role for Lambda functions
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Grant permissions
        athena_results_bucket.grant_read_write(lambda_role)
        session_table.grant_read_write_data(lambda_role)
        memory_table.grant_read_write_data(lambda_role)
        
        # Athena permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
                "athena:StopQueryExecution"
            ],
            resources=["*"]
        ))
        
        # Glue Data Catalog permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "glue:GetDatabase",
                "glue:GetTable",
                "glue:GetPartitions"
            ],
            resources=["*"]
        ))
        
        # Bedrock permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=["*"]
        ))
        
        # Lambda Layer for common dependencies
        lambda_layer = lambda_.LayerVersion(
            self, "CommonLayer",
            code=lambda_.Code.from_asset("../lambda_layers/common"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Common dependencies for supply chain agents"
        )
        
        # Environment variables
        lambda_env = {
            "ATHENA_OUTPUT_LOCATION": f"s3://{athena_results_bucket.bucket_name}/",
            "ATHENA_DATABASE": "aws-gpl-cog-sc-db",
            "SESSION_TABLE": session_table.table_name,
            "MEMORY_TABLE": memory_table.table_name,
            "AWS_REGION": self.region
        }
        
        # Lambda Functions
        inventory_optimizer = lambda_.Function(
            self, "InventoryOptimizer",
            function_name="supply-chain-inventory-optimizer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="inventory_optimizer.lambda_handler",
            code=lambda_.Code.from_asset("../lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=512,
            environment=lambda_env,
            layers=[lambda_layer],
            log_retention=logs.RetentionDays.ONE_MONTH
        )
        
        logistics_optimizer = lambda_.Function(
            self, "LogisticsOptimizer",
            function_name="supply-chain-logistics-optimizer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="logistics_optimizer.lambda_handler",
            code=lambda_.Code.from_asset("../lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=512,
            environment=lambda_env,
            layers=[lambda_layer],
            log_retention=logs.RetentionDays.ONE_MONTH
        )
        
        supplier_analyzer = lambda_.Function(
            self, "SupplierAnalyzer",
            function_name="supply-chain-supplier-analyzer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="supplier_analyzer.lambda_handler",
            code=lambda_.Code.from_asset("../lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=512,
            environment=lambda_env,
            layers=[lambda_layer],
            log_retention=logs.RetentionDays.ONE_MONTH
        )
        
        # Cognito User Pool for authentication
        user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="supply-chain-agent-users",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True, username=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        user_pool_client = user_pool.add_client(
            "AppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            generate_secret=False
        )
        
        # API Gateway
        api = apigw.RestApi(
            self, "SupplyChainAPI",
            rest_api_name="supply-chain-agent-api",
            description="API for Supply Chain Agentic AI",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            )
        )
        
        # Cognito Authorizer
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "APIAuthorizer",
            cognito_user_pools=[user_pool]
        )
        
        # API Resources and Methods
        query_resource = api.root.add_resource("query")
        query_resource.add_method(
            "POST",
            apigw.LambdaIntegration(inventory_optimizer),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO
        )
        
        # CloudWatch Dashboard (optional)
        # Add monitoring dashboard here if needed
        
        # Outputs
        from aws_cdk import CfnOutput
        
        CfnOutput(self, "AthenaResultsBucketName",
            value=athena_results_bucket.bucket_name,
            description="S3 bucket for Athena query results"
        )
        
        CfnOutput(self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )
        
        CfnOutput(self, "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )
        
        CfnOutput(self, "APIEndpoint",
            value=api.url,
            description="API Gateway endpoint URL"
        )
        
        # DynamoDB Tables with encryption and backups
        session_table = dynamodb.Table(
            self, "SessionTable",
            table_name="supply-chain-agent-sessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=kms_key,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            time_to_live_attribute="ttl",
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        memory_table = dynamodb.Table(
            self, "MemoryTable",
            table_name="supply-chain-agent-memory",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=kms_key,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True
        )
        
        # Add GSI for querying by persona
        memory_table.add_global_secondary_index(
            index_name="persona-index",
            partition_key=dynamodb.Attribute(
                name="persona",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # IAM Role for Lambda with least privilege
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            ],
            description="Execution role for supply chain Lambda functions"
        )
        
        # Grant specific permissions
        athena_results_bucket.grant_read_write(lambda_role)
        data_bucket.grant_read(lambda_role)
        session_table.grant_read_write_data(lambda_role)
        memory_table.grant_read_write_data(lambda_role)
        kms_key.grant_encrypt_decrypt(lambda_role)
        db_config_secret.grant_read(lambda_role)
        
        # Athena permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
                "athena:StopQueryExecution",
                "athena:GetWorkGroup"
            ],
            resources=[
                f"arn:aws:athena:{self.region}:{self.account}:workgroup/*"
            ]
        ))
        
        # Glue Data Catalog permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "glue:GetDatabase",
                "glue:GetTable",
                "glue:GetPartitions",
                "glue:GetTableVersions"
            ],
            resources=[
                f"arn:aws:glue:{self.region}:{self.account}:catalog",
                f"arn:aws:glue:{self.region}:{self.account}:database/*",
                f"arn:aws:glue:{self.region}:{self.account}:table/*/*"
            ]
        ))
        
        # Bedrock permissions (scoped to specific models)
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
            ]
        ))
        
        # Lambda Layer for dependencies
        lambda_layer = lambda_.LayerVersion(
            self, "CommonLayer",
            code=lambda_.Code.from_asset("../lambda_layers/common"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Common dependencies for supply chain agents",
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Environment variables
        lambda_env = {
            "ATHENA_OUTPUT_LOCATION": f"s3://{athena_results_bucket.bucket_name}/",
            "ATHENA_DATABASE": "aws-gpl-cog-sc-db",
            "SESSION_TABLE": session_table.table_name,
            "MEMORY_TABLE": memory_table.table_name,
            "AWS_REGION": self.region,
            "SECRET_ARN": db_config_secret.secret_arn,
            "POWERTOOLS_SERVICE_NAME": "supply-chain-agent",
            "LOG_LEVEL": "INFO"
        }
        
        # Lambda Functions with best practices
        inventory_optimizer = lambda_.Function(
            self, "InventoryOptimizer",
            function_name="supply-chain-inventory-optimizer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="inventory_optimizer.lambda_handler",
            code=lambda_.Code.from_asset("../lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment=lambda_env,
            layers=[lambda_layer],
            log_retention=logs.RetentionDays.ONE_MONTH,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[lambda_sg],
            reserved_concurrent_executions=100,
            tracing=lambda_.Tracing.ACTIVE,  # X-Ray tracing
            architecture=lambda_.Architecture.ARM_64,  # Cost optimization
            description="Inventory optimization tools"
        )
        
        logistics_optimizer = lambda_.Function(
            self, "LogisticsOptimizer",
            function_name="supply-chain-logistics-optimizer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="logistics_optimizer.lambda_handler",
            code=lambda_.Code.from_asset("../lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment=lambda_env,
            layers=[lambda_layer],
            log_retention=logs.RetentionDays.ONE_MONTH,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[lambda_sg],
            reserved_concurrent_executions=100,
            tracing=lambda_.Tracing.ACTIVE,
            architecture=lambda_.Architecture.ARM_64,
            description="Logistics optimization tools"
        )
        
        supplier_analyzer = lambda_.Function(
            self, "SupplierAnalyzer",
            function_name="supply-chain-supplier-analyzer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="supplier_analyzer.lambda_handler",
            code=lambda_.Code.from_asset("../lambda_functions"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment=lambda_env,
            layers=[lambda_layer],
            log_retention=logs.RetentionDays.ONE_MONTH,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[lambda_sg],
            reserved_concurrent_executions=100,
            tracing=lambda_.Tracing.ACTIVE,
            architecture=lambda_.Architecture.ARM_64,
            description="Supplier analysis tools"
        )
        
        # CloudWatch Alarms for Lambda functions
        for func in [inventory_optimizer, logistics_optimizer, supplier_analyzer]:
            cloudwatch.Alarm(
                self, f"{func.function_name}-ErrorAlarm",
                metric=func.metric_errors(period=Duration.minutes(5)),
                threshold=5,
                evaluation_periods=2,
                alarm_description=f"Alarm when {func.function_name} has errors"
            )
            
            cloudwatch.Alarm(
                self, f"{func.function_name}-ThrottleAlarm",
                metric=func.metric_throttles(period=Duration.minutes(5)),
                threshold=10,
                evaluation_periods=2,
                alarm_description=f"Alarm when {func.function_name} is throttled"
            )
        
        # Cognito User Pool with advanced security
        user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="supply-chain-agent-users",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True, username=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(3)
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN,
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(sms=True, otp=True),
            advanced_security_mode=cognito.AdvancedSecurityMode.ENFORCED,
            device_tracking=cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True
            )
        )
        
        # User pool groups for personas
        cognito.CfnUserPoolGroup(
            self, "WarehouseManagerGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="warehouse_managers",
            description="Warehouse Manager users"
        )
        
        cognito.CfnUserPoolGroup(
            self, "FieldEngineerGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="field_engineers",
            description="Field Engineer users"
        )
        
        cognito.CfnUserPoolGroup(
            self, "ProcurementSpecialistGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="procurement_specialists",
            description="Procurement Specialist users"
        )
        
        user_pool_client = user_pool.add_client(
            "AppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            generate_secret=False,
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30)
        )
        
        # API Gateway with WAF and throttling
        api_log_group = logs.LogGroup(
            self, "APIGatewayLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        api = apigw.RestApi(
            self, "SupplyChainAPI",
            rest_api_name="supply-chain-agent-api",
            description="API for Supply Chain Agentic AI",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                access_log_destination=apigw.LogGroupLogDestination(api_log_group),
                access_log_format=apigw.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True
                ),
                metrics_enabled=True,
                tracing_enabled=True
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["https://yourdomain.com"],  # Update with actual domain
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
                max_age=Duration.hours(1)
            ),
            cloud_watch_role=True
        )
        
        # Cognito Authorizer
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "APIAuthorizer",
            cognito_user_pools=[user_pool]
        )
        
        # API Resources and Methods
        query_resource = api.root.add_resource("query")
        
        # Inventory endpoint
        inventory_resource = query_resource.add_resource("inventory")
        inventory_resource.add_method(
            "POST",
            apigw.LambdaIntegration(
                inventory_optimizer,
                proxy=False,
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_templates={"application/json": ""}
                    )
                ]
            ),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            method_responses=[apigw.MethodResponse(status_code="200")],
            request_validator=apigw.RequestValidator(
                self, "InventoryRequestValidator",
                rest_api=api,
                validate_request_body=True,
                validate_request_parameters=True
            )
        )
        
        # Logistics endpoint
        logistics_resource = query_resource.add_resource("logistics")
        logistics_resource.add_method(
            "POST",
            apigw.LambdaIntegration(logistics_optimizer),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO
        )
        
        # Supplier endpoint
        supplier_resource = query_resource.add_resource("supplier")
        supplier_resource.add_method(
            "POST",
            apigw.LambdaIntegration(supplier_analyzer),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO
        )
        
        # Health check endpoint (no auth)
        health_resource = api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigw.MockIntegration(
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"status": "healthy"}'
                        }
                    )
                ],
                request_templates={"application/json": '{"statusCode": 200}'}
            ),
            method_responses=[apigw.MethodResponse(status_code="200")]
        )
        
        # Outputs
        CfnOutput(self, "SessionTableName", value=session_table.table_name)
        CfnOutput(self, "MemoryTableName", value=memory_table.table_name)
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
        CfnOutput(self, "APIEndpoint", value=api.url)
        CfnOutput(self, "InventoryOptimizerArn", value=inventory_optimizer.function_arn)
        CfnOutput(self, "LogisticsOptimizerArn", value=logistics_optimizer.function_arn)
        CfnOutput(self, "SupplierAnalyzerArn", value=supplier_analyzer.function_arn)

class MonitoringStack(Stack):
    """Monitoring and alerting infrastructure"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        alarm_email: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # SNS Topic for alarms
        alarm_topic = sns.Topic(
            self, "AlarmTopic",
            display_name="Supply Chain Agent Alarms",
            topic_name="supply-chain-agent-alarms"
        )
        
        alarm_topic.add_subscription(
            sns_subs.EmailSubscription(alarm_email)
        )
        
        # CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "SupplyChainDashboard",
            dashboard_name="SupplyChain-Agent-Dashboard"
        )
        
        # Add widgets (will be populated with metrics from other stacks)
        dashboard.add_widgets(
            cloudwatch.TextWidget(
                markdown="# Supply Chain Agent Monitoring Dashboard",
                width=24,
                height=1
            )
        )
        
        # Composite Alarm for critical issues
        cloudwatch.CompositeAlarm(
            self, "CriticalAlarm",
            alarm_description="Critical issues detected in supply chain system",
            composite_alarm_name="supply-chain-critical-alarm",
            actions_enabled=True
        )
        
        CfnOutput(self, "AlarmTopicArn", value=alarm_topic.topic_arn)
        CfnOutput(self, "DashboardURL", 
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}"
        )

class BackupStack(Stack):
    """Backup and disaster recovery infrastructure"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Backup Vault with encryption
        backup_vault = backup.BackupVault(
            self, "BackupVault",
            backup_vault_name="supply-chain-backup-vault",
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Backup Plan
        backup_plan = backup.BackupPlan(
            self, "BackupPlan",
            backup_plan_name="supply-chain-backup-plan",
            backup_vault=backup_vault
        )
        
        # Daily backups retained for 30 days
        backup_plan.add_rule(backup.BackupPlanRule(
            rule_name="DailyBackup",
            schedule_expression=events.Schedule.cron(hour="2", minute="0"),
            delete_after=Duration.days(30),
            enable_continuous_backup=True
        ))
        
        # Weekly backups retained for 90 days
        backup_plan.add_rule(backup.BackupPlanRule(
            rule_name="WeeklyBackup",
            schedule_expression=events.Schedule.cron(
                week_day="SUN",
                hour="3",
                minute="0"
            ),
            delete_after=Duration.days(90),
            move_to_cold_storage_after=Duration.days(30)
        ))
        
        # Backup selection will be added via tags
        backup_plan.add_selection(
            "BackupSelection",
            resources=[
                backup.BackupResource.from_tag("backup", "true")
            ]
        )
        
        CfnOutput(self, "BackupVaultArn", value=backup_vault.backup_vault_arn)
        CfnOutput(self, "BackupPlanId", value=backup_plan.backup_plan_id)

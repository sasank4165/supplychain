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


def get_retention_days(days: int) -> logs.RetentionDays:
    """Convert integer days to RetentionDays enum"""
    retention_map = {
        1: logs.RetentionDays.ONE_DAY,
        3: logs.RetentionDays.THREE_DAYS,
        5: logs.RetentionDays.FIVE_DAYS,
        7: logs.RetentionDays.ONE_WEEK,
        14: logs.RetentionDays.TWO_WEEKS,
        30: logs.RetentionDays.ONE_MONTH,
        60: logs.RetentionDays.TWO_MONTHS,
        90: logs.RetentionDays.THREE_MONTHS,
        120: logs.RetentionDays.FOUR_MONTHS,
        150: logs.RetentionDays.FIVE_MONTHS,
        180: logs.RetentionDays.SIX_MONTHS,
        365: logs.RetentionDays.ONE_YEAR,
        400: logs.RetentionDays.THIRTEEN_MONTHS,
        545: logs.RetentionDays.EIGHTEEN_MONTHS,
        731: logs.RetentionDays.TWO_YEARS,
        1827: logs.RetentionDays.FIVE_YEARS,
        3653: logs.RetentionDays.TEN_YEARS,
    }
    return retention_map.get(days, logs.RetentionDays.ONE_WEEK)

class NetworkStack(Stack):
    """VPC and networking infrastructure"""
    
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # VPC with public and private subnets
        self.vpc = ec2.Vpc(
            self, "SupplyChainVPC",
            vpc_name=config.get_resource_name('vpc', 'main'),
            ip_addresses=ec2.IpAddresses.cidr(config.vpc_cidr),
            max_azs=config.max_azs,
            nat_gateways=config.nat_gateways,
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
            log_group_name=config.resource_namer.cloudwatch_log_group('vpc-flow-logs'),
            retention=get_retention_days(config.log_retention_days),
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
    
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # KMS Keys for encryption
        self.data_key = kms.Key(
            self, "DataEncryptionKey",
            description="KMS key for data encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
            pending_window=Duration.days(30)
        )
        
        self.data_key.add_alias(f"alias/{config.project_prefix}-data")
        
        # Secrets Manager for sensitive configuration
        self.db_config_secret = secretsmanager.Secret(
            self, "DatabaseConfig",
            secret_name=config.resource_namer.secrets_manager_name('database-config'),
            description="Database configuration",
            secret_object_value={
                "athena_database": secretsmanager.SecretValue.unsafe_plain_text(config.athena_database),
                "athena_catalog": secretsmanager.SecretValue.unsafe_plain_text(config.glue_catalog)
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
        config,
        kms_key: kms.Key,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # S3 Buckets with versioning and encryption
        self.data_bucket = s3.Bucket(
            self, "DataBucket",
            bucket_name=config.resource_namer.s3_bucket('data'),
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
            bucket_name=config.resource_namer.s3_bucket('athena-results'),
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
                name=config.athena_database,
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
        config,
        vpc: ec2.Vpc,
        lambda_sg: ec2.SecurityGroup,
        kms_key: kms.Key,
        data_bucket: s3.Bucket,
        athena_results_bucket: s3.Bucket,
        db_config_secret: secretsmanager.Secret,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Determine billing mode
        billing_mode = (
            dynamodb.BillingMode.PAY_PER_REQUEST 
            if config.dynamodb_billing_mode == 'PAY_PER_REQUEST' 
            else dynamodb.BillingMode.PROVISIONED
        )
        
        # Build DynamoDB table configuration
        table_config = {
            "encryption": dynamodb.TableEncryption.CUSTOMER_MANAGED,
            "encryption_key": kms_key,
            "removal_policy": RemovalPolicy.RETAIN,
            "point_in_time_recovery": config.dynamodb_pitr_enabled,
            "billing_mode": billing_mode,
        }
        
        # Add provisioned capacity if using PROVISIONED billing mode
        if billing_mode == dynamodb.BillingMode.PROVISIONED:
            table_config["read_capacity"] = config.dynamodb_read_capacity
            table_config["write_capacity"] = config.dynamodb_write_capacity
        
        # DynamoDB Tables with encryption and backups
        session_table = dynamodb.Table(
            self, "SessionTable",
            table_name=config.resource_namer.dynamodb_table('sessions'),
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="ttl",
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            **table_config
        )
        
        memory_table = dynamodb.Table(
            self, "MemoryTable",
            table_name=config.resource_namer.dynamodb_table('memory'),
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            **table_config
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
        
        # Conversation history table with TTL for context management
        conversation_table = dynamodb.Table(
            self, "ConversationTable",
            table_name=config.resource_namer.dynamodb_table('conversations'),
            partition_key=dynamodb.Attribute(
                name="message_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="ttl",
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            **table_config
        )
        
        # Add GSI for querying by session_id and timestamp
        conversation_table.add_global_secondary_index(
            index_name="session-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Add GSI for querying by persona (optional, for analytics)
        conversation_table.add_global_secondary_index(
            index_name="persona-timestamp-index",
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
        managed_policies = []
        if config.vpc_enabled:
            managed_policies.append(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                )
            )
        else:
            managed_policies.append(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            )
        
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            role_name=config.resource_namer.iam_role('lambda-exec'),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=managed_policies,
            description="Execution role for supply chain Lambda functions"
        )
        
        # Grant specific permissions
        athena_results_bucket.grant_read_write(lambda_role)
        data_bucket.grant_read(lambda_role)
        session_table.grant_read_write_data(lambda_role)
        memory_table.grant_read_write_data(lambda_role)
        conversation_table.grant_read_write_data(lambda_role)
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
            "ATHENA_DATABASE": config.athena_database,
            "SESSION_TABLE": session_table.table_name,
            "MEMORY_TABLE": memory_table.table_name,
            "CONVERSATION_TABLE": conversation_table.table_name,
            "AWS_REGION": self.region,
            "SECRET_ARN": db_config_secret.secret_arn,
            "POWERTOOLS_SERVICE_NAME": "supply-chain-agent",
            "LOG_LEVEL": "INFO"
        }
        
        # Determine Lambda architecture
        lambda_arch = (
            lambda_.Architecture.ARM_64 
            if config.lambda_architecture == 'arm64' 
            else lambda_.Architecture.X86_64
        )
        
        # Determine tracing mode
        tracing_mode = lambda_.Tracing.ACTIVE if config.xray_tracing else lambda_.Tracing.DISABLED
        
        # Common Lambda configuration
        lambda_config = {
            "runtime": lambda_.Runtime.PYTHON_3_11,
            "code": lambda_.Code.from_asset("../lambda_functions"),
            "role": lambda_role,
            "timeout": Duration.seconds(config.lambda_timeout_seconds),
            "memory_size": config.lambda_memory_mb,
            "environment": lambda_env,
            "layers": [lambda_layer],
            "log_retention": get_retention_days(config.log_retention_days),
            "reserved_concurrent_executions": config.lambda_reserved_concurrency,
            "tracing": tracing_mode,
            "architecture": lambda_arch,
        }
        
        # Add VPC configuration if enabled
        if config.vpc_enabled and vpc and lambda_sg:
            lambda_config["vpc"] = vpc
            lambda_config["vpc_subnets"] = ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            )
            lambda_config["security_groups"] = [lambda_sg]
        
        # Lambda Functions with best practices
        inventory_optimizer = lambda_.Function(
            self, "InventoryOptimizer",
            function_name=config.resource_namer.lambda_function('inventory-optimizer'),
            handler="inventory_optimizer.lambda_handler",
            description="Inventory optimization tools",
            **lambda_config
        )
        
        logistics_optimizer = lambda_.Function(
            self, "LogisticsOptimizer",
            function_name=config.resource_namer.lambda_function('logistics-optimizer'),
            handler="logistics_optimizer.lambda_handler",
            description="Logistics optimization tools",
            **lambda_config
        )
        
        supplier_analyzer = lambda_.Function(
            self, "SupplierAnalyzer",
            function_name=config.resource_namer.lambda_function('supplier-analyzer'),
            handler="supplier_analyzer.lambda_handler",
            description="Supplier analysis tools",
            **lambda_config
        )
        
        # Add provisioned concurrency if configured (typically for production)
        # This keeps Lambda instances warm to reduce cold start latency
        provisioned_concurrency = config.lambda_provisioned_concurrency
        if provisioned_concurrency > 0:
            for func in [inventory_optimizer, logistics_optimizer, supplier_analyzer]:
                # Create an alias for the current version
                version = func.current_version
                alias = lambda_.Alias(
                    self, f"{func.node.id}ProdAlias",
                    alias_name="prod",
                    version=version,
                    provisioned_concurrent_executions=provisioned_concurrency
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
            user_pool_name=config.get_resource_name('cognito', 'users'),
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
            log_group_name=config.resource_namer.cloudwatch_log_group('api-gateway'),
            retention=get_retention_days(config.log_retention_days),
            removal_policy=RemovalPolicy.RETAIN
        )
        
        api = apigw.RestApi(
            self, "SupplyChainAPI",
            rest_api_name=config.resource_namer.api_gateway('api'),
            description="API for Supply Chain Agentic AI",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=config.api_throttle_rate_limit,
                throttling_burst_limit=config.api_throttle_burst_limit,
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
                tracing_enabled=config.xray_tracing
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=config.cors_origins,
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
        CfnOutput(self, "ConversationTableName", value=conversation_table.table_name)
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
        config,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # SNS Topic for alarms
        alarm_topic = sns.Topic(
            self, "AlarmTopic",
            display_name="Supply Chain Agent Alarms",
            topic_name=config.get_resource_name('sns', 'alarms')
        )
        
        alarm_topic.add_subscription(
            sns_subs.EmailSubscription(config.alarm_email)
        )
        
        # CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "SupplyChainDashboard",
            dashboard_name=config.get_resource_name('dashboard', 'main')
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
            composite_alarm_name=config.get_resource_name('alarm', 'critical'),
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
        config,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Backup Vault with encryption
        backup_vault = backup.BackupVault(
            self, "BackupVault",
            backup_vault_name=config.get_resource_name('backup', 'vault'),
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Backup Plan
        backup_plan = backup.BackupPlan(
            self, "BackupPlan",
            backup_plan_name=config.get_resource_name('backup', 'plan'),
            backup_vault=backup_vault
        )
        
        # Daily backups retained based on configuration
        backup_plan.add_rule(backup.BackupPlanRule(
            rule_name="DailyBackup",
            schedule_expression=events.Schedule.cron(hour="2", minute="0"),
            delete_after=Duration.days(config.backup_retention_days),
            enable_continuous_backup=True
        ))
        
        # Weekly backups retained for 90 days (if retention > 30 days)
        if config.backup_retention_days >= 30:
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

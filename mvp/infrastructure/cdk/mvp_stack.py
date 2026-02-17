"""CDK Stack for Supply Chain MVP Infrastructure."""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_redshiftserverless as redshift,
    aws_glue as glue,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_ec2 as ec2,
)
from constructs import Construct


class SupplyChainMVPStack(Stack):
    """
    CDK Stack that creates:
    - Redshift Serverless workgroup (8 RPUs)
    - AWS Glue Data Catalog database
    - 3 Lambda functions for specialized agents
    - IAM roles and permissions
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC for Redshift Serverless
        vpc = ec2.Vpc(
            self,
            "SupplyChainVPC",
            max_azs=2,
            nat_gateways=0,  # Cost optimization: no NAT gateways
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # Create Glue Database for schema metadata
        glue_database = glue.CfnDatabase(
            self,
            "SupplyChainGlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="supply_chain_catalog",
                description="Schema metadata for Supply Chain MVP tables"
            )
        )

        # Create Redshift Serverless Namespace
        redshift_namespace = redshift.CfnNamespace(
            self,
            "SupplyChainNamespace",
            namespace_name="supply-chain-mvp-namespace",
            admin_username="admin",
            admin_user_password="TempPassword123!",  # Change after deployment
            db_name="supply_chain_db",
            default_iam_role_arn=None,  # Will be set after creating role
        )

        # Create IAM role for Redshift Serverless
        redshift_role = iam.Role(
            self,
            "RedshiftServerlessRole",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSGlueConsoleFullAccess")
            ]
        )

        # Create Redshift Serverless Workgroup
        redshift_workgroup = redshift.CfnWorkgroup(
            self,
            "SupplyChainWorkgroup",
            workgroup_name="supply-chain-mvp",
            namespace_name=redshift_namespace.namespace_name,
            base_capacity=8,  # 8 RPUs for cost optimization
            publicly_accessible=True,  # For MVP access
            subnet_ids=[subnet.subnet_id for subnet in vpc.public_subnets],
            security_group_ids=[],
        )
        redshift_workgroup.add_dependency(redshift_namespace)

        # Create IAM role for Lambda functions
        lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Add permissions for Lambda to access Redshift and Bedrock
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "redshift-data:ExecuteStatement",
                    "redshift-data:GetStatementResult",
                    "redshift-data:DescribeStatement",
                    "redshift-data:ListStatements"
                ],
                resources=["*"]
            )
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "glue:GetDatabase",
                    "glue:GetTable",
                    "glue:GetTables"
                ],
                resources=["*"]
            )
        )

        # Lambda Layer for common dependencies (commented out for MVP simplicity)
        # Uncomment after building layer with: cd ../lambda_functions/layer && bash build_layer.sh
        # lambda_layer = lambda_.LayerVersion(
        #     self,
        #     "SupplyChainLambdaLayer",
        #     code=lambda_.Code.from_asset("../lambda_functions/layer"),
        #     compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
        #     description="Common dependencies for Supply Chain Lambda functions"
        # )

        # Lambda Function 1: Inventory Optimizer
        inventory_lambda = lambda_.Function(
            self,
            "InventoryOptimizerFunction",
            function_name="supply-chain-inventory-optimizer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda_functions/inventory_optimizer"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "REDSHIFT_WORKGROUP": redshift_workgroup.workgroup_name,
                "REDSHIFT_DATABASE": "supply_chain_db",
                "GLUE_DATABASE": glue_database.database_input.name
            }
            # layers=[lambda_layer]  # Commented out - Lambda functions include dependencies directly
        )

        # Lambda Function 2: Logistics Optimizer
        logistics_lambda = lambda_.Function(
            self,
            "LogisticsOptimizerFunction",
            function_name="supply-chain-logistics-optimizer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda_functions/logistics_optimizer"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "REDSHIFT_WORKGROUP": redshift_workgroup.workgroup_name,
                "REDSHIFT_DATABASE": "supply_chain_db",
                "GLUE_DATABASE": glue_database.database_input.name
            }
            # layers=[lambda_layer]  # Commented out - Lambda functions include dependencies directly
        )

        # Lambda Function 3: Supplier Analyzer
        supplier_lambda = lambda_.Function(
            self,
            "SupplierAnalyzerFunction",
            function_name="supply-chain-supplier-analyzer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../../lambda_functions/supplier_analyzer"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "REDSHIFT_WORKGROUP": redshift_workgroup.workgroup_name,
                "REDSHIFT_DATABASE": "supply_chain_db",
                "GLUE_DATABASE": glue_database.database_input.name
            }
            # layers=[lambda_layer]  # Commented out - Lambda functions include dependencies directly
        )

        # Outputs
        CfnOutput(
            self,
            "RedshiftWorkgroupName",
            value=redshift_workgroup.workgroup_name,
            description="Redshift Serverless Workgroup Name"
        )

        CfnOutput(
            self,
            "RedshiftDatabase",
            value="supply_chain_db",
            description="Redshift Database Name"
        )

        CfnOutput(
            self,
            "GlueDatabaseName",
            value=glue_database.database_input.name,
            description="Glue Catalog Database Name"
        )

        CfnOutput(
            self,
            "InventoryLambdaArn",
            value=inventory_lambda.function_arn,
            description="Inventory Optimizer Lambda Function ARN"
        )

        CfnOutput(
            self,
            "LogisticsLambdaArn",
            value=logistics_lambda.function_arn,
            description="Logistics Optimizer Lambda Function ARN"
        )

        CfnOutput(
            self,
            "SupplierLambdaArn",
            value=supplier_lambda.function_arn,
            description="Supplier Analyzer Lambda Function ARN"
        )

"""Multi-region deployment stack for disaster recovery"""
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_route53 as route53,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct

class MultiRegionStack(Stack):
    """Multi-region infrastructure for high availability and disaster recovery"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        primary_region: str,
        dr_region: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Global DynamoDB table with replication
        global_table = dynamodb.Table(
            self, "GlobalSessionTable",
            table_name="supply-chain-global-sessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            replication_regions=[dr_region],
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True
        )
        
        # S3 Cross-Region Replication
        # Note: Requires separate buckets in each region
        
        # Route53 Health Checks for failover
        health_check = route53.CfnHealthCheck(
            self, "APIHealthCheck",
            health_check_config=route53.CfnHealthCheck.HealthCheckConfigProperty(
                type="HTTPS",
                resource_path="/health",
                port=443,
                request_interval=30,
                failure_threshold=3
            )
        )
        
        CfnOutput(self, "GlobalTableName", value=global_table.table_name)
        CfnOutput(self, "HealthCheckId", value=health_check.attr_health_check_id)

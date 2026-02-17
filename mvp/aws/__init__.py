"""
AWS Service Client Wrappers

This package provides simplified interfaces for AWS services used in the MVP.
"""

from .bedrock_client import BedrockClient, BedrockResponse, TokenUsage, BedrockClientError
from .redshift_client import RedshiftClient, QueryResult, RedshiftClientError
from .lambda_client import (
    LambdaClient,
    LambdaResponse,
    LambdaClientError,
    InventoryOptimizerClient,
    LogisticsOptimizerClient,
    SupplierAnalyzerClient
)
from .glue_client import (
    GlueClient,
    TableMetadata,
    ColumnMetadata,
    GlueClientError
)

__all__ = [
    'BedrockClient',
    'BedrockResponse',
    'TokenUsage',
    'BedrockClientError',
    'RedshiftClient',
    'QueryResult',
    'RedshiftClientError',
    'LambdaClient',
    'LambdaResponse',
    'LambdaClientError',
    'InventoryOptimizerClient',
    'LogisticsOptimizerClient',
    'SupplierAnalyzerClient',
    'GlueClient',
    'TableMetadata',
    'ColumnMetadata',
    'GlueClientError'
]

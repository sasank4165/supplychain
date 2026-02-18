"""
Verify Persona Registration

Quick script to verify that all personas are properly registered in the AgentRouter.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from aws.bedrock_client import BedrockClient
from aws.redshift_client import RedshiftClient
from aws.lambda_client import LambdaClient
from aws.glue_client import GlueClient
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.schema_provider import SchemaProvider
from semantic_layer.business_metrics import Persona
from agents.warehouse_sql_agent import WarehouseSQLAgent
from agents.field_sql_agent import FieldEngineerSQLAgent
from agents.procurement_sql_agent import ProcurementSQLAgent
from agents.inventory_agent import InventoryAgent
from agents.logistics_agent import LogisticsAgent
from agents.supplier_agent import SupplierAgent
from orchestrator.agent_router import AgentRouter


def verify_personas():
    """Verify that all personas are properly registered."""
    print("="*80)
    print("PERSONA REGISTRATION VERIFICATION")
    print("="*80)
    print()
    
    try:
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
        config_manager = ConfigManager(config_path)
        config = config_manager.config
        
        # Setup logger
        logger = setup_logger(
            name='persona_verification',
            log_file='logs/persona_verification.log',
            level='INFO'
        )
        
        print("✓ Configuration loaded")
        
        # Initialize AWS clients
        aws_config = config.get('aws', {})
        bedrock_config = aws_config.get('bedrock', {})
        redshift_config = aws_config.get('redshift', {})
        glue_config = aws_config.get('glue', {})
        lambda_config = aws_config.get('lambda', {})
        
        bedrock_client = BedrockClient(
            region=aws_config.get('region', 'us-east-1'),
            model_id=bedrock_config.get('model_id', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
            max_tokens=bedrock_config.get('max_tokens', 4096),
            temperature=bedrock_config.get('temperature', 0.0)
        )
        
        redshift_client = RedshiftClient(
            region=aws_config.get('region', 'us-east-1'),
            workgroup_name=redshift_config.get('workgroup_name', 'supply-chain-mvp'),
            database=redshift_config.get('database', 'supply_chain_db'),
            timeout=redshift_config.get('data_api_timeout', 30)
        )
        
        lambda_client = LambdaClient(
            region=aws_config.get('region', 'us-east-1')
        )
        
        glue_client = GlueClient(
            region=aws_config.get('region', 'us-east-1'),
            catalog_id=glue_config.get('catalog_id'),
            database=glue_config.get('database', 'supply_chain_catalog')
        )
        
        print("✓ AWS clients initialized")
        
        # Create schema provider
        schema_provider = SchemaProvider(glue_client)
        
        # Create semantic layers for each persona
        warehouse_semantic_layer = SemanticLayer(
            schema_provider=schema_provider,
            persona=Persona.WAREHOUSE_MANAGER
        )
        
        field_semantic_layer = SemanticLayer(
            schema_provider=schema_provider,
            persona=Persona.FIELD_ENGINEER
        )
        
        procurement_semantic_layer = SemanticLayer(
            schema_provider=schema_provider,
            persona=Persona.PROCUREMENT_SPECIALIST
        )
        
        print("✓ Semantic layers created")
        
        # Initialize SQL agents
        warehouse_sql_agent = WarehouseSQLAgent(
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=warehouse_semantic_layer,
            logger=logger
        )
        
        field_sql_agent = FieldEngineerSQLAgent(
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=field_semantic_layer,
            logger=logger
        )
        
        procurement_sql_agent = ProcurementSQLAgent(
            bedrock_client=bedrock_client,
            redshift_client=redshift_client,
            semantic_layer=procurement_semantic_layer,
            logger=logger
        )
        
        print("✓ SQL agents initialized")
        
        # Initialize specialized agents
        inventory_agent = InventoryAgent(
            bedrock_client=bedrock_client,
            lambda_client=lambda_client,
            lambda_function_name=lambda_config.get('inventory_function', 'inventory-optimizer'),
            logger=logger
        )
        
        logistics_agent = LogisticsAgent(
            bedrock_client=bedrock_client,
            lambda_client=lambda_client,
            lambda_function_name=lambda_config.get('logistics_function', 'logistics-optimizer'),
            logger=logger
        )
        
        supplier_agent = SupplierAgent(
            bedrock_client=bedrock_client,
            lambda_client=lambda_client,
            lambda_function_name=lambda_config.get('supplier_function', 'supplier-analyzer'),
            logger=logger
        )
        
        print("✓ Specialized agents initialized")
        
        # Create agent mappings
        sql_agents = {
            "Warehouse Manager": warehouse_sql_agent,
            "Field Engineer": field_sql_agent,
            "Procurement Specialist": procurement_sql_agent
        }
        
        specialized_agents = {
            "Warehouse Manager": inventory_agent,
            "Field Engineer": logistics_agent,
            "Procurement Specialist": supplier_agent
        }
        
        # Initialize agent router
        agent_router = AgentRouter(
            sql_agents=sql_agents,
            specialized_agents=specialized_agents,
            logger=logger
        )
        
        print("✓ Agent router initialized")
        print()
        
        # Verify personas
        print("REGISTERED PERSONAS:")
        print("-" * 80)
        
        available_personas = agent_router.get_available_personas()
        
        if not available_personas:
            print("❌ ERROR: No personas registered!")
            return False
        
        for persona in available_personas:
            is_valid = agent_router.validate_persona(persona)
            status = "✓" if is_valid else "❌"
            print(f"{status} {persona}")
        
        print()
        print(f"Total personas registered: {len(available_personas)}")
        print()
        
        # Test persona validation
        print("PERSONA VALIDATION TESTS:")
        print("-" * 80)
        
        test_personas = [
            "Warehouse Manager",
            "Field Engineer",
            "Procurement Specialist",
            "Invalid Persona"
        ]
        
        for test_persona in test_personas:
            is_valid = agent_router.validate_persona(test_persona)
            status = "✓ VALID" if is_valid else "❌ INVALID"
            print(f"{status}: {test_persona}")
        
        print()
        print("="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_personas()
    sys.exit(0 if success else 1)

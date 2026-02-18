"""
Supply Chain AI Assistant - Main Application Entry Point

This is the main Streamlit application that ties together all UI components:
- Login/Authentication
- Persona selection
- Query input and processing
- Results display
- Cost tracking
- Conversation history
"""

import streamlit as st
import sys
import os
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import authentication components
from auth.auth_manager import AuthManager
from auth.session_manager import SessionManager

# Import UI components
from ui.login_page import show_login_page, logout, is_authenticated, get_current_user, get_session_id
from ui.main_app import render_main_interface, show_example_queries, get_example_query
from ui.results_display import display_query_response
from ui.cost_dashboard import display_cost_dashboard, display_cost_summary_sidebar
from ui.conversation_sidebar import display_conversation_sidebar, get_rerun_query, show_conversation_tips

# Import orchestrator and related components
from orchestrator.query_orchestrator import QueryOrchestrator
from orchestrator.intent_classifier import IntentClassifier
from orchestrator.agent_router import AgentRouter

# Import other required components
from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from utils.error_handler import ErrorHandler
from aws.bedrock_client import BedrockClient
from aws.redshift_client import RedshiftClient
from aws.lambda_client import LambdaClient
from aws.glue_client import GlueClient
from cache.query_cache import QueryCache
from cost.cost_tracker import CostTracker
from cost.cost_logger import CostLogger


# Page configuration
st.set_page_config(
    page_title="Supply Chain AI Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_app():
    """
    Initialize application components.
    
    This function sets up all required components and stores them in session state.
    """
    # Initialize session state for components
    if 'app_initialized' not in st.session_state:
        try:
            # Load configuration
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
            if not os.path.exists(config_path):
                config_path = os.path.join(os.path.dirname(__file__), 'config.example.yaml')
            
            config_manager = ConfigManager(config_path)
            config = config_manager.config
            
            # Set up logger
            logger = setup_logger(
                name='supply_chain_ai',
                log_file=config.get('logging', {}).get('file', 'logs/app.log'),
                level=config.get('logging', {}).get('level', 'INFO')
            )
            
            # Initialize authentication components
            users_file = config.get('auth', {}).get('users_file', 'mvp/auth/users.json')
            auth_manager = AuthManager(users_file)
            
            session_timeout = config.get('app', {}).get('session_timeout', 3600)
            session_manager = SessionManager(session_timeout)
            
            # Initialize AWS clients
            aws_config = config.get('aws', {})
            bedrock_config = aws_config.get('bedrock', {})
            redshift_config = aws_config.get('redshift', {})
            glue_config = aws_config.get('glue', {})
            
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
            
            # Initialize cache
            cache_config = config.get('cache', {})
            query_cache = None
            if cache_config.get('enabled', True):
                query_cache = QueryCache(
                    max_size=cache_config.get('max_size', 1000),
                    default_ttl=cache_config.get('default_ttl', 300)
                )
            
            # Initialize cost tracking
            cost_config = config.get('cost', {})
            cost_tracker = CostTracker(cost_config)
            cost_logger = CostLogger(
                log_file_path=cost_config.get('log_file', 'logs/cost_tracking.log'),
                enabled=cost_config.get('enabled', True)
            )
            
            # Initialize semantic layers for each persona
            from semantic_layer.semantic_layer import SemanticLayer
            from semantic_layer.schema_provider import SchemaProvider
            from semantic_layer.business_metrics import Persona
            from agents.warehouse_sql_agent import WarehouseSQLAgent
            from agents.field_sql_agent import FieldEngineerSQLAgent
            from agents.procurement_sql_agent import ProcurementSQLAgent
            from agents.inventory_agent import InventoryAgent
            from agents.logistics_agent import LogisticsAgent
            from agents.supplier_agent import SupplierAgent
            
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
            
            # Initialize SQL agents for each persona
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
            
            # Initialize specialized agents
            lambda_config = aws_config.get('lambda', {})
            
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
            
            # Initialize orchestrator components
            intent_classifier = IntentClassifier(bedrock_client, logger)
            
            agent_router = AgentRouter(
                sql_agents=sql_agents,
                specialized_agents=specialized_agents,
                logger=logger
            )
            
            orchestrator = QueryOrchestrator(
                intent_classifier=intent_classifier,
                agent_router=agent_router,
                query_cache=query_cache,
                logger=logger
            )
            
            # Store components in session state
            st.session_state.config = config
            st.session_state.logger = logger
            st.session_state.auth_manager = auth_manager
            st.session_state.session_manager = session_manager
            st.session_state.bedrock_client = bedrock_client
            st.session_state.redshift_client = redshift_client
            st.session_state.lambda_client = lambda_client
            st.session_state.glue_client = glue_client
            st.session_state.orchestrator = orchestrator
            st.session_state.cost_tracker = cost_tracker
            st.session_state.cost_logger = cost_logger
            st.session_state.app_initialized = True
            
            logger.info("Application initialized successfully")
            
        except Exception as e:
            st.error(f"Failed to initialize application: {str(e)}")
            st.error("Please check your configuration and try again.")
            st.stop()


def main():
    """Main application function."""
    # Initialize app components
    initialize_app()
    
    # Get components from session state
    auth_manager = st.session_state.auth_manager
    session_manager = st.session_state.session_manager
    orchestrator = st.session_state.orchestrator
    cost_tracker = st.session_state.cost_tracker
    cost_logger = st.session_state.cost_logger
    logger = st.session_state.logger
    
    # Show login page if not authenticated
    if not is_authenticated():
        show_login_page(auth_manager, session_manager)
        return
    
    # Get current user and session
    user = get_current_user()
    session_id = get_session_id()
    
    if not user or not session_id:
        st.error("Session error. Please login again.")
        logout(session_manager)
        st.rerun()
        return
    
    # Main application layout
    st.title("🏭 Supply Chain AI Assistant")
    
    # Sidebar
    with st.sidebar:
        # User info and logout
        st.markdown(f"### Welcome, {user.username}!")
        
        if st.button("🚪 Logout", use_container_width=True):
            logger.info(f"User {user.username} logged out")
            logout(session_manager)
            st.rerun()
        
        # Display cost summary in sidebar
        display_cost_summary_sidebar(cost_tracker, session_id)
        
        # Display conversation history in sidebar
        display_conversation_sidebar(orchestrator, session_id, show_cache_stats=True)
        
        # Show conversation tips
        show_conversation_tips()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Check for re-run query from history
        rerun_query = get_rerun_query()
        example_query = get_example_query()
        
        if rerun_query:
            st.info(f"Re-running query: {rerun_query}")
            # Set the query in session state to populate the form
            st.session_state.prefill_query = rerun_query
        
        if example_query:
            st.session_state.prefill_query = example_query
        
        # Show example queries for current persona
        if 'current_persona' in st.session_state and st.session_state.current_persona:
            show_example_queries(st.session_state.current_persona)
        
        # Render main interface
        response = render_main_interface(orchestrator, user, session_id)
        
        # Display response if available
        if response:
            st.markdown("---")
            display_query_response(response)
            
            # Log cost if query was successful
            if response.agent_response.success:
                # Calculate cost (this would normally come from the response metadata)
                # For now, we'll create a placeholder cost object
                from cost.cost_tracker import Cost, TokenUsage
                
                # Extract token usage from metadata if available
                tokens = TokenUsage()
                if response.agent_response.metadata and 'token_usage' in response.agent_response.metadata:
                    token_data = response.agent_response.metadata['token_usage']
                    tokens = TokenUsage(
                        input_tokens=token_data.get('input_tokens', 0),
                        output_tokens=token_data.get('output_tokens', 0)
                    )
                
                # Calculate query cost
                query_cost = cost_tracker.calculate_query_cost(
                    bedrock_tokens=tokens,
                    redshift_execution_time=response.agent_response.execution_time,
                    lambda_duration_ms=0  # Would be extracted from metadata
                )
                
                # Add to cost tracker
                cost_tracker.add_query_cost(session_id, query_cost)
                
                # Log cost
                cost_logger.log_query_cost(
                    session_id=session_id,
                    query=response.query,
                    persona=response.persona,
                    cost=query_cost,
                    execution_time=response.total_execution_time
                )
    
    with col2:
        # Display cost dashboard
        display_cost_dashboard(cost_tracker, session_id, show_session_costs=True)
    
    # Footer
    st.markdown("---")
    st.caption("Supply Chain AI Assistant - Powered by Amazon Bedrock and AWS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.error("Please refresh the page or contact support if the problem persists.")
        
        # Log error if logger is available
        if 'logger' in st.session_state:
            st.session_state.logger.error(f"Application error: {e}", exc_info=True)

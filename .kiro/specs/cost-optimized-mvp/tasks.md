# Implementation Plan - Cost-Optimized Supply Chain MVP

This implementation plan breaks down the development into discrete, manageable coding tasks. Each task builds incrementally on previous steps, with all code integrated into the working system.

## Task List

- [x] 1. Set up project structure and infrastructure foundation





  - Create project directory structure with all required folders
  - Set up Python virtual environment and install base dependencies
  - Create CDK infrastructure stack for Redshift Serverless, Glue Catalog, and Lambda functions
  - Deploy infrastructure and verify AWS resources are created
  - _Requirements: 2, 9, 21_


- [x] 1.1 Create project directory structure

  - Create all folders: auth/, agents/, orchestrator/, semantic_layer/, tools/, cache/, memory/, cost/, database/, aws/, ui/, utils/, lambda_functions/, infrastructure/, scripts/, tests/, logs/
  - Create __init__.py files in all Python packages
  - _Requirements: 2, 9_

- [x] 1.2 Set up Python environment and dependencies


  - Create requirements.txt with all required packages (streamlit, boto3, pandas, bcrypt, pyyaml, pytest)
  - Create virtual environment and install dependencies
  - _Requirements: 21_

- [x] 1.3 Create CDK infrastructure stack


  - Write infrastructure/cdk/mvp_stack.py with Redshift Serverless (8 RPUs), Glue Database, and 3 Lambda functions
  - Configure IAM roles and permissions for all services
  - Deploy stack and capture resource ARNs
  - _Requirements: 2, 3, 9_

- [x] 2. Implement configuration management and AWS clients





  - Create configuration file structure with YAML support
  - Implement AWS service client wrappers for Bedrock, Redshift, Lambda, and Glue
  - Set up logging infrastructure
  - _Requirements: 4, 11, 12_

- [x] 2.1 Create configuration management


  - Write utils/config_manager.py to load and validate config.yaml
  - Create config.example.yaml template with all settings
  - Implement environment variable substitution
  - _Requirements: 11_

- [x] 2.2 Implement AWS service clients


  - Write aws/bedrock_client.py wrapper for Bedrock Converse API
  - Write aws/redshift_client.py for Redshift Data API
  - Write aws/lambda_client.py for Lambda invocations
  - Write aws/glue_client.py for Glue Catalog access
  - _Requirements: 2, 3, 4_

- [x] 2.3 Set up logging infrastructure


  - Write utils/logger.py with rotating file handler
  - Configure log levels and formats
  - _Requirements: 12_

- [x] 3. Create database schema and sample data generation





  - Define Glue Catalog table schemas for all 6 tables
  - Implement sample data generation script
  - Load sample data into Redshift Serverless
  - _Requirements: 2, 5, 10_

- [x] 3.1 Define Glue Catalog schemas


  - Write scripts/setup_glue_catalog.py to create database and table definitions
  - Define schemas for product, warehouse_product, sales_order_header, sales_order_line, purchase_order_header, purchase_order_line
  - Execute script to create Glue Catalog tables
  - _Requirements: 2, 5_

- [x] 3.2 Implement sample data generation


  - Write scripts/generate_sample_data.py to create realistic test data
  - Generate 100+ products, 3 warehouses, 90 days of orders
  - _Requirements: 10_

- [x] 3.3 Load data into Redshift Serverless


  - Extend generate_sample_data.py to load data via Redshift Data API
  - Verify data loaded correctly with test queries
  - _Requirements: 2, 10_

- [x] 4. Implement semantic layer with Glue Catalog integration





  - Create semantic layer to map business terms to SQL patterns
  - Integrate with Glue Catalog for schema metadata
  - Define persona-specific business metrics
  - _Requirements: 15_

- [x] 4.1 Create semantic layer foundation


  - Write semantic_layer/semantic_layer.py with business metric definitions
  - Write semantic_layer/schema_provider.py to fetch schemas from Glue Catalog
  - Write semantic_layer/business_metrics.py with metric definitions for all personas
  - _Requirements: 15_

- [x] 4.2 Define business metrics for each persona


  - Add Warehouse Manager metrics (low_stock, stockout_risk, reorder_needed)
  - Add Field Engineer metrics (overdue_orders, delivery_today, delayed_shipments)
  - Add Procurement Specialist metrics (top_suppliers, cost_variance, pending_pos)
  - _Requirements: 15_

- [x] 5. Implement Python calculation tools





  - Create calculation functions for business metrics
  - Register tools for Bedrock tool calling
  - _Requirements: 19_

- [x] 5.1 Implement calculation functions


  - Write tools/calculation_tools.py with reorder_point, safety_stock, supplier_score, demand_forecast, route_optimization functions
  - Add proper docstrings and type hints
  - _Requirements: 19_

- [x] 5.2 Create tool registry for Bedrock


  - Write tools/tool_registry.py to register tools with Bedrock-compatible definitions
  - Define tool schemas with parameters and descriptions
  - _Requirements: 19_

- [x] 6. Implement Lambda functions for specialized agents
  - Create Lambda function code for Inventory, Logistics, and Supplier agents
  - Deploy Lambda functions
  - Test Lambda invocations
  - _Requirements: 3, 7_

- [x] 6.1 Implement Inventory Optimizer Lambda
  - Write lambda_functions/inventory_optimizer/handler.py with tools: calculate_reorder_point, identify_low_stock, forecast_demand, identify_stockout_risk
  - Add Redshift query logic for inventory data
  - _Requirements: 3, 7_

- [x] 6.2 Implement Logistics Optimizer Lambda
  - Write lambda_functions/logistics_optimizer/handler.py with tools: optimize_delivery_route, check_fulfillment_status, identify_delayed_orders, calculate_warehouse_capacity
  - Add Redshift query logic for order data
  - _Requirements: 3, 7_

- [x] 6.3 Implement Supplier Analyzer Lambda
  - Write lambda_functions/supplier_analyzer/handler.py with tools: analyze_supplier_performance, compare_supplier_costs, identify_cost_savings, analyze_purchase_trends
  - Add Redshift query logic for purchase order data
  - _Requirements: 3, 7_

- [x] 6.4 Deploy Lambda functions
  - Create scripts/deploy_lambda.sh to package and deploy all Lambda functions
  - Configure Lambda environment variables and IAM roles
  - Test each Lambda function with sample invocations
  - _Requirements: 3_

- [x] 7. Implement SQL agents for each persona
  - Create base SQL agent class
  - Implement persona-specific SQL agents
  - Integrate with Bedrock for SQL generation
  - _Requirements: 3, 6_

- [x] 7.1 Create base SQL agent
  - Write agents/base_agent.py with common agent functionality
  - Write agents/sql_agent.py with SQL generation and execution logic
  - Integrate with semantic layer and Glue Catalog
  - _Requirements: 3, 6_

- [x] 7.2 Implement Warehouse Manager SQL agent
  - Write agents/warehouse_sql_agent.py with access to product, warehouse_product, sales_order tables
  - Configure persona-specific prompts and table access
  - _Requirements: 1, 3, 6_

- [x] 7.3 Implement Field Engineer SQL agent
  - Write agents/field_sql_agent.py with access to product, warehouse_product, sales_order tables
  - Configure persona-specific prompts and table access
  - _Requirements: 1, 3, 6_

- [x] 7.4 Implement Procurement Specialist SQL agent
  - Write agents/procurement_sql_agent.py with access to product, warehouse_product, purchase_order tables
  - Configure persona-specific prompts and table access
  - _Requirements: 1, 3, 6_

- [x] 8. Implement specialized agents
  - Create specialized agent classes that invoke Lambda functions
  - Integrate with Bedrock for tool calling
  - _Requirements: 3, 7_

- [x] 8.1 Implement Inventory Agent
  - Write agents/inventory_agent.py to invoke Inventory Optimizer Lambda
  - Integrate with Bedrock tool calling for inventory optimization tasks
  - _Requirements: 3, 7_

- [x] 8.2 Implement Logistics Agent
  - Write agents/logistics_agent.py to invoke Logistics Optimizer Lambda
  - Integrate with Bedrock tool calling for logistics optimization tasks
  - _Requirements: 3, 7_

- [x] 8.3 Implement Supplier Agent
  - Write agents/supplier_agent.py to invoke Supplier Analyzer Lambda
  - Integrate with Bedrock tool calling for supplier analysis tasks
  - _Requirements: 3, 7_

- [x] 9. Implement query orchestrator
  - Create intent classification logic
  - Implement agent routing based on persona and intent
  - Integrate all agents
  - _Requirements: 3_

- [x] 9.1 Create intent classifier
  - Write orchestrator/intent_classifier.py to determine query intent (SQL_QUERY, OPTIMIZATION, HYBRID)
  - Use Bedrock to classify user queries
  - _Requirements: 3_

- [x] 9.2 Implement agent router
  - Write orchestrator/agent_router.py to route queries to appropriate agents
  - Handle persona-based routing
  - _Requirements: 1, 3_

- [x] 9.3 Create main orchestrator
  - Write orchestrator/query_orchestrator.py to coordinate intent classification and agent routing
  - Integrate SQL agents and specialized agents
  - Handle hybrid queries that need both SQL and optimization
  - _Requirements: 3_

- [x] 10. Implement caching and conversation memory
  - Create query result cache with TTL
  - Implement session-level conversation memory
  - _Requirements: 16, 17_

- [x] 10.1 Implement query cache
  - Write cache/query_cache.py with LRU eviction and TTL support
  - Write cache/cache_stats.py for hit/miss tracking
  - Integrate cache with orchestrator
  - _Requirements: 16_

- [x] 10.2 Implement conversation memory
  - Write memory/conversation_memory.py to store last 10 interactions per session
  - Write memory/context.py with ConversationContext data model
  - Integrate with SQL agents for context-aware queries
  - _Requirements: 17_

- [x] 11. Implement cost tracking
  - Create cost calculation logic
  - Implement cost logging
  - _Requirements: 18_

- [x] 11.1 Implement cost tracker
  - Write cost/cost_tracker.py to calculate costs for Bedrock, Redshift, Lambda
  - Track per-query and daily costs
  - _Requirements: 18_

- [x] 11.2 Implement cost logger
  - Write cost/cost_logger.py to log cost information to file
  - Generate cost reports and breakdowns
  - _Requirements: 18_

- [x] 12. Implement authentication and authorization
  - Create authentication manager
  - Implement session management
  - Add persona-based authorization
  - _Requirements: 20_

- [x] 12.1 Create authentication manager
  - Write auth/auth_manager.py with bcrypt password hashing
  - Write auth/session_manager.py for session token management
  - Create auth/users.json structure for user storage
  - _Requirements: 20_

- [x] 12.2 Implement user management utilities
  - Write scripts/create_user.py to add new users with persona assignments
  - Add functions to update and delete users
  - _Requirements: 20_

- [x] 13. Implement error handling
  - Create error handler with categorization
  - Add user-friendly error messages
  - Implement retry logic
  - _Requirements: 12_

- [x] 13.1 Create error handler
  - Write utils/error_handler.py with error categorization and user-friendly messages
  - Implement retry logic with exponential backoff
  - Add error logging with stack traces
  - _Requirements: 12_

- [x] 14. Build Streamlit UI
  - Create login page
  - Build main application interface
  - Add results display and visualizations
  - Integrate cost dashboard and conversation history
  - _Requirements: 8, 17, 18_

- [x] 14.1 Create login page
  - Write ui/login_page.py with username/password form
  - Integrate with authentication manager
  - Handle login errors
  - _Requirements: 8, 20_

- [x] 14.2 Build main application interface
  - Write ui/main_app.py with persona selector and query input
  - Integrate with orchestrator
  - Add loading indicators
  - _Requirements: 1, 8_

- [x] 14.3 Create results display
  - Write ui/results_display.py to format and display query results
  - Add table and chart visualizations
  - Add export to CSV functionality
  - _Requirements: 8_

- [x] 14.4 Add cost dashboard
  - Write ui/cost_dashboard.py to display per-query and daily costs
  - Show cost breakdown by service
  - Display estimated monthly cost
  - _Requirements: 18_

- [x] 14.5 Create conversation sidebar
  - Write ui/conversation_sidebar.py to display conversation history
  - Make past queries clickable to re-run
  - Show cache statistics
  - _Requirements: 17_

- [x] 14.6 Create main app entry point
  - Write app.py to tie all UI components together
  - Implement session state management
  - Add logout functionality
  - _Requirements: 8, 20_

- [x] 15. Create deployment scripts and documentation
  - Write deployment scripts for SageMaker and EC2
  - Create comprehensive README
  - Document configuration options
  - _Requirements: 13, 21_

- [x] 15.1 Create SageMaker deployment scripts
  - Write infrastructure/sagemaker/setup_notebook.sh for SageMaker Notebook setup
  - Write infrastructure/sagemaker/lifecycle_config.sh for automatic startup
  - Document SageMaker deployment steps
  - _Requirements: 21_

- [x] 15.2 Create README documentation
  - Write README.md with setup instructions for all deployment options
  - Document prerequisites, installation steps, and example queries
  - Add cost structure and troubleshooting guide
  - _Requirements: 13_

- [x] 15.3 Document configuration options
  - Document all config.yaml settings
  - Provide examples for different deployment scenarios
  - Document environment variables
  - _Requirements: 11, 13_

- [x] 16. Integration testing and validation
  - Test end-to-end query flows for all personas
  - Validate cost tracking accuracy
  - Test caching and conversation memory
  - Verify error handling
  - _Requirements: All_

- [x] 16.1 Test Warehouse Manager workflows
  - Test SQL queries for inventory data
  - Test inventory optimization tools
  - Verify reorder point calculations and demand forecasting
  - _Requirements: 1, 6, 7_

- [x] 16.2 Test Field Engineer workflows
  - Test SQL queries for order and delivery data
  - Test logistics optimization tools
  - Verify route optimization and fulfillment tracking
  - _Requirements: 1, 6, 7_

- [x] 16.3 Test Procurement Specialist workflows
  - Test SQL queries for purchase order and supplier data
  - Test supplier analysis tools
  - Verify supplier performance analysis and cost comparisons
  - _Requirements: 1, 6, 7_

- [x] 16.4 Validate system features
  - Test query caching with identical queries
  - Test conversation memory with follow-up questions
  - Verify cost tracking calculations
  - Test authentication and persona authorization
  - _Requirements: 16, 17, 18, 20_

- [x] 17. Create migration documentation
  - Document differences between MVP and production architecture
  - Provide step-by-step migration guide
  - Create database migration scripts
  - _Requirements: 14_

- [x] 17.1 Document migration path
  - Write detailed migration guide from Redshift to Athena
  - Document code changes needed for production
  - Provide timeline and risk assessment
  - _Requirements: 14_
# Requirements Document - Cost-Optimized Supply Chain MVP

## Introduction

This document defines requirements for a Minimum Viable Product (MVP) version of the supply chain agentic AI system. The MVP focuses on reducing AWS infrastructure costs while maintaining comprehensive functionality for all three personas: Warehouse Manager, Field Engineer, and Procurement Specialist. The system uses Amazon Redshift Serverless with AWS Glue Data Catalog instead of AWS Athena to reduce data warehouse costs while preserving schema metadata capabilities, uses AWS Lambda for specialized agent tools, eliminates unnecessary services (API Gateway, DynamoDB), and runs the application layer locally or on a single compute instance. The MVP includes advanced features such as semantic data layer (leveraging Glue catalog metadata), query caching, conversation memory, cost tracking, and Python-based calculation tools. The goal is to validate the full system capabilities with minimal infrastructure before scaling to production.

## Glossary

- **MVP System**: The minimum viable product version of the supply chain AI application
- **Warehouse Manager**: A user persona responsible for inventory management and stock optimization
- **Field Engineer**: A user persona responsible for logistics, delivery, and order fulfillment
- **Procurement Specialist**: A user persona responsible for supplier management and purchase orders
- **SQL Agent**: An AI agent that converts natural language queries to SQL and executes them
- **Inventory Agent**: An AI agent that provides inventory optimization recommendations for Warehouse Managers
- **Logistics Agent**: An AI agent that provides delivery route optimization and order fulfillment tracking for Field Engineers
- **Supplier Agent**: An AI agent that provides supplier performance analysis and cost optimization for Procurement Specialists
- **Bedrock Service**: Amazon Bedrock AI service for agent orchestration
- **Redshift Serverless**: Amazon Redshift Serverless database for cost-effective data warehousing
- **Glue Data Catalog**: AWS Glue Data Catalog for storing database schema metadata and table definitions
- **Streamlit UI**: The web-based user interface built with Streamlit framework
- **Query Response**: The result returned by the system to a user query
- **Semantic Layer**: A business logic layer that maps business terms to database queries
- **Query Cache**: A storage mechanism for caching query results to improve performance
- **Conversation Memory**: Session-level storage of conversation history and context
- **Calculation Tool**: A Python function that performs business calculations invoked by the LLM
- **Authentication**: The process of verifying user identity through credentials
- **Authorization**: The process of granting access to specific personas based on user roles

## Requirements

### Requirement 1: Multi-Persona Support

**User Story:** As a product owner, I want to support all three personas (Warehouse Manager, Field Engineer, and Procurement Specialist) in the MVP, so that I can validate the system with different user types.

#### Acceptance Criteria

1. THE MVP System SHALL provide access to Warehouse Manager, Field Engineer, and Procurement Specialist personas
2. THE MVP System SHALL display all three personas as selectable options in the user interface
3. THE MVP System SHALL route queries to persona-appropriate agents based on user selection
4. THE MVP System SHALL maintain separate agent configurations for each persona
5. THE MVP System SHALL support persona-specific data access patterns and queries

### Requirement 2: Redshift Serverless Database with Glue Catalog

**User Story:** As a developer, I want to use Redshift Serverless with AWS Glue Data Catalog instead of AWS Athena, so that I can reduce data warehouse costs while maintaining schema metadata and semantic capabilities.

#### Acceptance Criteria

1. THE MVP System SHALL use Amazon Redshift Serverless as the database engine
2. THE MVP System SHALL configure Redshift Serverless with minimal base capacity (8 RPUs)
3. THE MVP System SHALL use AWS Glue Data Catalog to store table schemas and metadata
4. THE MVP System SHALL execute SQL queries against Redshift Serverless using the Data API
5. THE MVP System SHALL provide sample data generation scripts that create Glue catalog tables and load data into Redshift Serverless

### Requirement 3: Comprehensive Agent Architecture

**User Story:** As a developer, I want to implement SQL agents and specialized agents for all three personas, so that I can provide complete functionality for each user type.

#### Acceptance Criteria

1. THE MVP System SHALL implement six agent types: three SQL Agents (one per persona) and three specialized agents (Inventory, Logistics, Supplier)
2. THE MVP System SHALL route natural language queries to the appropriate SQL Agent based on selected persona
3. THE MVP System SHALL route optimization requests to the appropriate specialized agent based on persona
4. THE MVP System SHALL use a simplified orchestrator that routes based on persona and query intent
5. THE MVP System SHALL execute specialized agent tools using AWS Lambda functions for scalability and separation of concerns

### Requirement 4: Bedrock Integration

**User Story:** As a developer, I want to use Amazon Bedrock for AI capabilities, so that I can leverage production-quality language models without managing infrastructure.

#### Acceptance Criteria

1. THE MVP System SHALL use Amazon Bedrock Claude 3.5 Sonnet model for agent orchestration
2. THE MVP System SHALL authenticate with Bedrock using AWS credentials from the local environment
3. THE MVP System SHALL implement tool calling using Bedrock Converse API
4. THE MVP System SHALL handle Bedrock API errors gracefully with user-friendly messages
5. THE MVP System SHALL optimize prompts to minimize token usage and costs

### Requirement 5: Complete Data Tables

**User Story:** As a user, I want access to all supply chain data tables, so that I can perform comprehensive queries across inventory, orders, and procurement.

#### Acceptance Criteria

1. THE MVP System SHALL implement the product table with product master data
2. THE MVP System SHALL implement the warehouse_product table with inventory levels
3. THE MVP System SHALL implement the sales_order_header and sales_order_line tables for sales orders
4. THE MVP System SHALL implement the purchase_order_header and purchase_order_line tables for purchase orders
5. THE MVP System SHALL support relationships between all tables for complex queries

### Requirement 6: Comprehensive Query Capabilities

**User Story:** As a user, I want to query all relevant data using natural language based on my persona, so that I can quickly access information without writing SQL.

#### Acceptance Criteria

1. WHEN a user submits a natural language query, THE SQL Agent SHALL convert it to valid Redshift SQL syntax
2. WHEN the SQL is generated, THE SQL Agent SHALL execute the query against Redshift Serverless using Data API
3. WHEN query results are returned, THE MVP System SHALL format them in a readable table format
4. IF a query fails, THEN THE MVP System SHALL display a clear error message to the user
5. THE SQL Agent SHALL support persona-specific queries: inventory for Warehouse Managers, orders/delivery for Field Engineers, and purchase orders/suppliers for Procurement Specialists

### Requirement 7: Comprehensive Specialized Agent Capabilities

**User Story:** As a user, I want specialized optimization and analysis capabilities based on my persona, so that I can make informed decisions in my domain.

#### Acceptance Criteria

1. THE Inventory Agent SHALL calculate reorder points, identify low stock, forecast demand, and identify stockout risks for Warehouse Managers
2. THE Logistics Agent SHALL optimize delivery routes, track order fulfillment, identify delayed orders, and calculate warehouse capacity for Field Engineers
3. THE Supplier Agent SHALL analyze supplier performance, compare costs, identify savings opportunities, and analyze purchase trends for Procurement Specialists
4. THE specialized agents SHALL use historical data from Redshift Serverless for calculations
5. THE specialized agents SHALL present recommendations in a clear, actionable format

### Requirement 8: Streamlit User Interface

**User Story:** As a user, I want a simple web interface to interact with the system, so that I can easily select my persona, submit queries, and view results.

#### Acceptance Criteria

1. THE MVP System SHALL provide a Streamlit-based web interface accessible via web browser
2. THE Streamlit UI SHALL display a persona selector with all three persona options
3. THE Streamlit UI SHALL display a text input field for natural language queries
4. THE Streamlit UI SHALL show query results in formatted tables and charts
5. THE Streamlit UI SHALL display system status and error messages clearly

### Requirement 9: Minimal AWS Infrastructure

**User Story:** As a product owner, I want to minimize AWS service usage, so that I can reduce monthly infrastructure costs during MVP validation.

#### Acceptance Criteria

1. THE MVP System SHALL use Amazon Bedrock, Redshift Serverless, AWS Glue Data Catalog, and AWS Lambda as required AWS services
2. THE MVP System SHALL implement exactly 3 Lambda functions (one per specialized agent: Inventory, Logistics, Supplier)
3. THE MVP System SHALL use Glue Data Catalog for schema metadata without Glue ETL jobs or crawlers
4. THE MVP System SHALL eliminate API Gateway, DynamoDB, and Athena services
5. THE MVP System SHALL support deployment on local machine, EC2 instance, or Amazon SageMaker Notebook Instance
6. THE MVP System SHALL target monthly AWS costs under $200 for moderate usage (Bedrock + Redshift Serverless + Lambda + optional SageMaker Notebook)

### Requirement 10: Sample Data Generation

**User Story:** As a developer, I want automated sample data generation, so that I can quickly set up a working environment for testing and demonstration.

#### Acceptance Criteria

1. THE MVP System SHALL provide a data generation script that creates realistic sample data
2. THE data generation script SHALL populate all required tables with at least 100 products
3. THE data generation script SHALL create inventory records for at least 3 warehouses
4. THE data generation script SHALL generate sales orders and purchase orders spanning at least 90 days
5. THE data generation script SHALL load data into Redshift Serverless within 5 minutes

### Requirement 11: Configuration Management

**User Story:** As a developer, I want simple configuration management, so that I can easily adjust settings without modifying code.

#### Acceptance Criteria

1. THE MVP System SHALL use a single configuration file for all settings
2. THE configuration file SHALL include Bedrock model ID, region, Redshift cluster details, and database credentials
3. THE MVP System SHALL load configuration at startup before initializing components
4. IF configuration is missing or invalid, THEN THE MVP System SHALL display clear error messages
5. THE MVP System SHALL provide a template configuration file with sensible defaults

### Requirement 12: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error handling and logging, so that I can troubleshoot issues and monitor system behavior.

#### Acceptance Criteria

1. THE MVP System SHALL log all agent interactions to a local log file
2. THE MVP System SHALL log Bedrock API calls including token usage
3. THE MVP System SHALL log database queries and execution times
4. WHEN an error occurs, THE MVP System SHALL log the full error details with stack trace
5. THE MVP System SHALL display user-friendly error messages in the UI without exposing technical details

### Requirement 13: Documentation

**User Story:** As a new user, I want clear documentation, so that I can quickly understand how to set up and use the MVP system.

#### Acceptance Criteria

1. THE MVP System SHALL include a README file with setup instructions
2. THE README SHALL document all prerequisites including Python version and AWS credentials
3. THE README SHALL provide step-by-step installation instructions
4. THE README SHALL include example queries for common use cases
5. THE README SHALL document the cost structure and expected monthly AWS charges

### Requirement 14: Migration Path

**User Story:** As a product owner, I want a clear migration path to production, so that I can scale the MVP to full production when validated.

#### Acceptance Criteria

1. THE MVP System SHALL use the same data schema as the production system
2. THE MVP System SHALL document differences between MVP and production architecture
3. THE MVP System SHALL use modular code structure that supports swapping between Redshift Serverless and Athena
4. THE MVP System SHALL provide configuration options to switch database backends
5. THE MVP System SHALL document the steps required to migrate from Redshift Serverless to full Athena/Glue infrastructure

### Requirement 15: Semantic Data Layer

**User Story:** As a developer, I want a semantic layer that maps business terms to database queries, so that the SQL agent can better understand business context and generate accurate queries.

#### Acceptance Criteria

1. THE MVP System SHALL implement a semantic layer that defines business metrics and their SQL representations
2. THE semantic layer SHALL leverage AWS Glue Data Catalog metadata for table schemas and column definitions
3. THE semantic layer SHALL map common business terms (e.g., "low stock", "overdue orders", "top suppliers") to SQL patterns
4. THE SQL Agent SHALL use the semantic layer and Glue catalog metadata to enhance query generation with business context
5. THE semantic layer SHALL be configurable per persona with persona-specific business terms and metric definitions

### Requirement 16: Query Result Caching

**User Story:** As a user, I want fast responses for repeated queries, so that I can quickly access frequently requested information without waiting for database execution.

#### Acceptance Criteria

1. THE MVP System SHALL implement a query result cache that stores results of executed queries
2. WHEN an identical query is submitted, THE MVP System SHALL return cached results instead of re-executing the query
3. THE cache SHALL store results for common dashboard queries with configurable expiration times
4. THE cache SHALL use query text and parameters as the cache key
5. THE MVP System SHALL provide cache statistics showing hit rate and storage usage

### Requirement 17: Conversation Memory

**User Story:** As a user, I want the system to remember our conversation context, so that I can ask follow-up questions without repeating information.

#### Acceptance Criteria

1. THE MVP System SHALL maintain session-level conversation memory stored in local application state
2. THE conversation memory SHALL store the last 10 user queries and system responses per session
3. THE SQL Agent SHALL use conversation memory to understand context for follow-up queries
4. THE conversation memory SHALL be cleared when the user switches personas or starts a new session
5. THE Streamlit UI SHALL display conversation history in a sidebar for user reference

### Requirement 18: Cost Tracking and Monitoring

**User Story:** As a product owner, I want to track AWS costs per query and daily totals, so that I can monitor spending and optimize usage.

#### Acceptance Criteria

1. THE MVP System SHALL calculate and display estimated cost per query based on Bedrock token usage
2. THE MVP System SHALL maintain a daily cost counter that accumulates costs across all queries
3. THE MVP System SHALL display current daily cost and estimated monthly cost in the UI
4. THE MVP System SHALL log cost information for each query to a local file for analysis
5. THE MVP System SHALL provide cost breakdown by service (Bedrock vs Redshift Serverless)

### Requirement 19: Python Calculation Tools

**User Story:** As a developer, I want Python-based calculation tools for business metrics, so that the LLM can invoke precise calculations without relying on SQL for complex formulas.

#### Acceptance Criteria

1. THE MVP System SHALL implement Python calculation tools for reorder point, safety stock, and supplier score calculations
2. THE calculation tools SHALL be invoked by the LLM through Bedrock tool calling mechanism
3. THE calculation tools SHALL accept parameters from the LLM and return structured results
4. THE calculation tools SHALL use data retrieved from Redshift Serverless as input
5. THE MVP System SHALL provide at least 5 calculation tools: reorder_point, safety_stock, supplier_score, demand_forecast, and route_optimization

### Requirement 20: Authentication and Authorization

**User Story:** As a system administrator, I want users to authenticate with credentials and be authorized to specific personas, so that I can control access and ensure users only access appropriate functionality.

#### Acceptance Criteria

1. THE MVP System SHALL display a login window before granting access to the application
2. THE MVP System SHALL authenticate users with username and password credentials
3. THE MVP System SHALL store user credentials and persona assignments in a local configuration file
4. WHEN a user logs in, THE MVP System SHALL authorize access only to their assigned persona(s)
5. THE MVP System SHALL prevent users from accessing personas they are not authorized for
6. THE MVP System SHALL provide a logout function that clears the session and returns to the login window
7. THE MVP System SHALL support users with multiple persona assignments who can switch between authorized personas

### Requirement 21: Flexible Deployment Options

**User Story:** As a developer, I want multiple deployment options for the MVP, so that I can choose the most appropriate environment for development, testing, and production use.

#### Acceptance Criteria

1. THE MVP System SHALL support deployment on local development machines for development and testing
2. THE MVP System SHALL support deployment on Amazon SageMaker Notebook Instances for team collaboration
3. THE MVP System SHALL support deployment on EC2 instances for production use with full control
4. THE MVP System SHALL provide deployment scripts and documentation for each deployment option
5. THE MVP System SHALL use the same codebase across all deployment options with configuration-based differences
6. THE MVP System SHALL document cost implications and use cases for each deployment option
7. WHEN deployed on SageMaker, THE MVP System SHALL leverage SageMaker's IAM role for AWS service authentication

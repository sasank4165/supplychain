"""Access Control System for Supply Chain Agentic AI Application

This module provides fine-grained access control including:
- Table-level access validation
- Tool-level access validation
- Row-level security query injection
- Access control audit logging
"""
import boto3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from config import Persona, PERSONA_TABLE_ACCESS


class AccessLevel(Enum):
    """Access levels for resources"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class AccessController:
    """Fine-grained access control for agents, tables, and tools
    
    Provides:
    - Table-level access validation based on persona
    - Tool-level access validation based on persona
    - Row-level security through SQL query injection
    - Comprehensive audit logging for all access decisions
    """
    
    def __init__(self, region: str = "us-east-1", config=None):
        """Initialize access controller
        
        Args:
            region: AWS region
            config: Optional ConfigurationManager instance
        """
        self.region = region
        self.config = config
        
        # Configure logging first (before using it in _ensure_log_stream)
        self.logger = logging.getLogger(__name__)
        
        self.cloudwatch_logs = boto3.client('logs', region_name=region)
        
        # Initialize log group for audit logging
        self.log_group_name = self._get_log_group_name()
        self.log_stream_name = f"access-audit-{datetime.utcnow().strftime('%Y-%m-%d')}"
        self._ensure_log_stream()
        
        # Define persona to group mapping
        self.persona_groups = {
            "warehouse_manager": "warehouse_managers",
            "field_engineer": "field_engineers",
            "procurement_specialist": "procurement_specialists"
        }
        
        # Define tool access permissions per persona
        self.tool_permissions = {
            "warehouse_manager": [
                "execute_sql_query",
                "calculate_reorder_points",
                "forecast_demand",
                "identify_stockout_risks",
                "optimize_stock_levels"
            ],
            "field_engineer": [
                "execute_sql_query",
                "optimize_delivery_routes",
                "calculate_shipping_costs",
                "track_shipments",
                "analyze_logistics_performance"
            ],
            "procurement_specialist": [
                "execute_sql_query",
                "analyze_supplier_performance",
                "identify_cost_savings",
                "evaluate_supplier_risk",
                "recommend_suppliers"
            ]
        }
        
        # Define row-level security rules per persona
        self.row_level_security_rules = {
            "warehouse_manager": {
                "warehouse_product": "warehouse_code IN (SELECT warehouse_code FROM user_warehouses WHERE user_id = '{user_id}')",
                "sales_order_header": "warehouse_code IN (SELECT warehouse_code FROM user_warehouses WHERE user_id = '{user_id}')"
            },
            "field_engineer": {
                "sales_order_header": "warehouse_code IN (SELECT warehouse_code FROM user_territories WHERE user_id = '{user_id}')"
            },
            "procurement_specialist": {
                # Procurement specialists typically have full access to purchase data
            }
        }
    
    def _get_log_group_name(self) -> str:
        """Get CloudWatch log group name from config or use default"""
        if self.config:
            prefix = self.config.get("project.prefix", "sc-agent")
            env = self.config.get("environment.name", "dev")
            return f"/aws/{prefix}/{env}/access-control"
        return "/aws/sc-agent/access-control"
    
    def _ensure_log_stream(self):
        """Ensure CloudWatch log stream exists"""
        try:
            # Create log group if it doesn't exist
            try:
                self.cloudwatch_logs.create_log_group(logGroupName=self.log_group_name)
            except self.cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Create log stream if it doesn't exist
            try:
                self.cloudwatch_logs.create_log_stream(
                    logGroupName=self.log_group_name,
                    logStreamName=self.log_stream_name
                )
            except self.cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
                pass
        except Exception as e:
            self.logger.warning(f"Failed to create log stream: {e}")
    
    def authorize(self, user_context: Dict[str, Any], persona: str) -> bool:
        """Authorize user for persona access
        
        Args:
            user_context: User context containing groups, user_id, etc.
            persona: Requested persona
            
        Returns:
            True if authorized, False otherwise
        """
        user_groups = user_context.get('groups', [])
        user_id = user_context.get('user_id', user_context.get('username', 'unknown'))
        
        # Get required group for persona
        required_group = self._get_group_for_persona(persona)
        
        # Check authorization
        authorized = required_group in user_groups
        
        # Audit log
        self._log_access_decision(
            user_id=user_id,
            resource_type="persona",
            resource_name=persona,
            action="access",
            decision="allow" if authorized else "deny",
            reason=f"Group membership: {required_group}" if authorized else f"Missing group: {required_group}",
            user_context=user_context
        )
        
        return authorized
    
    def authorize_table_access(
        self,
        user_context: Dict[str, Any],
        table_name: str,
        action: str = "read"
    ) -> bool:
        """Authorize table access for user
        
        Args:
            user_context: User context containing persona, groups, etc.
            table_name: Name of the table
            action: Action to perform (read, write)
            
        Returns:
            True if authorized, False otherwise
        """
        persona = user_context.get('persona')
        user_id = user_context.get('user_id', user_context.get('username', 'unknown'))
        
        if not persona:
            self._log_access_decision(
                user_id=user_id,
                resource_type="table",
                resource_name=table_name,
                action=action,
                decision="deny",
                reason="No persona in user context",
                user_context=user_context
            )
            return False
        
        # Get allowed tables for persona
        try:
            persona_enum = Persona(persona)
            allowed_tables = PERSONA_TABLE_ACCESS.get(persona_enum, [])
        except ValueError:
            self._log_access_decision(
                user_id=user_id,
                resource_type="table",
                resource_name=table_name,
                action=action,
                decision="deny",
                reason=f"Invalid persona: {persona}",
                user_context=user_context
            )
            return False
        
        # Check if table is in allowed list
        authorized = table_name in allowed_tables
        
        # Audit log
        self._log_access_decision(
            user_id=user_id,
            resource_type="table",
            resource_name=table_name,
            action=action,
            decision="allow" if authorized else "deny",
            reason=f"Persona {persona} table access" if authorized else f"Table not in allowed list for {persona}",
            user_context=user_context
        )
        
        return authorized
    
    def authorize_tool_access(
        self,
        user_context: Dict[str, Any],
        tool_name: str
    ) -> bool:
        """Authorize tool execution for user
        
        Args:
            user_context: User context containing persona, groups, etc.
            tool_name: Name of the tool
            
        Returns:
            True if authorized, False otherwise
        """
        persona = user_context.get('persona')
        user_id = user_context.get('user_id', user_context.get('username', 'unknown'))
        
        if not persona:
            self._log_access_decision(
                user_id=user_id,
                resource_type="tool",
                resource_name=tool_name,
                action="execute",
                decision="deny",
                reason="No persona in user context",
                user_context=user_context
            )
            return False
        
        # Get allowed tools for persona
        allowed_tools = self.tool_permissions.get(persona, [])
        
        # Check if tool is in allowed list
        authorized = tool_name in allowed_tools
        
        # Audit log
        self._log_access_decision(
            user_id=user_id,
            resource_type="tool",
            resource_name=tool_name,
            action="execute",
            decision="allow" if authorized else "deny",
            reason=f"Persona {persona} tool access" if authorized else f"Tool not in allowed list for {persona}",
            user_context=user_context
        )
        
        return authorized
    
    def inject_row_level_security(
        self,
        user_context: Dict[str, Any],
        sql_query: str
    ) -> str:
        """Inject row-level security filters into SQL query
        
        Args:
            user_context: User context containing persona, user_id, etc.
            sql_query: Original SQL query
            
        Returns:
            Modified SQL query with row-level security filters
        """
        persona = user_context.get('persona')
        user_id = user_context.get('user_id', user_context.get('username', 'unknown'))
        
        if not persona:
            return sql_query
        
        # Get row-level security rules for persona
        rls_rules = self.row_level_security_rules.get(persona, {})
        
        if not rls_rules:
            # No row-level security rules for this persona
            return sql_query
        
        # Extract tables from query
        tables_in_query = self._extract_tables_from_sql(sql_query)
        
        # Apply row-level security filters
        modified_query = sql_query
        for table in tables_in_query:
            if table in rls_rules:
                # Get the RLS filter for this table
                rls_filter = rls_rules[table].format(user_id=user_id)
                
                # Inject the filter into the WHERE clause
                modified_query = self._inject_where_clause(modified_query, table, rls_filter)
                
                # Log the injection
                self.logger.info(f"Injected RLS filter for table {table}: {rls_filter}")
        
        # Audit log if query was modified
        if modified_query != sql_query:
            self._log_access_decision(
                user_id=user_id,
                resource_type="query",
                resource_name="sql_query",
                action="row_level_security",
                decision="applied",
                reason=f"RLS filters applied for persona {persona}",
                user_context=user_context,
                metadata={"original_query": sql_query[:100], "modified": True}
            )
        
        return modified_query
    
    def get_accessible_tables(self, persona: str) -> List[str]:
        """Get list of tables accessible to persona
        
        Args:
            persona: Persona name
            
        Returns:
            List of accessible table names
        """
        try:
            persona_enum = Persona(persona)
            return PERSONA_TABLE_ACCESS.get(persona_enum, [])
        except ValueError:
            return []
    
    def get_accessible_tools(self, persona: str) -> List[str]:
        """Get list of tools accessible to persona
        
        Args:
            persona: Persona name
            
        Returns:
            List of accessible tool names
        """
        return self.tool_permissions.get(persona, [])
    
    def validate_bulk_table_access(
        self,
        user_context: Dict[str, Any],
        table_names: List[str],
        action: str = "read"
    ) -> Dict[str, bool]:
        """Validate access to multiple tables at once
        
        Args:
            user_context: User context
            table_names: List of table names
            action: Action to perform
            
        Returns:
            Dictionary mapping table names to authorization status
        """
        results = {}
        for table_name in table_names:
            results[table_name] = self.authorize_table_access(
                user_context, table_name, action
            )
        return results
    
    def validate_bulk_tool_access(
        self,
        user_context: Dict[str, Any],
        tool_names: List[str]
    ) -> Dict[str, bool]:
        """Validate access to multiple tools at once
        
        Args:
            user_context: User context
            tool_names: List of tool names
            
        Returns:
            Dictionary mapping tool names to authorization status
        """
        results = {}
        for tool_name in tool_names:
            results[tool_name] = self.authorize_tool_access(
                user_context, tool_name
            )
        return results
    
    def _get_group_for_persona(self, persona: str) -> str:
        """Get Cognito group name for persona
        
        Args:
            persona: Persona name
            
        Returns:
            Group name
        """
        return self.persona_groups.get(persona, "")
    
    def _extract_tables_from_sql(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query
        
        Args:
            sql_query: SQL query string
            
        Returns:
            List of table names
        """
        import re
        
        # Simple regex to extract table names (after FROM and JOIN)
        # Format: database.table or just table
        pattern = r'(?:FROM|JOIN)\s+(?:`?[\w-]+`?\.)?`?([\w_]+)`?'
        matches = re.findall(pattern, sql_query, re.IGNORECASE)
        
        # Remove duplicates
        tables = list(set(matches))
        return tables
    
    def _inject_where_clause(self, sql_query: str, table_name: str, filter_clause: str) -> str:
        """Inject WHERE clause into SQL query for row-level security
        
        Args:
            sql_query: Original SQL query
            table_name: Table to apply filter to
            filter_clause: Filter condition to inject
            
        Returns:
            Modified SQL query
        """
        import re
        
        # This is a simplified implementation
        # In production, use a proper SQL parser
        
        # Check if query already has a WHERE clause
        if re.search(r'\bWHERE\b', sql_query, re.IGNORECASE):
            # Add to existing WHERE clause with AND
            # Find the WHERE clause and inject after it
            modified = re.sub(
                r'(\bWHERE\b)',
                f'\\1 ({filter_clause}) AND',
                sql_query,
                count=1,
                flags=re.IGNORECASE
            )
        else:
            # Add new WHERE clause
            # Find the FROM clause with the table and add WHERE after it
            # This is simplified - in production use proper SQL parsing
            modified = re.sub(
                rf'(\bFROM\b\s+(?:\w+\.)?{table_name}\b)',
                f'\\1 WHERE ({filter_clause})',
                sql_query,
                count=1,
                flags=re.IGNORECASE
            )
        
        return modified
    
    def _log_access_decision(
        self,
        user_id: str,
        resource_type: str,
        resource_name: str,
        action: str,
        decision: str,
        reason: str,
        user_context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log access control decision to CloudWatch Logs
        
        Args:
            user_id: User identifier
            resource_type: Type of resource (table, tool, persona, query)
            resource_name: Name of the resource
            action: Action attempted
            decision: Decision made (allow, deny, applied)
            reason: Reason for decision
            user_context: Full user context
            metadata: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_name": resource_name,
            "action": action,
            "decision": decision,
            "reason": reason,
            "persona": user_context.get('persona'),
            "groups": user_context.get('groups', []),
            "session_id": user_context.get('session_id'),
            "metadata": metadata or {}
        }
        
        # Log to application logger
        log_message = (
            f"Access {decision}: user={user_id}, "
            f"resource={resource_type}/{resource_name}, "
            f"action={action}, reason={reason}"
        )
        
        if decision == "deny":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log to CloudWatch for audit trail
        try:
            self.cloudwatch_logs.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'message': json.dumps(log_entry)
                    }
                ]
            )
        except Exception as e:
            self.logger.error(f"Failed to write audit log to CloudWatch: {e}")
    
    def get_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with optional filters
        
        Args:
            start_time: Start time for log retrieval
            end_time: End time for log retrieval
            user_id: Filter by user ID
            resource_type: Filter by resource type
            decision: Filter by decision (allow, deny)
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of audit log entries
        """
        try:
            # Build filter pattern
            filter_patterns = []
            if user_id:
                filter_patterns.append(f'{{ $.user_id = "{user_id}" }}')
            if resource_type:
                filter_patterns.append(f'{{ $.resource_type = "{resource_type}" }}')
            if decision:
                filter_patterns.append(f'{{ $.decision = "{decision}" }}')
            
            filter_pattern = ' && '.join(filter_patterns) if filter_patterns else ''
            
            # Query CloudWatch Logs
            kwargs = {
                'logGroupName': self.log_group_name,
                'limit': limit
            }
            
            if filter_pattern:
                kwargs['filterPattern'] = filter_pattern
            
            if start_time:
                kwargs['startTime'] = int(start_time.timestamp() * 1000)
            
            if end_time:
                kwargs['endTime'] = int(end_time.timestamp() * 1000)
            
            response = self.cloudwatch_logs.filter_log_events(**kwargs)
            
            # Parse log entries
            logs = []
            for event in response.get('events', []):
                try:
                    log_entry = json.loads(event['message'])
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve audit logs: {e}")
            return []

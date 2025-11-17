"""Agent Registry and Plugin Architecture for Supply Chain Agentic AI Application

This module provides a plugin-based architecture for agent discovery, registration,
and management. It enables dynamic agent loading from configuration without hardcoding
agent instances in the orchestrator.
"""

import importlib
import inspect
from typing import Dict, List, Any, Optional, Type
from pathlib import Path

from agents.base_agent import BaseAgent
from config_manager import ConfigurationManager


class AgentRegistryError(Exception):
    """Raised when agent registration or discovery fails"""
    pass


class AgentRegistry:
    """Registry for pluggable agents
    
    Provides automatic agent discovery from configuration, registration,
    and retrieval. Supports dynamic agent loading without hardcoding.
    
    Example:
        >>> config = ConfigurationManager('dev')
        >>> registry = AgentRegistry(config)
        >>> sql_agent = registry.get_agent('sql_agent')
        >>> all_agents = registry.list_agents()
    """
    
    def __init__(self, config: ConfigurationManager, auto_discover: bool = True, model_manager=None):
        """Initialize agent registry
        
        Args:
            config: ConfigurationManager instance
            auto_discover: Whether to automatically discover and register agents from config
            model_manager: Optional ModelManager instance to pass to agents
        """
        self.config = config
        self.model_manager = model_manager
        self.agents: Dict[str, BaseAgent] = {}
        self._agent_configs: Dict[str, Dict[str, Any]] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        
        # Discover available agent classes
        self._discover_agent_classes()
        
        # Auto-discover and register agents from configuration
        if auto_discover:
            self._discover_agents_from_config()
    
    def _discover_agent_classes(self):
        """Discover available agent classes from agents module
        
        Scans the agents module for classes that inherit from BaseAgent
        and registers them for later instantiation.
        """
        try:
            # Import agents module
            import agents
            
            # Get all classes from agents module
            for name, obj in inspect.getmembers(agents, inspect.isclass):
                # Check if it's a BaseAgent subclass (but not BaseAgent itself)
                if issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    # Map class name to class for instantiation
                    class_name = obj.__name__
                    self._agent_classes[class_name] = obj
                    
                    # Also map common name patterns
                    # e.g., SQLAgent -> sql_agent, InventoryOptimizerAgent -> inventory_optimizer
                    snake_case_name = self._camel_to_snake(class_name)
                    if snake_case_name.endswith('_agent'):
                        snake_case_name = snake_case_name[:-6]  # Remove '_agent' suffix
                    self._agent_classes[snake_case_name] = obj
            
            print(f"Discovered {len(set(self._agent_classes.values()))} agent classes")
            
        except Exception as e:
            raise AgentRegistryError(f"Failed to discover agent classes: {str(e)}")
    
    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case
        
        Args:
            name: CamelCase string
            
        Returns:
            snake_case string
        """
        import re
        # Insert underscore before uppercase letters and convert to lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _discover_agents_from_config(self):
        """Auto-discover and register agents from configuration
        
        Reads the 'agents' section from configuration and registers
        all enabled agents with their specific configurations.
        """
        agents_config = self.config.get('agents', {})
        
        if not agents_config:
            print("Warning: No agents configuration found")
            return
        
        # Track which agents were registered
        registered_count = 0
        
        for agent_name, agent_config in agents_config.items():
            # Skip non-dict entries (like default_model, context_window_size, etc.)
            if not isinstance(agent_config, dict):
                continue
            
            # Check if agent is enabled
            if not agent_config.get('enabled', True):
                print(f"Skipping disabled agent: {agent_name}")
                continue
            
            try:
                self.register_agent(agent_name, agent_config)
                registered_count += 1
            except Exception as e:
                print(f"Warning: Failed to register agent '{agent_name}': {str(e)}")
        
        print(f"Successfully registered {registered_count} agents from configuration")
    
    def register_agent(self, name: str, agent_config: Dict[str, Any]) -> BaseAgent:
        """Register an agent with the registry
        
        Args:
            name: Agent name (e.g., 'sql_agent', 'inventory_optimizer')
            agent_config: Agent-specific configuration dictionary
            
        Returns:
            Registered agent instance
            
        Raises:
            AgentRegistryError: If agent class not found or instantiation fails
            
        Example:
            >>> registry.register_agent('sql_agent', {
            ...     'enabled': True,
            ...     'model': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            ...     'timeout_seconds': 60
            ... })
        """
        # Check if already registered
        if name in self.agents:
            print(f"Warning: Agent '{name}' already registered, skipping")
            return self.agents[name]
        
        # Find the agent class
        agent_class = self._find_agent_class(name)
        if not agent_class:
            raise AgentRegistryError(
                f"Agent class not found for '{name}'. "
                f"Available agents: {list(set(self._agent_classes.keys()))}"
            )
        
        # Instantiate the agent with configuration
        try:
            agent = self._instantiate_agent(agent_class, name, agent_config)
            self.agents[name] = agent
            self._agent_configs[name] = agent_config
            print(f"Registered agent: {name} ({agent_class.__name__})")
            return agent
            
        except Exception as e:
            raise AgentRegistryError(f"Failed to instantiate agent '{name}': {str(e)}")
    
    def _find_agent_class(self, name: str) -> Optional[Type[BaseAgent]]:
        """Find agent class by name
        
        Args:
            name: Agent name (supports multiple formats)
            
        Returns:
            Agent class or None if not found
        """
        # Try direct lookup
        if name in self._agent_classes:
            return self._agent_classes[name]
        
        # Try with _agent suffix
        if f"{name}_agent" in self._agent_classes:
            return self._agent_classes[f"{name}_agent"]
        
        # Try CamelCase conversion
        camel_case = self._snake_to_camel(name)
        if camel_case in self._agent_classes:
            return self._agent_classes[camel_case]
        
        # Try CamelCase with Agent suffix
        if f"{camel_case}Agent" in self._agent_classes:
            return self._agent_classes[f"{camel_case}Agent"]
        
        return None
    
    def _snake_to_camel(self, name: str) -> str:
        """Convert snake_case to CamelCase
        
        Args:
            name: snake_case string
            
        Returns:
            CamelCase string
        """
        components = name.split('_')
        return ''.join(x.title() for x in components)
    
    def _instantiate_agent(
        self, 
        agent_class: Type[BaseAgent], 
        name: str, 
        agent_config: Dict[str, Any]
    ) -> BaseAgent:
        """Instantiate an agent with configuration
        
        Args:
            agent_class: Agent class to instantiate
            name: Agent name
            agent_config: Agent configuration
            
        Returns:
            Agent instance
        """
        # Get region from global config
        region = self.config.get('environment.region', 'us-east-1')
        
        # Inspect the agent class constructor to determine required parameters
        sig = inspect.signature(agent_class.__init__)
        params = list(sig.parameters.keys())[1:]  # Skip 'self'
        
        # Build constructor arguments based on agent class signature
        kwargs = {'region': region}
        
        # Handle different agent constructor patterns
        if 'persona' in params:
            # SQL Agent requires persona
            # For SQL agent, we'll need to handle persona dynamically
            # For now, we'll create a generic instance
            kwargs['persona'] = agent_config.get('persona', 'generic')
        
        if 'agent_name' in params:
            kwargs['agent_name'] = name
        
        # Add agent_config to kwargs for agents that support it
        if 'config' in params:
            kwargs['config'] = agent_config
        
        # Add model_manager if agent supports it
        if 'model_manager' in params and self.model_manager:
            kwargs['model_manager'] = self.model_manager
        
        # Instantiate the agent
        agent = agent_class(**kwargs)
        
        # Store configuration in agent for runtime access
        if hasattr(agent, 'agent_config'):
            agent.agent_config = agent_config
        else:
            # Add config as attribute if not present
            agent.agent_config = agent_config
        
        # Store model_manager reference if not already set
        if self.model_manager and not hasattr(agent, 'model_manager'):
            agent.model_manager = self.model_manager
        
        return agent
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get registered agent by name
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None if not found
            
        Example:
            >>> agent = registry.get_agent('sql_agent')
        """
        return self.agents.get(name)
    
    def get_agent_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a registered agent
        
        Args:
            name: Agent name
            
        Returns:
            Agent configuration dictionary or None if not found
        """
        return self._agent_configs.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names
        
        Returns:
            List of agent names
            
        Example:
            >>> registry.list_agents()
            ['sql_agent', 'inventory_optimizer', 'logistics_agent', 'supplier_analyzer']
        """
        return list(self.agents.keys())
    
    def list_available_agent_classes(self) -> List[str]:
        """List all available agent classes that can be registered
        
        Returns:
            List of available agent class names
        """
        # Return unique class names
        return list(set(cls.__name__ for cls in self._agent_classes.values()))
    
    def get_agents_by_persona(self, persona: str) -> List[BaseAgent]:
        """Get all agents suitable for a specific persona
        
        Args:
            persona: Persona name (e.g., 'warehouse_manager', 'field_engineer')
            
        Returns:
            List of agents for the persona
        """
        matching_agents = []
        
        for agent_name, agent in self.agents.items():
            # Check if agent has persona attribute
            if hasattr(agent, 'persona'):
                if agent.persona == persona or agent.persona == 'generic':
                    matching_agents.append(agent)
            else:
                # If no persona specified, include all agents
                matching_agents.append(agent)
        
        return matching_agents
    
    def unregister_agent(self, name: str) -> bool:
        """Unregister an agent from the registry
        
        Args:
            name: Agent name
            
        Returns:
            True if agent was unregistered, False if not found
        """
        if name in self.agents:
            del self.agents[name]
            if name in self._agent_configs:
                del self._agent_configs[name]
            print(f"Unregistered agent: {name}")
            return True
        return False
    
    def reload_agent(self, name: str) -> Optional[BaseAgent]:
        """Reload an agent with its current configuration
        
        Args:
            name: Agent name
            
        Returns:
            Reloaded agent instance or None if not found
        """
        if name not in self._agent_configs:
            return None
        
        # Unregister and re-register
        self.unregister_agent(name)
        return self.register_agent(name, self._agent_configs[name])
    
    def get_agent_capabilities(self, name: str) -> Dict[str, Any]:
        """Get capabilities of a registered agent
        
        Args:
            name: Agent name
            
        Returns:
            Dictionary describing agent capabilities
        """
        agent = self.get_agent(name)
        if not agent:
            return {"error": f"Agent '{name}' not found"}
        
        capabilities = {
            "name": name,
            "class": agent.__class__.__name__,
            "persona": getattr(agent, 'persona', 'generic'),
            "enabled": True
        }
        
        # Get tools if available
        if hasattr(agent, 'get_tools'):
            try:
                tools = agent.get_tools()
                capabilities["tools"] = [
                    tool.get("toolSpec", {}).get("name", "unknown")
                    for tool in tools
                ]
                capabilities["tool_count"] = len(tools)
            except Exception as e:
                capabilities["tools_error"] = str(e)
        
        # Get configuration
        config = self.get_agent_config(name)
        if config:
            capabilities["model"] = config.get("model", "default")
            capabilities["timeout_seconds"] = config.get("timeout_seconds")
        
        return capabilities
    
    def get_all_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of all registered agents
        
        Returns:
            Dictionary mapping agent names to their capabilities
        """
        return {
            name: self.get_agent_capabilities(name)
            for name in self.list_agents()
        }
    
    def __repr__(self) -> str:
        return f"AgentRegistry(agents={len(self.agents)}, available_classes={len(set(self._agent_classes.values()))})"
    
    def __len__(self) -> int:
        """Return number of registered agents"""
        return len(self.agents)

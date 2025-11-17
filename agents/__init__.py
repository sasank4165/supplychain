"""Agent modules for supply chain application

This module provides a plugin-based agent architecture with:
- BaseAgent: Abstract base class for all agents with configuration support
- SQLAgent: Natural language to SQL conversion and execution
- InventoryOptimizerAgent: Inventory forecasting and optimization
- SupplierAnalyzerAgent: Supplier performance analysis
- LogisticsAgent: Logistics and delivery optimization

All agents support configuration-driven initialization for dynamic loading
through the AgentRegistry.
"""
from .base_agent import BaseAgent
from .sql_agent import SQLAgent
from .inventory_optimizer_agent import InventoryOptimizerAgent
from .supplier_analyzer_agent import SupplierAnalyzerAgent
from .logistics_agent import LogisticsAgent

__all__ = [
    'BaseAgent',
    'SQLAgent',
    'InventoryOptimizerAgent',
    'SupplierAnalyzerAgent',
    'LogisticsAgent'
]

"""
Tests for Calculation Tools and Tool Registry

Run with: python -m pytest mvp/tools/test_tools.py -v
"""

import pytest
from .calculation_tools import CalculationTools, Order, Location
from .tool_registry import get_tool_registry, get_bedrock_tool_config


class TestCalculationTools:
    """Tests for CalculationTools class"""
    
    def test_calculate_reorder_point(self):
        """Test reorder point calculation"""
        result = CalculationTools.calculate_reorder_point(
            avg_daily_demand=10.0,
            lead_time_days=7,
            safety_stock=20.0
        )
        assert result == 90.0
    
    def test_calculate_reorder_point_negative_values(self):
        """Test reorder point with negative values raises error"""
        with pytest.raises(ValueError):
            CalculationTools.calculate_reorder_point(-10.0, 7, 20.0)
    
    def test_calculate_safety_stock(self):
        """Test safety stock calculation"""
        result = CalculationTools.calculate_safety_stock(
            max_daily_demand=15.0,
            avg_daily_demand=10.0,
            max_lead_time=10,
            avg_lead_time=7
        )
        assert result == 80.0
    
    def test_calculate_safety_stock_invalid_max(self):
        """Test safety stock with invalid max values"""
        with pytest.raises(ValueError):
            CalculationTools.calculate_safety_stock(
                max_daily_demand=5.0,  # Less than avg
                avg_daily_demand=10.0,
                max_lead_time=10,
                avg_lead_time=7
            )
    
    def test_calculate_supplier_score(self):
        """Test supplier score calculation"""
        result = CalculationTools.calculate_supplier_score(
            fill_rate=0.95,
            on_time_rate=0.90,
            quality_rate=0.98,
            cost_competitiveness=0.85
        )
        # 0.95*0.3 + 0.90*0.3 + 0.98*0.2 + 0.85*0.2 = 0.921
        assert result == 0.921
    
    def test_calculate_supplier_score_out_of_range(self):
        """Test supplier score with out of range values"""
        with pytest.raises(ValueError):
            CalculationTools.calculate_supplier_score(1.5, 0.9, 0.98, 0.85)
    
    def test_forecast_demand_moving_average(self):
        """Test demand forecasting with moving average"""
        historical = [10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0]
        result = CalculationTools.forecast_demand(
            historical_demand=historical,
            periods=3,
            method="moving_average",
            window_size=7
        )
        assert len(result) == 3
        assert all(isinstance(x, float) for x in result)
    
    def test_forecast_demand_weighted_moving_average(self):
        """Test demand forecasting with weighted moving average"""
        historical = [10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0]
        result = CalculationTools.forecast_demand(
            historical_demand=historical,
            periods=2,
            method="weighted_moving_average",
            window_size=5
        )
        assert len(result) == 2
    
    def test_forecast_demand_exponential_smoothing(self):
        """Test demand forecasting with exponential smoothing"""
        historical = [10.0, 12.0, 11.0, 13.0, 12.0]
        result = CalculationTools.forecast_demand(
            historical_demand=historical,
            periods=3,
            method="exponential_smoothing"
        )
        assert len(result) == 3
    
    def test_forecast_demand_invalid_method(self):
        """Test forecast with invalid method"""
        with pytest.raises(ValueError):
            CalculationTools.forecast_demand([10, 12, 11], 3, method="invalid")
    
    def test_optimize_route(self):
        """Test route optimization"""
        warehouse = Location(40.7128, -74.0060, "Warehouse A")
        orders = [
            Order("SO-001", "123 Main St", "Downtown", 40.7589, -73.9851, 1),
            Order("SO-002", "456 Oak Ave", "Downtown", 40.7614, -73.9776, 3),
            Order("SO-003", "789 Pine Rd", "Uptown", 40.7829, -73.9654, 1)
        ]
        
        result = CalculationTools.optimize_route(orders, warehouse)
        
        assert len(result.optimized_order) == 3
        assert result.total_distance_km > 0
        assert result.estimated_time_hours > 0
        assert "Downtown" in result.delivery_groups
        # Urgent order (priority 3) should come before normal order in same area
        downtown_orders = result.delivery_groups["Downtown"]
        assert downtown_orders[0] == "SO-002"  # Priority 3
    
    def test_optimize_route_empty_orders(self):
        """Test route optimization with no orders"""
        warehouse = Location(40.7128, -74.0060, "Warehouse A")
        result = CalculationTools.optimize_route([], warehouse)
        
        assert result.optimized_order == []
        assert result.total_distance_km == 0.0
        assert result.estimated_time_hours == 0.0
    
    def test_calculate_economic_order_quantity(self):
        """Test EOQ calculation"""
        result = CalculationTools.calculate_economic_order_quantity(
            annual_demand=1000,
            ordering_cost=50,
            holding_cost_per_unit=2
        )
        # sqrt((2 * 1000 * 50) / 2) = sqrt(50000) ≈ 223.61
        assert result == 223.61
    
    def test_calculate_inventory_turnover(self):
        """Test inventory turnover calculation"""
        result = CalculationTools.calculate_inventory_turnover(
            cost_of_goods_sold=500000,
            average_inventory=50000
        )
        assert result == 10.0
    
    def test_calculate_days_of_supply(self):
        """Test days of supply calculation"""
        result = CalculationTools.calculate_days_of_supply(
            current_inventory=100,
            avg_daily_demand=10
        )
        assert result == 10.0


class TestToolRegistry:
    """Tests for ToolRegistry class"""
    
    def test_get_tool_registry_singleton(self):
        """Test that get_tool_registry returns singleton"""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is registry2
    
    def test_get_tool_definitions(self):
        """Test getting tool definitions"""
        registry = get_tool_registry()
        definitions = registry.get_tool_definitions()
        
        assert isinstance(definitions, list)
        assert len(definitions) > 0
        
        # Check structure of first definition
        first_def = definitions[0]
        assert "toolSpec" in first_def
        assert "name" in first_def["toolSpec"]
        assert "description" in first_def["toolSpec"]
        assert "inputSchema" in first_def["toolSpec"]
    
    def test_get_tool_names(self):
        """Test getting tool names"""
        registry = get_tool_registry()
        names = registry.get_tool_names()
        
        assert "calculate_reorder_point" in names
        assert "calculate_safety_stock" in names
        assert "calculate_supplier_score" in names
        assert "forecast_demand" in names
        assert "optimize_route" in names
    
    def test_invoke_tool_reorder_point(self):
        """Test invoking reorder point tool"""
        registry = get_tool_registry()
        result = registry.invoke_tool(
            "calculate_reorder_point",
            {
                "avg_daily_demand": 10.0,
                "lead_time_days": 7,
                "safety_stock": 20.0
            }
        )
        assert result == 90.0
    
    def test_invoke_tool_invalid_name(self):
        """Test invoking non-existent tool"""
        registry = get_tool_registry()
        with pytest.raises(ValueError, match="Unknown tool"):
            registry.invoke_tool("invalid_tool", {})
    
    def test_invoke_tool_invalid_parameters(self):
        """Test invoking tool with invalid parameters"""
        registry = get_tool_registry()
        with pytest.raises(ValueError):
            registry.invoke_tool("calculate_reorder_point", {"wrong_param": 10})
    
    def test_format_tool_result_number(self):
        """Test formatting numeric result"""
        registry = get_tool_registry()
        result = registry.format_tool_result("calculate_reorder_point", 90.0)
        assert result == "90.0"
    
    def test_format_tool_result_list(self):
        """Test formatting list result"""
        registry = get_tool_registry()
        result = registry.format_tool_result("forecast_demand", [10.5, 11.2, 10.8])
        assert "10.5" in result
        assert "11.2" in result
    
    def test_get_bedrock_tool_config(self):
        """Test getting Bedrock tool config"""
        config = get_bedrock_tool_config()
        
        assert "tools" in config
        assert isinstance(config["tools"], list)
        assert len(config["tools"]) > 0
    
    def test_get_tool_description(self):
        """Test getting tool description"""
        registry = get_tool_registry()
        description = registry.get_tool_description("calculate_reorder_point")
        
        assert description is not None
        assert "reorder point" in description.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

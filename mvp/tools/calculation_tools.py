"""
Calculation Tools for Supply Chain Business Metrics

This module provides Python calculation functions for business metrics that can be
invoked by the LLM through Bedrock tool calling. These tools perform precise
calculations for inventory management, logistics optimization, and supplier analysis.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics


@dataclass
class Location:
    """Represents a geographic location"""
    latitude: float
    longitude: float
    address: str


@dataclass
class Order:
    """Represents a sales order for route optimization"""
    order_id: str
    delivery_address: str
    delivery_area: str
    latitude: float
    longitude: float
    priority: int = 1  # 1=normal, 2=high, 3=urgent


@dataclass
class RouteOptimization:
    """Result of route optimization"""
    optimized_order: List[str]  # Order IDs in delivery sequence
    total_distance_km: float
    estimated_time_hours: float
    delivery_groups: Dict[str, List[str]]  # Area -> Order IDs


class CalculationTools:
    """
    Collection of calculation functions for supply chain business metrics.
    
    These tools are designed to be invoked by the LLM through Bedrock tool calling
    and provide precise calculations for inventory optimization, logistics planning,
    and supplier analysis.
    """
    
    @staticmethod
    def calculate_reorder_point(
        avg_daily_demand: float,
        lead_time_days: int,
        safety_stock: float
    ) -> float:
        """
        Calculate the optimal reorder point for a product.
        
        The reorder point is the inventory level at which a new order should be placed
        to avoid stockouts while accounting for lead time and safety stock.
        
        Formula: Reorder Point = (Average Daily Demand × Lead Time) + Safety Stock
        
        Args:
            avg_daily_demand: Average daily demand for the product (units/day)
            lead_time_days: Lead time from order to delivery (days)
            safety_stock: Safety stock quantity to buffer against variability (units)
        
        Returns:
            float: The reorder point in units
        
        Example:
            >>> calculate_reorder_point(10.0, 7, 20.0)
            90.0
        """
        if avg_daily_demand < 0 or lead_time_days < 0 or safety_stock < 0:
            raise ValueError("All parameters must be non-negative")
        
        reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
        return round(reorder_point, 2)
    
    @staticmethod
    def calculate_safety_stock(
        max_daily_demand: float,
        avg_daily_demand: float,
        max_lead_time: int,
        avg_lead_time: int
    ) -> float:
        """
        Calculate the safety stock quantity to buffer against demand and lead time variability.
        
        Safety stock protects against stockouts caused by demand spikes or delivery delays.
        
        Formula: Safety Stock = (Max Daily Demand × Max Lead Time) - (Avg Daily Demand × Avg Lead Time)
        
        Args:
            max_daily_demand: Maximum observed daily demand (units/day)
            avg_daily_demand: Average daily demand (units/day)
            max_lead_time: Maximum observed lead time (days)
            avg_lead_time: Average lead time (days)
        
        Returns:
            float: The safety stock quantity in units
        
        Example:
            >>> calculate_safety_stock(15.0, 10.0, 10, 7)
            80.0
        """
        if any(x < 0 for x in [max_daily_demand, avg_daily_demand, max_lead_time, avg_lead_time]):
            raise ValueError("All parameters must be non-negative")
        
        if max_daily_demand < avg_daily_demand:
            raise ValueError("Maximum daily demand must be >= average daily demand")
        
        if max_lead_time < avg_lead_time:
            raise ValueError("Maximum lead time must be >= average lead time")
        
        safety_stock = (max_daily_demand * max_lead_time) - (avg_daily_demand * avg_lead_time)
        return round(safety_stock, 2)
    
    @staticmethod
    def calculate_supplier_score(
        fill_rate: float,
        on_time_rate: float,
        quality_rate: float,
        cost_competitiveness: float
    ) -> float:
        """
        Calculate a weighted supplier performance score.
        
        The score combines multiple performance metrics with predefined weights:
        - Fill Rate: 30% (ability to fulfill orders completely)
        - On-Time Rate: 30% (delivery punctuality)
        - Quality Rate: 20% (product quality/defect rate)
        - Cost Competitiveness: 20% (price competitiveness)
        
        Args:
            fill_rate: Percentage of orders fulfilled completely (0.0 to 1.0)
            on_time_rate: Percentage of orders delivered on time (0.0 to 1.0)
            quality_rate: Percentage of products meeting quality standards (0.0 to 1.0)
            cost_competitiveness: Cost competitiveness score (0.0 to 1.0, where 1.0 is most competitive)
        
        Returns:
            float: Weighted supplier score (0.0 to 1.0)
        
        Example:
            >>> calculate_supplier_score(0.95, 0.90, 0.98, 0.85)
            0.921
        """
        # Validate inputs are in valid range
        for rate, name in [(fill_rate, "fill_rate"), (on_time_rate, "on_time_rate"),
                           (quality_rate, "quality_rate"), (cost_competitiveness, "cost_competitiveness")]:
            if not 0.0 <= rate <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")
        
        # Weighted calculation: 30% fill, 30% on-time, 20% quality, 20% cost
        score = (
            fill_rate * 0.3 +
            on_time_rate * 0.3 +
            quality_rate * 0.2 +
            cost_competitiveness * 0.2
        )
        
        return round(score, 3)
    
    @staticmethod
    def forecast_demand(
        historical_demand: List[float],
        periods: int,
        method: str = "moving_average",
        window_size: int = 7
    ) -> List[float]:
        """
        Forecast future demand using historical data.
        
        Supports multiple forecasting methods:
        - moving_average: Simple moving average
        - weighted_moving_average: Recent data weighted more heavily
        - exponential_smoothing: Exponential smoothing with alpha=0.3
        
        Args:
            historical_demand: List of historical demand values (most recent last)
            periods: Number of periods to forecast
            method: Forecasting method ("moving_average", "weighted_moving_average", "exponential_smoothing")
            window_size: Window size for moving average methods (default: 7)
        
        Returns:
            List[float]: Forecasted demand values for the specified periods
        
        Example:
            >>> forecast_demand([10, 12, 11, 13, 12, 14, 13], 3, "moving_average", 7)
            [12.14, 12.14, 12.14]
        """
        if not historical_demand:
            raise ValueError("Historical demand data cannot be empty")
        
        if periods <= 0:
            raise ValueError("Periods must be positive")
        
        if method not in ["moving_average", "weighted_moving_average", "exponential_smoothing"]:
            raise ValueError(f"Unknown forecasting method: {method}")
        
        forecast = []
        
        if method == "moving_average":
            # Simple moving average
            window = min(window_size, len(historical_demand))
            avg = statistics.mean(historical_demand[-window:])
            forecast = [round(avg, 2) for _ in range(periods)]
        
        elif method == "weighted_moving_average":
            # Weighted moving average (more weight on recent data)
            window = min(window_size, len(historical_demand))
            recent_data = historical_demand[-window:]
            weights = list(range(1, len(recent_data) + 1))
            weighted_sum = sum(d * w for d, w in zip(recent_data, weights))
            weight_total = sum(weights)
            avg = weighted_sum / weight_total
            forecast = [round(avg, 2) for _ in range(periods)]
        
        elif method == "exponential_smoothing":
            # Exponential smoothing with alpha = 0.3
            alpha = 0.3
            smoothed = historical_demand[0]
            
            # Calculate smoothed values for historical data
            for value in historical_demand[1:]:
                smoothed = alpha * value + (1 - alpha) * smoothed
            
            # Use last smoothed value for forecast
            forecast = [round(smoothed, 2) for _ in range(periods)]
        
        return forecast
    
    @staticmethod
    def optimize_route(
        orders: List[Order],
        warehouse_location: Location
    ) -> RouteOptimization:
        """
        Optimize delivery route by grouping orders by delivery area and prioritizing urgent orders.
        
        This is a simplified route optimization that:
        1. Groups orders by delivery area
        2. Prioritizes urgent orders within each area
        3. Estimates distance and time based on order count and area
        
        For production use, integrate with a proper routing API (e.g., Google Maps, HERE).
        
        Args:
            orders: List of Order objects to deliver
            warehouse_location: Starting location (warehouse)
        
        Returns:
            RouteOptimization: Optimized route with order sequence and estimates
        
        Example:
            >>> warehouse = Location(40.7128, -74.0060, "Warehouse A")
            >>> orders = [
            ...     Order("SO-001", "123 Main St", "Downtown", 40.7589, -73.9851, 1),
            ...     Order("SO-002", "456 Oak Ave", "Downtown", 40.7614, -73.9776, 3)
            ... ]
            >>> result = optimize_route(orders, warehouse)
            >>> result.optimized_order
            ['SO-002', 'SO-001']
        """
        if not orders:
            return RouteOptimization(
                optimized_order=[],
                total_distance_km=0.0,
                estimated_time_hours=0.0,
                delivery_groups={}
            )
        
        # Group orders by delivery area
        area_groups: Dict[str, List[Order]] = {}
        for order in orders:
            area = order.delivery_area or "Unknown"
            if area not in area_groups:
                area_groups[area] = []
            area_groups[area].append(order)
        
        # Sort orders within each area by priority (urgent first)
        for area in area_groups:
            area_groups[area].sort(key=lambda o: (-o.priority, o.order_id))
        
        # Create optimized order sequence
        optimized_order = []
        delivery_groups = {}
        
        # Sort areas by number of orders (deliver to areas with most orders first)
        sorted_areas = sorted(area_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for area, area_orders in sorted_areas:
            order_ids = [o.order_id for o in area_orders]
            optimized_order.extend(order_ids)
            delivery_groups[area] = order_ids
        
        # Estimate distance and time (simplified calculation)
        # In production, use actual routing API
        num_stops = len(orders)
        avg_distance_per_stop = 5.0  # km
        avg_time_per_stop = 0.5  # hours (includes driving and delivery time)
        
        total_distance_km = round(num_stops * avg_distance_per_stop, 2)
        estimated_time_hours = round(num_stops * avg_time_per_stop, 2)
        
        return RouteOptimization(
            optimized_order=optimized_order,
            total_distance_km=total_distance_km,
            estimated_time_hours=estimated_time_hours,
            delivery_groups=delivery_groups
        )
    
    @staticmethod
    def calculate_economic_order_quantity(
        annual_demand: float,
        ordering_cost: float,
        holding_cost_per_unit: float
    ) -> float:
        """
        Calculate the Economic Order Quantity (EOQ) for optimal order sizing.
        
        EOQ minimizes the total cost of ordering and holding inventory.
        
        Formula: EOQ = sqrt((2 × Annual Demand × Ordering Cost) / Holding Cost per Unit)
        
        Args:
            annual_demand: Annual demand for the product (units/year)
            ordering_cost: Fixed cost per order (currency)
            holding_cost_per_unit: Annual cost to hold one unit in inventory (currency/unit/year)
        
        Returns:
            float: Economic order quantity in units
        
        Example:
            >>> calculate_economic_order_quantity(1000, 50, 2)
            223.61
        """
        if annual_demand <= 0 or ordering_cost <= 0 or holding_cost_per_unit <= 0:
            raise ValueError("All parameters must be positive")
        
        eoq = ((2 * annual_demand * ordering_cost) / holding_cost_per_unit) ** 0.5
        return round(eoq, 2)
    
    @staticmethod
    def calculate_inventory_turnover(
        cost_of_goods_sold: float,
        average_inventory: float
    ) -> float:
        """
        Calculate inventory turnover ratio.
        
        Inventory turnover measures how many times inventory is sold and replaced
        over a period. Higher turnover indicates efficient inventory management.
        
        Formula: Inventory Turnover = Cost of Goods Sold / Average Inventory
        
        Args:
            cost_of_goods_sold: Total cost of goods sold during the period
            average_inventory: Average inventory value during the period
        
        Returns:
            float: Inventory turnover ratio
        
        Example:
            >>> calculate_inventory_turnover(500000, 50000)
            10.0
        """
        if average_inventory <= 0:
            raise ValueError("Average inventory must be positive")
        
        if cost_of_goods_sold < 0:
            raise ValueError("Cost of goods sold cannot be negative")
        
        turnover = cost_of_goods_sold / average_inventory
        return round(turnover, 2)
    
    @staticmethod
    def calculate_days_of_supply(
        current_inventory: float,
        avg_daily_demand: float
    ) -> float:
        """
        Calculate how many days the current inventory will last.
        
        Days of supply indicates how long current inventory will meet demand
        at the current consumption rate.
        
        Formula: Days of Supply = Current Inventory / Average Daily Demand
        
        Args:
            current_inventory: Current inventory quantity (units)
            avg_daily_demand: Average daily demand (units/day)
        
        Returns:
            float: Number of days the inventory will last
        
        Example:
            >>> calculate_days_of_supply(100, 10)
            10.0
        """
        if avg_daily_demand <= 0:
            raise ValueError("Average daily demand must be positive")
        
        if current_inventory < 0:
            raise ValueError("Current inventory cannot be negative")
        
        days = current_inventory / avg_daily_demand
        return round(days, 2)

"""
Test suite for cost tracking module
"""

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
import json

from cost_tracker import CostTracker, Cost, TokenUsage
from cost_logger import CostLogger


class TestTokenUsage:
    """Test TokenUsage dataclass"""
    
    def test_token_usage_creation(self):
        """Test creating TokenUsage object"""
        tokens = TokenUsage(input_tokens=100, output_tokens=200)
        assert tokens.input_tokens == 100
        assert tokens.output_tokens == 200
    
    def test_token_usage_addition(self):
        """Test adding two TokenUsage objects"""
        tokens1 = TokenUsage(input_tokens=100, output_tokens=200)
        tokens2 = TokenUsage(input_tokens=50, output_tokens=75)
        result = tokens1 + tokens2
        
        assert result.input_tokens == 150
        assert result.output_tokens == 275


class TestCost:
    """Test Cost dataclass"""
    
    def test_cost_creation(self):
        """Test creating Cost object"""
        cost = Cost(
            bedrock_cost=0.01,
            redshift_cost=0.005,
            lambda_cost=0.001,
            total_cost=0.016,
            tokens_used=TokenUsage(100, 200)
        )
        
        assert cost.bedrock_cost == 0.01
        assert cost.redshift_cost == 0.005
        assert cost.lambda_cost == 0.001
        assert cost.total_cost == 0.016
        assert cost.tokens_used.input_tokens == 100
    
    def test_cost_addition(self):
        """Test adding two Cost objects"""
        cost1 = Cost(
            bedrock_cost=0.01,
            redshift_cost=0.005,
            lambda_cost=0.001,
            total_cost=0.016,
            tokens_used=TokenUsage(100, 200)
        )
        cost2 = Cost(
            bedrock_cost=0.02,
            redshift_cost=0.003,
            lambda_cost=0.002,
            total_cost=0.025,
            tokens_used=TokenUsage(50, 75)
        )
        
        result = cost1 + cost2
        
        assert result.bedrock_cost == 0.03
        assert result.redshift_cost == 0.008
        assert result.lambda_cost == 0.003
        assert result.total_cost == 0.041
        assert result.tokens_used.input_tokens == 150
        assert result.tokens_used.output_tokens == 275


class TestCostTracker:
    """Test CostTracker class"""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration"""
        return {
            'enabled': True,
            'bedrock_input_cost_per_1k': 0.003,
            'bedrock_output_cost_per_1k': 0.015,
            'redshift_rpu_cost_per_hour': 0.36,
            'redshift_base_rpus': 8,
            'lambda_cost_per_gb_second': 0.0000166667
        }
    
    @pytest.fixture
    def tracker(self, config):
        """Provide CostTracker instance"""
        return CostTracker(config)
    
    def test_tracker_initialization(self, tracker):
        """Test CostTracker initialization"""
        assert tracker.enabled is True
        assert tracker.bedrock_input_cost_per_1k == 0.003
        assert tracker.bedrock_output_cost_per_1k == 0.015
    
    def test_calculate_bedrock_cost(self, tracker):
        """Test Bedrock cost calculation"""
        # 1000 input tokens + 1000 output tokens
        cost = tracker.calculate_bedrock_cost(1000, 1000)
        expected = (1000/1000 * 0.003) + (1000/1000 * 0.015)
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_calculate_redshift_cost(self, tracker):
        """Test Redshift cost calculation"""
        # 10 seconds execution time
        cost = tracker.calculate_redshift_cost(10.0)
        # 8 RPUs * (10/3600) hours * 0.36 per RPU-hour
        expected = 8 * (10/3600) * 0.36
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_calculate_lambda_cost(self, tracker):
        """Test Lambda cost calculation"""
        # 1000ms duration, 512MB memory
        cost = tracker.calculate_lambda_cost(1000, 512)
        # (512/1024) GB * 1 second * 0.0000166667
        expected = (512/1024) * 1 * 0.0000166667
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_calculate_query_cost(self, tracker):
        """Test complete query cost calculation"""
        tokens = TokenUsage(input_tokens=1000, output_tokens=500)
        cost = tracker.calculate_query_cost(
            bedrock_tokens=tokens,
            redshift_execution_time=5.0,
            lambda_duration_ms=500,
            lambda_memory_mb=512
        )
        
        assert cost.bedrock_cost > 0
        assert cost.redshift_cost > 0
        assert cost.lambda_cost > 0
        assert cost.total_cost == pytest.approx(
            cost.bedrock_cost + cost.redshift_cost + cost.lambda_cost,
            rel=1e-6
        )
        assert cost.tokens_used.input_tokens == 1000
        assert cost.tokens_used.output_tokens == 500
    
    def test_add_query_cost(self, tracker):
        """Test adding query cost to session and daily totals"""
        session_id = "test_session"
        cost = Cost(
            bedrock_cost=0.01,
            redshift_cost=0.005,
            lambda_cost=0.001,
            total_cost=0.016,
            tokens_used=TokenUsage(100, 200)
        )
        
        tracker.add_query_cost(session_id, cost)
        
        session_cost = tracker.get_session_cost(session_id)
        assert session_cost.total_cost == 0.016
        
        daily_cost = tracker.get_daily_cost()
        assert daily_cost.total_cost == 0.016
    
    def test_get_session_cost(self, tracker):
        """Test getting session cost"""
        session_id = "test_session"
        cost1 = Cost(total_cost=0.01, tokens_used=TokenUsage(100, 200))
        cost2 = Cost(total_cost=0.02, tokens_used=TokenUsage(50, 75))
        
        tracker.add_query_cost(session_id, cost1)
        tracker.add_query_cost(session_id, cost2)
        
        session_cost = tracker.get_session_cost(session_id)
        assert session_cost.total_cost == 0.03
        assert session_cost.tokens_used.input_tokens == 150
    
    def test_get_daily_cost(self, tracker):
        """Test getting daily cost"""
        cost1 = Cost(total_cost=0.01, tokens_used=TokenUsage(100, 200))
        cost2 = Cost(total_cost=0.02, tokens_used=TokenUsage(50, 75))
        
        tracker.add_query_cost("session1", cost1)
        tracker.add_query_cost("session2", cost2)
        
        daily_cost = tracker.get_daily_cost()
        assert daily_cost.total_cost == 0.03
    
    def test_get_monthly_estimate(self, tracker):
        """Test monthly cost estimation"""
        cost = Cost(total_cost=5.0, tokens_used=TokenUsage(1000, 2000))
        tracker.add_query_cost("session1", cost)
        
        monthly_estimate = tracker.get_monthly_estimate()
        assert monthly_estimate == 150.0  # 5.0 * 30
    
    def test_get_cost_breakdown(self, tracker):
        """Test cost breakdown"""
        cost = Cost(
            bedrock_cost=0.01,
            redshift_cost=0.005,
            lambda_cost=0.001,
            total_cost=0.016,
            tokens_used=TokenUsage(100, 200)
        )
        tracker.add_query_cost("session1", cost)
        
        breakdown = tracker.get_cost_breakdown("session1")
        assert breakdown['bedrock'] == 0.01
        assert breakdown['redshift'] == 0.005
        assert breakdown['lambda'] == 0.001
        assert breakdown['total'] == 0.016
    
    def test_format_cost(self, tracker):
        """Test cost formatting"""
        formatted = tracker.format_cost(0.0234)
        assert formatted == "$0.0234"
    
    def test_clear_session_costs(self, tracker):
        """Test clearing session costs"""
        session_id = "test_session"
        cost = Cost(total_cost=0.01, tokens_used=TokenUsage(100, 200))
        
        tracker.add_query_cost(session_id, cost)
        assert tracker.get_session_cost(session_id).total_cost == 0.01
        
        tracker.clear_session_costs(session_id)
        assert tracker.get_session_cost(session_id).total_cost == 0.0
    
    def test_disabled_tracker(self):
        """Test that disabled tracker doesn't track costs"""
        config = {'enabled': False}
        tracker = CostTracker(config)
        
        cost = Cost(total_cost=0.01, tokens_used=TokenUsage(100, 200))
        tracker.add_query_cost("session1", cost)
        
        # Should return empty cost
        session_cost = tracker.get_session_cost("session1")
        assert session_cost.total_cost == 0.0


class TestCostLogger:
    """Test CostLogger class"""
    
    @pytest.fixture
    def temp_log_file(self):
        """Provide temporary log file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            yield f.name
        # Cleanup
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def logger(self, temp_log_file):
        """Provide CostLogger instance"""
        return CostLogger(temp_log_file, enabled=True)
    
    def test_logger_initialization(self, logger, temp_log_file):
        """Test CostLogger initialization"""
        assert logger.enabled is True
        assert logger.log_file_path == Path(temp_log_file)
    
    def test_log_query_cost(self, logger, temp_log_file):
        """Test logging query cost"""
        cost = Cost(
            bedrock_cost=0.01,
            redshift_cost=0.005,
            lambda_cost=0.001,
            total_cost=0.016,
            tokens_used=TokenUsage(100, 200)
        )
        
        logger.log_query_cost(
            session_id="test_session",
            persona="Warehouse Manager",
            query="Show me low stock products",
            cost=cost,
            execution_time=2.5,
            cached=False,
            query_type="SQL_QUERY"
        )
        
        # Verify log file was created and contains data
        assert Path(temp_log_file).exists()
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "test_session" in content
            assert "Warehouse Manager" in content
    
    def test_log_daily_summary(self, logger, temp_log_file):
        """Test logging daily summary"""
        cost = Cost(
            bedrock_cost=0.5,
            redshift_cost=0.3,
            lambda_cost=0.1,
            total_cost=0.9,
            tokens_used=TokenUsage(10000, 20000)
        )
        
        logger.log_daily_summary(date.today(), cost, query_count=50)
        
        # Verify log file contains summary
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "daily_summary" in content
            assert "query_count" in content
    
    def test_generate_cost_breakdown(self, logger):
        """Test generating cost breakdown"""
        cost = Cost(
            bedrock_cost=0.01,
            redshift_cost=0.005,
            lambda_cost=0.001,
            total_cost=0.016,
            tokens_used=TokenUsage(100, 200)
        )
        
        breakdown = logger.generate_cost_breakdown(cost)
        assert "Bedrock:" in breakdown
        assert "Redshift:" in breakdown
        assert "Lambda:" in breakdown
        assert "$0.0100" in breakdown
    
    def test_export_json(self, logger):
        """Test exporting cost data as JSON"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_file = f.name
        
        try:
            cost_data = {
                date(2024, 1, 1): Cost(total_cost=1.0, tokens_used=TokenUsage(1000, 2000)),
                date(2024, 1, 2): Cost(total_cost=2.0, tokens_used=TokenUsage(2000, 4000))
            }
            
            logger.export_cost_data(output_file, cost_data, format='json')
            
            # Verify JSON file
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]['date'] == '2024-01-01'
                assert data[0]['total_cost'] == 1.0
        finally:
            Path(output_file).unlink(missing_ok=True)
    
    def test_export_csv(self, logger):
        """Test exporting cost data as CSV"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            output_file = f.name
        
        try:
            cost_data = {
                date(2024, 1, 1): Cost(total_cost=1.0, tokens_used=TokenUsage(1000, 2000)),
                date(2024, 1, 2): Cost(total_cost=2.0, tokens_used=TokenUsage(2000, 4000))
            }
            
            logger.export_cost_data(output_file, cost_data, format='csv')
            
            # Verify CSV file
            with open(output_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3  # Header + 2 data rows
                assert 'date,bedrock_cost' in lines[0]
                assert '2024-01-01' in lines[1]
        finally:
            Path(output_file).unlink(missing_ok=True)
    
    def test_read_log_entries(self, logger, temp_log_file):
        """Test reading log entries"""
        # Log some entries
        cost = Cost(total_cost=0.01, tokens_used=TokenUsage(100, 200))
        logger.log_query_cost(
            session_id="session1",
            persona="Warehouse Manager",
            query="Test query",
            cost=cost,
            execution_time=1.0
        )
        
        # Read entries
        entries = logger.read_log_entries()
        assert len(entries) > 0
        assert entries[0]['session_id'] == 'session1'
        assert entries[0]['persona'] == 'Warehouse Manager'
    
    def test_disabled_logger(self, temp_log_file):
        """Test that disabled logger doesn't log"""
        logger = CostLogger(temp_log_file, enabled=False)
        
        cost = Cost(total_cost=0.01, tokens_used=TokenUsage(100, 200))
        logger.log_query_cost(
            session_id="session1",
            persona="Warehouse Manager",
            query="Test query",
            cost=cost,
            execution_time=1.0
        )
        
        # Log file should be empty or not exist
        if Path(temp_log_file).exists():
            with open(temp_log_file, 'r') as f:
                content = f.read()
                assert len(content) == 0 or "session1" not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

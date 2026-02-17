"""
Cost Logger Module

This module provides logging functionality for cost tracking in the Supply Chain AI MVP system.
Logs cost information to file for analysis and generates cost reports.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .cost_tracker import Cost, TokenUsage
except ImportError:
    from cost_tracker import Cost, TokenUsage


class CostLogger:
    """
    Log cost information to file and generate cost reports.
    
    This class provides methods to:
    - Log individual query costs
    - Generate daily cost reports
    - Generate cost summaries and breakdowns
    - Export cost data for analysis
    """
    
    def __init__(self, log_file_path: str, enabled: bool = True):
        """
        Initialize the cost logger.
        
        Args:
            log_file_path: Path to the cost log file
            enabled: Whether cost logging is enabled
        """
        self.log_file_path = Path(log_file_path)
        self.enabled = enabled
        
        # Create log directory if it doesn't exist
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger('cost_logger')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create file handler
        if self.enabled:
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
    
    def log_query_cost(
        self,
        session_id: str,
        persona: str,
        query: str,
        cost: Cost,
        execution_time: float,
        cached: bool = False,
        query_type: str = "unknown"
    ) -> None:
        """
        Log cost information for a single query.
        
        Args:
            session_id: Session identifier
            persona: User persona (Warehouse Manager, Field Engineer, etc.)
            query: User query text
            cost: Cost object with breakdown
            execution_time: Query execution time in seconds
            cached: Whether result was from cache
            query_type: Type of query (SQL_QUERY, OPTIMIZATION, HYBRID)
        """
        if not self.enabled:
            return
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'persona': persona,
            'query': query[:100] + '...' if len(query) > 100 else query,  # Truncate long queries
            'query_type': query_type,
            'cached': cached,
            'execution_time': round(execution_time, 3),
            'costs': {
                'bedrock': round(cost.bedrock_cost, 6),
                'redshift': round(cost.redshift_cost, 6),
                'lambda': round(cost.lambda_cost, 6),
                'total': round(cost.total_cost, 6)
            },
            'tokens': {
                'input': cost.tokens_used.input_tokens,
                'output': cost.tokens_used.output_tokens,
                'total': cost.tokens_used.input_tokens + cost.tokens_used.output_tokens
            }
        }
        
        # Log as JSON for easy parsing
        self.logger.info(json.dumps(log_entry))
    
    def log_daily_summary(self, target_date: date, total_cost: Cost, query_count: int) -> None:
        """
        Log daily cost summary.
        
        Args:
            target_date: Date for the summary
            total_cost: Total cost for the day
            query_count: Number of queries executed
        """
        if not self.enabled:
            return
        
        summary = {
            'type': 'daily_summary',
            'date': target_date.isoformat(),
            'query_count': query_count,
            'costs': {
                'bedrock': round(total_cost.bedrock_cost, 6),
                'redshift': round(total_cost.redshift_cost, 6),
                'lambda': round(total_cost.lambda_cost, 6),
                'total': round(total_cost.total_cost, 6)
            },
            'tokens': {
                'input': total_cost.tokens_used.input_tokens,
                'output': total_cost.tokens_used.output_tokens,
                'total': total_cost.tokens_used.input_tokens + total_cost.tokens_used.output_tokens
            },
            'avg_cost_per_query': round(total_cost.total_cost / query_count, 6) if query_count > 0 else 0
        }
        
        self.logger.info(json.dumps(summary))
    
    def generate_cost_report(
        self,
        start_date: date,
        end_date: date,
        cost_data: Dict[date, Cost]
    ) -> str:
        """
        Generate a formatted cost report for a date range.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            cost_data: Dictionary mapping dates to Cost objects
            
        Returns:
            Formatted cost report as string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"Cost Report: {start_date} to {end_date}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Calculate totals
        total_cost = Cost()
        days_with_data = 0
        
        for current_date in self._date_range(start_date, end_date):
            if current_date in cost_data:
                daily_cost = cost_data[current_date]
                total_cost = total_cost + daily_cost
                days_with_data += 1
                
                report_lines.append(f"{current_date}:")
                report_lines.append(f"  Bedrock:  ${daily_cost.bedrock_cost:.4f}")
                report_lines.append(f"  Redshift: ${daily_cost.redshift_cost:.4f}")
                report_lines.append(f"  Lambda:   ${daily_cost.lambda_cost:.4f}")
                report_lines.append(f"  Total:    ${daily_cost.total_cost:.4f}")
                report_lines.append(f"  Tokens:   {daily_cost.tokens_used.input_tokens} in / {daily_cost.tokens_used.output_tokens} out")
                report_lines.append("")
        
        # Add summary
        report_lines.append("-" * 80)
        report_lines.append("Summary:")
        report_lines.append(f"  Days with data: {days_with_data}")
        report_lines.append(f"  Total Bedrock:  ${total_cost.bedrock_cost:.4f}")
        report_lines.append(f"  Total Redshift: ${total_cost.redshift_cost:.4f}")
        report_lines.append(f"  Total Lambda:   ${total_cost.lambda_cost:.4f}")
        report_lines.append(f"  Grand Total:    ${total_cost.total_cost:.4f}")
        report_lines.append(f"  Total Tokens:   {total_cost.tokens_used.input_tokens} in / {total_cost.tokens_used.output_tokens} out")
        
        if days_with_data > 0:
            avg_daily = total_cost.total_cost / days_with_data
            report_lines.append(f"  Avg Daily Cost: ${avg_daily:.4f}")
            report_lines.append(f"  Est. Monthly:   ${avg_daily * 30:.2f}")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def generate_cost_breakdown(self, cost: Cost) -> str:
        """
        Generate a formatted cost breakdown.
        
        Args:
            cost: Cost object to break down
            
        Returns:
            Formatted cost breakdown as string
        """
        lines = []
        lines.append("Cost Breakdown:")
        lines.append(f"  Bedrock:  ${cost.bedrock_cost:.4f} ({self._percentage(cost.bedrock_cost, cost.total_cost)})")
        lines.append(f"  Redshift: ${cost.redshift_cost:.4f} ({self._percentage(cost.redshift_cost, cost.total_cost)})")
        lines.append(f"  Lambda:   ${cost.lambda_cost:.4f} ({self._percentage(cost.lambda_cost, cost.total_cost)})")
        lines.append(f"  Total:    ${cost.total_cost:.4f}")
        
        return "\n".join(lines)
    
    def export_cost_data(
        self,
        output_file: str,
        cost_data: Dict[date, Cost],
        format: str = 'json'
    ) -> None:
        """
        Export cost data to file for analysis.
        
        Args:
            output_file: Path to output file
            cost_data: Dictionary mapping dates to Cost objects
            format: Export format ('json' or 'csv')
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            self._export_json(output_path, cost_data)
        elif format == 'csv':
            self._export_csv(output_path, cost_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, output_path: Path, cost_data: Dict[date, Cost]) -> None:
        """Export cost data as JSON"""
        export_data = []
        
        for date_key, cost in sorted(cost_data.items()):
            export_data.append({
                'date': date_key.isoformat(),
                'bedrock_cost': cost.bedrock_cost,
                'redshift_cost': cost.redshift_cost,
                'lambda_cost': cost.lambda_cost,
                'total_cost': cost.total_cost,
                'input_tokens': cost.tokens_used.input_tokens,
                'output_tokens': cost.tokens_used.output_tokens
            })
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _export_csv(self, output_path: Path, cost_data: Dict[date, Cost]) -> None:
        """Export cost data as CSV"""
        with open(output_path, 'w') as f:
            # Write header
            f.write("date,bedrock_cost,redshift_cost,lambda_cost,total_cost,input_tokens,output_tokens\n")
            
            # Write data rows
            for date_key, cost in sorted(cost_data.items()):
                f.write(f"{date_key.isoformat()},")
                f.write(f"{cost.bedrock_cost:.6f},")
                f.write(f"{cost.redshift_cost:.6f},")
                f.write(f"{cost.lambda_cost:.6f},")
                f.write(f"{cost.total_cost:.6f},")
                f.write(f"{cost.tokens_used.input_tokens},")
                f.write(f"{cost.tokens_used.output_tokens}\n")
    
    def read_log_entries(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        persona: Optional[str] = None
    ) -> List[Dict]:
        """
        Read and parse log entries from the cost log file.
        
        Args:
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            persona: Filter entries by persona
            
        Returns:
            List of parsed log entries
        """
        if not self.log_file_path.exists():
            return []
        
        entries = []
        
        with open(self.log_file_path, 'r') as f:
            for line in f:
                # Skip non-JSON lines (like log level prefixes)
                if ' - INFO - ' in line:
                    # Extract JSON part
                    json_start = line.find('{')
                    if json_start != -1:
                        json_str = line[json_start:]
                        try:
                            entry = json.loads(json_str)
                            
                            # Apply filters
                            if start_date or end_date or persona:
                                entry_time = datetime.fromisoformat(entry['timestamp'])
                                
                                if start_date and entry_time < start_date:
                                    continue
                                if end_date and entry_time > end_date:
                                    continue
                                if persona and entry.get('persona') != persona:
                                    continue
                            
                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        
        return entries
    
    def _date_range(self, start_date: date, end_date: date):
        """Generate date range between start and end dates"""
        current = start_date
        while current <= end_date:
            yield current
            # Add one day
            from datetime import timedelta
            current = current + timedelta(days=1)
    
    def _percentage(self, part: float, total: float) -> str:
        """Calculate percentage and format as string"""
        if total == 0:
            return "0.0%"
        return f"{(part / total * 100):.1f}%"

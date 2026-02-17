"""
Cache Statistics

Provides detailed cache statistics tracking and reporting.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import time


@dataclass
class CacheStatsSnapshot:
    """Snapshot of cache statistics at a point in time."""
    timestamp: float
    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: float
    evictions: int
    expirations: int
    total_requests: int
    utilization: float  # Percentage of max_size used
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CacheStatsTracker:
    """
    Tracks cache statistics over time.
    
    Features:
    - Historical snapshots
    - Aggregated statistics
    - Performance metrics
    """
    
    def __init__(self, max_snapshots: int = 100):
        """
        Initialize cache statistics tracker.
        
        Args:
            max_snapshots: Maximum number of historical snapshots to keep
        """
        self.max_snapshots = max_snapshots
        self._snapshots: List[CacheStatsSnapshot] = []
    
    def record_snapshot(self, stats: Dict[str, Any]) -> CacheStatsSnapshot:
        """
        Record a cache statistics snapshot.
        
        Args:
            stats: Statistics dictionary from QueryCache.get_stats()
            
        Returns:
            CacheStatsSnapshot object
        """
        # Calculate utilization
        utilization = (stats["size"] / stats["max_size"] * 100) if stats["max_size"] > 0 else 0.0
        
        snapshot = CacheStatsSnapshot(
            timestamp=time.time(),
            size=stats["size"],
            max_size=stats["max_size"],
            hits=stats["hits"],
            misses=stats["misses"],
            hit_rate=stats["hit_rate"],
            evictions=stats["evictions"],
            expirations=stats["expirations"],
            total_requests=stats["total_requests"],
            utilization=utilization
        )
        
        # Add to snapshots
        self._snapshots.append(snapshot)
        
        # Trim if exceeds max
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots = self._snapshots[-self.max_snapshots:]
        
        return snapshot
    
    def get_latest_snapshot(self) -> CacheStatsSnapshot | None:
        """
        Get the most recent snapshot.
        
        Returns:
            Latest CacheStatsSnapshot or None if no snapshots
        """
        return self._snapshots[-1] if self._snapshots else None
    
    def get_all_snapshots(self) -> List[CacheStatsSnapshot]:
        """
        Get all historical snapshots.
        
        Returns:
            List of CacheStatsSnapshot objects
        """
        return self._snapshots.copy()
    
    def get_aggregated_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics across all snapshots.
        
        Returns:
            Dictionary with aggregated statistics
        """
        if not self._snapshots:
            return {
                "total_snapshots": 0,
                "avg_hit_rate": 0.0,
                "avg_utilization": 0.0,
                "total_evictions": 0,
                "total_expirations": 0
            }
        
        total_hit_rate = sum(s.hit_rate for s in self._snapshots)
        total_utilization = sum(s.utilization for s in self._snapshots)
        
        latest = self._snapshots[-1]
        
        return {
            "total_snapshots": len(self._snapshots),
            "avg_hit_rate": total_hit_rate / len(self._snapshots),
            "avg_utilization": total_utilization / len(self._snapshots),
            "total_evictions": latest.evictions,
            "total_expirations": latest.expirations,
            "current_size": latest.size,
            "current_hit_rate": latest.hit_rate
        }
    
    def get_performance_summary(self) -> str:
        """
        Get human-readable performance summary.
        
        Returns:
            Formatted performance summary string
        """
        if not self._snapshots:
            return "No cache statistics available"
        
        latest = self._snapshots[-1]
        aggregated = self.get_aggregated_stats()
        
        summary = f"""Cache Performance Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Status:
  • Cache Size: {latest.size}/{latest.max_size} ({latest.utilization:.1f}% full)
  • Hit Rate: {latest.hit_rate:.1f}%
  • Total Requests: {latest.total_requests:,}
  • Hits: {latest.hits:,} | Misses: {latest.misses:,}

Historical Performance:
  • Average Hit Rate: {aggregated['avg_hit_rate']:.1f}%
  • Average Utilization: {aggregated['avg_utilization']:.1f}%
  • Total Evictions: {aggregated['total_evictions']:,}
  • Total Expirations: {aggregated['total_expirations']:,}
  • Snapshots Recorded: {aggregated['total_snapshots']}

Performance Rating: {self._get_performance_rating(latest.hit_rate)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return summary
    
    def _get_performance_rating(self, hit_rate: float) -> str:
        """
        Get performance rating based on hit rate.
        
        Args:
            hit_rate: Cache hit rate percentage
            
        Returns:
            Performance rating string
        """
        if hit_rate >= 80:
            return "Excellent ⭐⭐⭐⭐⭐"
        elif hit_rate >= 60:
            return "Good ⭐⭐⭐⭐"
        elif hit_rate >= 40:
            return "Fair ⭐⭐⭐"
        elif hit_rate >= 20:
            return "Poor ⭐⭐"
        else:
            return "Very Poor ⭐"
    
    def clear_snapshots(self) -> None:
        """Clear all historical snapshots."""
        self._snapshots.clear()
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export all statistics to dictionary.
        
        Returns:
            Dictionary with all statistics and snapshots
        """
        return {
            "aggregated": self.get_aggregated_stats(),
            "snapshots": [s.to_dict() for s in self._snapshots]
        }


def format_cache_stats_for_ui(stats: Dict[str, Any]) -> str:
    """
    Format cache statistics for UI display.
    
    Args:
        stats: Statistics dictionary from QueryCache.get_stats()
        
    Returns:
        Formatted string for UI display
    """
    hit_rate = stats.get("hit_rate", 0.0)
    size = stats.get("size", 0)
    max_size = stats.get("max_size", 0)
    hits = stats.get("hits", 0)
    misses = stats.get("misses", 0)
    
    return f"""📊 Cache Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hit Rate: {hit_rate:.1f}%
Cached Entries: {size}/{max_size}
Hits: {hits:,} | Misses: {misses:,}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

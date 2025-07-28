"""
Database Connection Pool Metrics Module.

This module provides comprehensive metrics tracking, calculation, and reporting
for database connection pools, including performance monitoring and analysis.
"""

import json
import time
import threading
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict, replace
from collections import deque
from ..core.logging import get_logger


@dataclass(frozen=True)
class PoolMetrics:
    """Connection pool performance metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connections_created: int = 0
    connections_closed: int = 0
    pool_hits: int = 0
    pool_misses: int = 0
    health_check_failures: int = 0
    query_count: int = 0
    avg_connection_time: float = 0.0
    total_connection_time: float = 0.0
    last_reset: float = field(default_factory=time.time)
    
    def reset(self) -> 'PoolMetrics':
        """
        Reset performance counters while preserving current state metrics.
        
        Returns:
            New PoolMetrics instance with reset counters
        """
        return replace(
            self,
            connections_created=0,
            connections_closed=0,
            pool_hits=0,
            pool_misses=0,
            health_check_failures=0,
            query_count=0,
            total_connection_time=0.0,
            last_reset=time.time()
        )
    
    def increment_pool_hits(self) -> 'PoolMetrics':
        """
        Increment pool hits counter.
        
        Returns:
            New PoolMetrics instance with incremented pool hits
        """
        return replace(self, pool_hits=self.pool_hits + 1)
    
    def increment_pool_misses(self) -> 'PoolMetrics':
        """
        Increment pool misses counter.
        
        Returns:
            New PoolMetrics instance with incremented pool misses
        """
        return replace(self, pool_misses=self.pool_misses + 1)
    
    def increment_connections_created(self) -> 'PoolMetrics':
        """
        Increment connections created counter.
        
        Returns:
            New PoolMetrics instance with incremented connections created
        """
        return replace(
            self, 
            connections_created=self.connections_created + 1,
            total_connections=self.total_connections + 1
        )
    
    def increment_connections_closed(self) -> 'PoolMetrics':
        """
        Increment connections closed counter.
        
        Returns:
            New PoolMetrics instance with incremented connections closed
        """
        return replace(
            self, 
            connections_closed=self.connections_closed + 1,
            total_connections=max(0, self.total_connections - 1)
        )
    
    def update_connection_counts(self, active: int, idle: int, total: int) -> 'PoolMetrics':
        """
        Update current connection counts.
        
        Args:
            active: Current active connections
            idle: Current idle connections
            total: Current total connections
            
        Returns:
            New PoolMetrics instance with updated counts
        """
        return replace(
            self,
            active_connections=active,
            idle_connections=idle,
            total_connections=total
        )
    
    def update_connection_time(self, connection_time: float) -> 'PoolMetrics':
        """
        Update average connection time with new measurement.
        
        Args:
            connection_time: Time taken to obtain connection
            
        Returns:
            New PoolMetrics instance with updated average time
        """
        new_query_count = self.query_count + 1
        new_total_time = self.total_connection_time + connection_time
        new_avg_time = new_total_time / new_query_count if new_query_count > 0 else 0.0
        
        return replace(
            self,
            query_count=new_query_count,
            total_connection_time=new_total_time,
            avg_connection_time=new_avg_time
        )


class MetricsCalculator:
    """Calculator for derived metrics and performance indicators"""
    
    def __init__(self):
        self.logger = get_logger("metrics_calculator")
    
    def calculate_hit_ratio(self, metrics: PoolMetrics) -> float:
        """
        Calculate pool hit ratio.
        
        Args:
            metrics: Pool metrics to analyze
            
        Returns:
            Hit ratio as a float between 0.0 and 1.0
        """
        total_requests = metrics.pool_hits + metrics.pool_misses
        if total_requests == 0:
            return 0.0
        return metrics.pool_hits / total_requests
    
    def calculate_utilization(self, metrics: PoolMetrics) -> float:
        """
        Calculate pool utilization rate.
        
        Args:
            metrics: Pool metrics to analyze
            
        Returns:
            Utilization ratio as a float between 0.0 and 1.0
        """
        if metrics.total_connections == 0:
            return 0.0
        return metrics.active_connections / metrics.total_connections
    
    def calculate_efficiency(self, metrics: PoolMetrics) -> float:
        """
        Calculate connection efficiency based on usage patterns.
        
        Args:
            metrics: Pool metrics to analyze
            
        Returns:
            Efficiency score as a float
        """
        if metrics.connections_created == 0:
            return 0.0
        
        # Calculate churn rate (how often connections are recycled)
        churn_rate = metrics.connections_closed / metrics.connections_created
        
        # Calculate queries per connection
        queries_per_connection = (
            metrics.query_count / metrics.connections_created
            if metrics.connections_created > 0 else 0
        )
        
        # Efficiency is higher with more queries per connection and lower churn
        efficiency = queries_per_connection * (1.0 - min(churn_rate, 1.0))
        return max(0.0, efficiency)
    
    def calculate_turnover_rate(self, metrics: PoolMetrics) -> float:
        """
        Calculate connection turnover rate per hour.
        
        Args:
            metrics: Pool metrics to analyze
            
        Returns:
            Turnover rate as connections per hour
        """
        time_elapsed = time.time() - metrics.last_reset
        if time_elapsed <= 0:
            return 0.0
        
        # Convert to hourly rate
        hours_elapsed = time_elapsed / 3600.0
        return (metrics.connections_created + metrics.connections_closed) / hours_elapsed
    
    def calculate_average_lifetime(self, metrics: PoolMetrics) -> float:
        """
        Calculate average connection lifetime.
        
        Args:
            metrics: Pool metrics to analyze
            
        Returns:
            Average lifetime in seconds
        """
        if metrics.connections_closed == 0:
            return 0.0
        return metrics.total_connection_time / metrics.connections_closed
    
    def calculate_performance_score(self, metrics: PoolMetrics) -> float:
        """
        Calculate overall performance score (0.0 to 1.0).
        
        Args:
            metrics: Pool metrics to analyze
            
        Returns:
            Composite performance score
        """
        hit_ratio = self.calculate_hit_ratio(metrics)
        utilization = self.calculate_utilization(metrics)
        
        # Factor in health check failures
        failure_rate = (
            metrics.health_check_failures / max(1, metrics.query_count)
            if metrics.query_count > 0 else 0
        )
        health_score = max(0.0, 1.0 - failure_rate)
        
        # Weighted composite score
        score = (
            hit_ratio * 0.4 +        # 40% weight on hit ratio
            utilization * 0.3 +      # 30% weight on utilization
            health_score * 0.3       # 30% weight on health
        )
        
        return min(1.0, max(0.0, score))


@dataclass(frozen=True)
class MetricsSnapshot:
    """Immutable snapshot of metrics at a specific time"""
    metrics: PoolMetrics
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def create(cls, metrics: PoolMetrics) -> 'MetricsSnapshot':
        """
        Create a new metrics snapshot.
        
        Args:
            metrics: Pool metrics to snapshot
            
        Returns:
            New MetricsSnapshot instance
        """
        return cls(metrics=metrics)
    
    def time_since_creation(self) -> float:
        """
        Calculate time elapsed since snapshot creation.
        
        Returns:
            Time elapsed in seconds
        """
        return time.time() - self.timestamp
    
    def diff_from(self, other: 'MetricsSnapshot') -> Dict[str, Any]:
        """
        Calculate differences from another snapshot.
        
        Args:
            other: Other snapshot to compare against
            
        Returns:
            Dictionary of differences
        """
        current_dict = asdict(self.metrics)
        other_dict = asdict(other.metrics)
        
        diff = {}
        for key in current_dict:
            if isinstance(current_dict[key], (int, float)):
                diff[key] = current_dict[key] - other_dict[key]
        
        diff['time_elapsed'] = self.timestamp - other.timestamp
        return diff
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert snapshot to dictionary.
        
        Returns:
            Dictionary representation of snapshot
        """
        return {
            'timestamp': self.timestamp,
            'metrics': asdict(self.metrics)
        }


class MetricsReporter:
    """Reporter for generating human-readable metrics reports"""
    
    def __init__(self):
        self.logger = get_logger("metrics_reporter")
        self.calculator = MetricsCalculator()
    
    def generate_report(self, metrics: PoolMetrics, include_calculations: bool = False) -> str:
        """
        Generate a human-readable metrics report.
        
        Args:
            metrics: Pool metrics to report
            include_calculations: Whether to include calculated metrics
            
        Returns:
            Formatted report string
        """
        lines = [
            "=== Connection Pool Metrics Report ===",
            f"Total Connections: {metrics.total_connections}",
            f"Active Connections: {metrics.active_connections}",
            f"Idle Connections: {metrics.idle_connections}",
            "",
            "=== Performance Counters ===",
            f"Connections Created: {metrics.connections_created}",
            f"Connections Closed: {metrics.connections_closed}",
            f"Pool Hits: {metrics.pool_hits}",
            f"Pool Misses: {metrics.pool_misses}",
            f"Query Count: {metrics.query_count}",
            f"Health Check Failures: {metrics.health_check_failures}",
            f"Average Connection Time: {metrics.avg_connection_time:.4f}s",
        ]
        
        if include_calculations:
            hit_ratio = self.calculator.calculate_hit_ratio(metrics)
            utilization = self.calculator.calculate_utilization(metrics)
            efficiency = self.calculator.calculate_efficiency(metrics)
            score = self.calculator.calculate_performance_score(metrics)
            
            lines.extend([
                "",
                "=== Calculated Metrics ===",
                f"Hit Ratio: {hit_ratio:.2%}",
                f"Utilization: {utilization:.2%}",
                f"Efficiency Score: {efficiency:.2f}",
                f"Performance Score: {score:.2%}",
            ])
        
        lines.append(f"\nReport generated at: {time.ctime()}")
        return "\n".join(lines)
    
    def format_metrics(self, metrics: PoolMetrics, template: str) -> str:
        """
        Format metrics using a custom template.
        
        Args:
            metrics: Pool metrics to format
            template: Format template string
            
        Returns:
            Formatted string
        """
        metrics_dict = asdict(metrics)
        try:
            return template.format(**metrics_dict)
        except KeyError as e:
            self.logger.error(f"Template formatting error: {e}")
            return f"Template error: missing key {e}"
    
    def export_metrics(self, metrics: PoolMetrics, format: str = 'json') -> str:
        """
        Export metrics in specified format.
        
        Args:
            metrics: Pool metrics to export
            format: Export format ('json', 'csv')
            
        Returns:
            Exported metrics string
        """
        metrics_dict = asdict(metrics)
        
        if format.lower() == 'json':
            return json.dumps(metrics_dict, indent=2)
        elif format.lower() == 'csv':
            headers = ','.join(metrics_dict.keys())
            values = ','.join(str(v) for v in metrics_dict.values())
            return f"{headers}\n{values}"
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def generate_comparison_report(
        self, 
        current_metrics: PoolMetrics, 
        historical_snapshots: List[MetricsSnapshot]
    ) -> str:
        """
        Generate a report comparing current metrics with historical data.
        
        Args:
            current_metrics: Current pool metrics
            historical_snapshots: List of historical snapshots
            
        Returns:
            Comparison report string
        """
        if not historical_snapshots:
            return "No historical data available for comparison."
        
        # Use most recent historical snapshot for comparison
        latest_snapshot = max(historical_snapshots, key=lambda s: s.timestamp)
        diff = MetricsSnapshot.create(current_metrics).diff_from(latest_snapshot)
        
        lines = [
            "=== Metrics Comparison Report ===",
            f"Comparison period: {diff['time_elapsed']:.1f} seconds",
            ""
        ]
        
        # Report significant changes
        for key, value in diff.items():
            if key == 'time_elapsed':
                continue
            
            if isinstance(value, (int, float)) and value != 0:
                direction = "increase" if value > 0 else "decrease"
                lines.append(f"{key}: {direction} of {abs(value)}")
        
        return "\n".join(lines)


class MetricsAggregator:
    """Aggregator for collecting and analyzing metrics over time"""
    
    def __init__(self, max_snapshots: int = 1000):
        self.logger = get_logger("metrics_aggregator")
        self.snapshots: deque = deque(maxlen=max_snapshots)
        self.calculator = MetricsCalculator()
        self._lock = threading.Lock()
    
    def add_snapshot(self, snapshot: MetricsSnapshot):
        """
        Add a metrics snapshot to the aggregator.
        
        Args:
            snapshot: Metrics snapshot to add
        """
        with self._lock:
            self.snapshots.append(snapshot)
    
    def get_snapshots_in_range(
        self, 
        start_time: float, 
        end_time: float
    ) -> List[MetricsSnapshot]:
        """
        Get snapshots within a time range.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            List of snapshots in the time range
        """
        with self._lock:
            return [
                snapshot for snapshot in self.snapshots
                if start_time <= snapshot.timestamp <= end_time
            ]
    
    def get_average_metrics(self) -> PoolMetrics:
        """
        Calculate average metrics across all snapshots.
        
        Returns:
            PoolMetrics with averaged values
        """
        with self._lock:
            if not self.snapshots:
                return PoolMetrics()
            
            # Sum all numeric fields
            total_metrics = {}
            for snapshot in self.snapshots:
                metrics_dict = asdict(snapshot.metrics)
                for key, value in metrics_dict.items():
                    if isinstance(value, (int, float)):
                        total_metrics[key] = total_metrics.get(key, 0) + value
            
            # Calculate averages
            count = len(self.snapshots)
            avg_metrics = {}
            for key, total in total_metrics.items():
                avg_metrics[key] = total / count
            
            return PoolMetrics(**avg_metrics)
    
    def get_peak_metrics(self) -> PoolMetrics:
        """
        Get peak (maximum) values across all snapshots.
        
        Returns:
            PoolMetrics with peak values
        """
        with self._lock:
            if not self.snapshots:
                return PoolMetrics()
            
            # Find maximum values for each field
            peak_metrics = {}
            for snapshot in self.snapshots:
                metrics_dict = asdict(snapshot.metrics)
                for key, value in metrics_dict.items():
                    if isinstance(value, (int, float)):
                        peak_metrics[key] = max(peak_metrics.get(key, value), value)
            
            return PoolMetrics(**peak_metrics)
    
    def analyze_trends(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze trends in metrics over time.
        
        Returns:
            Dictionary of trend analysis results
        """
        with self._lock:
            if len(self.snapshots) < 2:
                return {}
            
            # Sort snapshots by timestamp
            sorted_snapshots = sorted(self.snapshots, key=lambda s: s.timestamp)
            first_snapshot = sorted_snapshots[0]
            last_snapshot = sorted_snapshots[-1]
            
            trends = {}
            first_dict = asdict(first_snapshot.metrics)
            last_dict = asdict(last_snapshot.metrics)
            
            for key in first_dict:
                if isinstance(first_dict[key], (int, float)):
                    first_value = first_dict[key]
                    last_value = last_dict[key]
                    
                    if first_value == last_value:
                        direction = 'stable'
                    elif last_value > first_value:
                        direction = 'increasing'
                    else:
                        direction = 'decreasing'
                    
                    change = last_value - first_value
                    change_rate = (
                        change / first_value if first_value != 0 else 0
                    )
                    
                    trends[key] = {
                        'direction': direction,
                        'change': change,
                        'change_rate': change_rate
                    }
            
            return trends
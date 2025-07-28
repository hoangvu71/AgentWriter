"""
TDD Test Suite for Pool Metrics module.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- PoolMetrics dataclass functionality
- Metrics tracking and calculation
- Metrics reset and state management
- Thread-safe metrics operations
- Metrics aggregation and reporting
- Performance metrics calculation
- Metrics export and serialization
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from dataclasses import asdict
from datetime import datetime, timedelta

from src.database.pool_metrics import (
    PoolMetrics,
    MetricsCalculator,
    MetricsReporter,
    MetricsAggregator,
    MetricsSnapshot
)


class TestPoolMetrics:
    """Test PoolMetrics dataclass functionality"""
    
    def test_pool_metrics_default_values(self):
        """
        RED: Test PoolMetrics default initialization
        Should initialize with zero values and current timestamp
        """
        # Act
        metrics = PoolMetrics()
        
        # Assert
        assert metrics.total_connections == 0
        assert metrics.active_connections == 0
        assert metrics.idle_connections == 0
        assert metrics.connections_created == 0
        assert metrics.connections_closed == 0
        assert metrics.pool_hits == 0
        assert metrics.pool_misses == 0
        assert metrics.health_check_failures == 0
        assert metrics.query_count == 0
        assert metrics.avg_connection_time == 0.0
        assert isinstance(metrics.last_reset, float)
        assert metrics.last_reset > 0
    
    def test_pool_metrics_custom_values(self):
        """
        RED: Test PoolMetrics with custom initialization
        Should allow setting custom values for all metrics
        """
        # Arrange & Act
        metrics = PoolMetrics(
            total_connections=10,
            active_connections=3,
            idle_connections=7,
            connections_created=15,
            connections_closed=5,
            pool_hits=100,
            pool_misses=10,
            health_check_failures=2,
            query_count=500,
            avg_connection_time=0.05
        )
        
        # Assert
        assert metrics.total_connections == 10
        assert metrics.active_connections == 3
        assert metrics.idle_connections == 7
        assert metrics.connections_created == 15
        assert metrics.connections_closed == 5
        assert metrics.pool_hits == 100
        assert metrics.pool_misses == 10
        assert metrics.health_check_failures == 2
        assert metrics.query_count == 500
        assert metrics.avg_connection_time == 0.05
    
    def test_pool_metrics_reset_functionality(self):
        """
        RED: Test PoolMetrics reset functionality
        Should reset counters but preserve current state metrics
        """
        # Arrange
        metrics = PoolMetrics(
            total_connections=10,
            active_connections=3,
            idle_connections=7,
            connections_created=15,
            connections_closed=5,
            pool_hits=100,
            pool_misses=10,
            health_check_failures=2,
            query_count=500,
            avg_connection_time=0.05
        )
        original_reset_time = metrics.last_reset
        
        # Act
        time.sleep(0.01)  # Ensure time difference
        reset_metrics = metrics.reset()
        
        # Assert
        # Counters should be reset
        assert reset_metrics.connections_created == 0
        assert reset_metrics.connections_closed == 0
        assert reset_metrics.pool_hits == 0
        assert reset_metrics.pool_misses == 0
        assert reset_metrics.health_check_failures == 0
        assert reset_metrics.query_count == 0
        
        # Current state should be preserved
        assert reset_metrics.total_connections == 10
        assert reset_metrics.active_connections == 3
        assert reset_metrics.idle_connections == 7
        assert reset_metrics.avg_connection_time == 0.05
        
        # Reset time should be updated
        assert reset_metrics.last_reset > original_reset_time
    
    def test_pool_metrics_immutability_after_creation(self):
        """
        RED: Test PoolMetrics immutability
        Should be immutable after creation (frozen dataclass)
        """
        # Arrange
        metrics = PoolMetrics()
        
        # Act & Assert
        with pytest.raises(AttributeError):
            metrics.total_connections = 5
    
    def test_pool_metrics_to_dict(self):
        """
        RED: Test PoolMetrics conversion to dictionary
        Should convert to dictionary for serialization
        """
        # Arrange
        metrics = PoolMetrics(total_connections=5, pool_hits=20)
        
        # Act
        metrics_dict = asdict(metrics)
        
        # Assert
        assert isinstance(metrics_dict, dict)
        assert metrics_dict['total_connections'] == 5
        assert metrics_dict['pool_hits'] == 20
        assert 'last_reset' in metrics_dict
    
    def test_pool_metrics_equality(self):
        """
        RED: Test PoolMetrics equality comparison
        Should support equality comparison between instances
        """
        # Arrange
        reset_time = time.time()
        metrics1 = PoolMetrics(total_connections=5, pool_hits=20, last_reset=reset_time)
        metrics2 = PoolMetrics(total_connections=5, pool_hits=20, last_reset=reset_time)
        metrics3 = PoolMetrics(total_connections=3, pool_hits=20, last_reset=reset_time)
        
        # Act & Assert
        assert metrics1 == metrics2
        assert metrics1 != metrics3
    
    def test_pool_metrics_thread_safe_operations(self):
        """
        RED: Test PoolMetrics thread safety for atomic operations
        Should handle concurrent access safely
        """
        # Arrange
        metrics = PoolMetrics()
        results = []
        errors = []
        
        def update_metrics(thread_id):
            try:
                for i in range(100):
                    # Simulate metrics update
                    new_metrics = metrics.increment_pool_hits()
                    results.append((thread_id, new_metrics.pool_hits))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Act
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_metrics, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(errors) == 0, f"Thread errors: {errors}"
        assert len(results) > 0


class TestMetricsCalculator:
    """Test MetricsCalculator functionality"""
    
    def test_metrics_calculator_initialization(self):
        """
        RED: Test MetricsCalculator initialization
        Should create calculator instance
        """
        # Act
        calculator = MetricsCalculator()
        
        # Assert
        assert calculator is not None
        assert hasattr(calculator, 'calculate_hit_ratio')
        assert hasattr(calculator, 'calculate_utilization')
        assert hasattr(calculator, 'calculate_efficiency')
    
    def test_metrics_calculator_hit_ratio_calculation(self):
        """
        RED: Test hit ratio calculation
        Should calculate pool hit ratio correctly
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(pool_hits=80, pool_misses=20)
        
        # Act
        hit_ratio = calculator.calculate_hit_ratio(metrics)
        
        # Assert
        assert hit_ratio == 0.8  # 80/(80+20) = 0.8
    
    def test_metrics_calculator_hit_ratio_no_requests(self):
        """
        RED: Test hit ratio calculation with no requests
        Should handle zero requests gracefully
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(pool_hits=0, pool_misses=0)
        
        # Act
        hit_ratio = calculator.calculate_hit_ratio(metrics)
        
        # Assert
        assert hit_ratio == 0.0
    
    def test_metrics_calculator_utilization_calculation(self):
        """
        RED: Test pool utilization calculation
        Should calculate connection utilization correctly
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(active_connections=6, total_connections=10)
        
        # Act
        utilization = calculator.calculate_utilization(metrics)
        
        # Assert
        assert utilization == 0.6  # 6/10 = 0.6
    
    def test_metrics_calculator_utilization_no_connections(self):
        """
        RED: Test utilization calculation with no connections
        Should handle zero connections gracefully
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(active_connections=0, total_connections=0)
        
        # Act
        utilization = calculator.calculate_utilization(metrics)
        
        # Assert
        assert utilization == 0.0
    
    def test_metrics_calculator_efficiency_calculation(self):
        """
        RED: Test connection efficiency calculation
        Should calculate connection efficiency based on usage
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(
            connections_created=10,
            connections_closed=2,
            query_count=1000
        )
        
        # Act
        efficiency = calculator.calculate_efficiency(metrics)
        
        # Assert
        # High query count with low churn should indicate good efficiency
        assert efficiency > 0.0
    
    def test_metrics_calculator_connection_turnover_rate(self):
        """
        RED: Test connection turnover rate calculation
        Should calculate how frequently connections are recycled
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(
            connections_created=20,
            connections_closed=15,
            last_reset=time.time() - 3600  # 1 hour ago
        )
        
        # Act
        turnover_rate = calculator.calculate_turnover_rate(metrics)
        
        # Assert
        assert turnover_rate > 0.0
        assert isinstance(turnover_rate, float)
    
    def test_metrics_calculator_average_connection_lifetime(self):
        """
        RED: Test average connection lifetime calculation
        Should calculate average time connections stay active
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(
            connections_closed=10,
            total_connection_time=1000.0  # Total seconds all connections were alive
        )
        
        # Act
        avg_lifetime = calculator.calculate_average_lifetime(metrics)
        
        # Assert
        assert avg_lifetime == 100.0  # 1000/10 = 100 seconds
    
    def test_metrics_calculator_performance_score(self):
        """
        RED: Test overall performance score calculation
        Should calculate composite performance score
        """
        # Arrange
        calculator = MetricsCalculator()
        metrics = PoolMetrics(
            pool_hits=90,
            pool_misses=10,
            active_connections=5,
            total_connections=10,
            health_check_failures=1,
            query_count=1000
        )
        
        # Act
        score = calculator.calculate_performance_score(metrics)
        
        # Assert
        assert 0.0 <= score <= 1.0  # Score should be normalized between 0 and 1
        assert isinstance(score, float)


class TestMetricsSnapshot:
    """Test MetricsSnapshot functionality"""
    
    def test_metrics_snapshot_creation(self):
        """
        RED: Test MetricsSnapshot creation
        Should create snapshot with timestamp and metrics
        """
        # Arrange
        metrics = PoolMetrics(total_connections=5, pool_hits=100)
        
        # Act
        snapshot = MetricsSnapshot.create(metrics)
        
        # Assert
        assert isinstance(snapshot, MetricsSnapshot)
        assert snapshot.metrics == metrics
        assert isinstance(snapshot.timestamp, float)
        assert snapshot.timestamp > 0
    
    def test_metrics_snapshot_time_since_creation(self):
        """
        RED: Test MetricsSnapshot time calculation
        Should calculate time elapsed since snapshot creation
        """
        # Arrange
        metrics = PoolMetrics()
        snapshot = MetricsSnapshot.create(metrics)
        
        # Act
        time.sleep(0.01)  # Small delay
        elapsed = snapshot.time_since_creation()
        
        # Assert
        assert elapsed > 0.0
        assert elapsed < 1.0  # Should be very small
    
    def test_metrics_snapshot_comparison(self):
        """
        RED: Test MetricsSnapshot comparison
        Should compare snapshots and calculate differences
        """
        # Arrange
        metrics1 = PoolMetrics(pool_hits=50, query_count=100)
        metrics2 = PoolMetrics(pool_hits=75, query_count=150)
        snapshot1 = MetricsSnapshot.create(metrics1)
        time.sleep(0.01)
        snapshot2 = MetricsSnapshot.create(metrics2)
        
        # Act
        diff = snapshot2.diff_from(snapshot1)
        
        # Assert
        assert diff['pool_hits'] == 25  # 75 - 50
        assert diff['query_count'] == 50  # 150 - 100
        assert 'time_elapsed' in diff
    
    def test_metrics_snapshot_serialization(self):
        """
        RED: Test MetricsSnapshot serialization
        Should convert to dictionary for storage/transmission
        """
        # Arrange
        metrics = PoolMetrics(total_connections=5)
        snapshot = MetricsSnapshot.create(metrics)
        
        # Act
        snapshot_dict = snapshot.to_dict()
        
        # Assert
        assert isinstance(snapshot_dict, dict)
        assert 'timestamp' in snapshot_dict
        assert 'metrics' in snapshot_dict
        assert snapshot_dict['metrics']['total_connections'] == 5


class TestMetricsReporter:
    """Test MetricsReporter functionality"""
    
    def test_metrics_reporter_initialization(self):
        """
        RED: Test MetricsReporter initialization
        Should create reporter instance with optional configuration
        """
        # Act
        reporter = MetricsReporter()
        
        # Assert
        assert reporter is not None
        assert hasattr(reporter, 'generate_report')
        assert hasattr(reporter, 'format_metrics')
        assert hasattr(reporter, 'export_metrics')
    
    def test_metrics_reporter_generate_basic_report(self):
        """
        RED: Test basic metrics report generation
        Should generate human-readable metrics report
        """
        # Arrange
        reporter = MetricsReporter()
        metrics = PoolMetrics(
            total_connections=10,
            active_connections=6,
            pool_hits=80,
            pool_misses=20,
            query_count=1000
        )
        
        # Act
        report = reporter.generate_report(metrics)
        
        # Assert
        assert isinstance(report, str)
        assert '10' in report  # total_connections
        assert '6' in report   # active_connections
        assert 'hit' in report.lower()
        assert len(report) > 100  # Should be substantial report
    
    def test_metrics_reporter_format_with_calculations(self):
        """
        RED: Test metrics formatting with calculated values
        Should include calculated metrics in report
        """
        # Arrange
        reporter = MetricsReporter()
        metrics = PoolMetrics(
            pool_hits=90,
            pool_misses=10,
            active_connections=7,
            total_connections=10
        )
        
        # Act
        report = reporter.generate_report(metrics, include_calculations=True)
        
        # Assert
        assert isinstance(report, str)
        assert 'hit ratio' in report.lower() or 'hit rate' in report.lower()
        assert 'utilization' in report.lower()
        # Should include percentages
        assert '%' in report
    
    def test_metrics_reporter_export_json_format(self):
        """
        RED: Test metrics export in JSON format
        Should export metrics as JSON string
        """
        # Arrange
        reporter = MetricsReporter()
        metrics = PoolMetrics(total_connections=5, pool_hits=100)
        
        # Act
        json_export = reporter.export_metrics(metrics, format='json')
        
        # Assert
        assert isinstance(json_export, str)
        assert '{' in json_export  # JSON structure
        assert 'total_connections' in json_export
        assert '5' in json_export
    
    def test_metrics_reporter_export_csv_format(self):
        """
        RED: Test metrics export in CSV format
        Should export metrics as CSV string
        """
        # Arrange
        reporter = MetricsReporter()
        metrics = PoolMetrics(total_connections=5, pool_hits=100)
        
        # Act
        csv_export = reporter.export_metrics(metrics, format='csv')
        
        # Assert
        assert isinstance(csv_export, str)
        assert ',' in csv_export  # CSV delimiter
        assert 'total_connections' in csv_export
    
    def test_metrics_reporter_custom_format(self):
        """
        RED: Test metrics reporter with custom formatting
        Should support custom formatting templates
        """
        # Arrange
        reporter = MetricsReporter()
        metrics = PoolMetrics(total_connections=5, active_connections=3)
        template = "Pool has {total_connections} total, {active_connections} active"
        
        # Act
        formatted = reporter.format_metrics(metrics, template)
        
        # Assert
        assert formatted == "Pool has 5 total, 3 active"
    
    def test_metrics_reporter_historical_comparison(self):
        """
        RED: Test metrics reporter with historical data
        Should compare current metrics with historical snapshots
        """
        # Arrange
        reporter = MetricsReporter()
        old_metrics = PoolMetrics(pool_hits=50, query_count=100)
        new_metrics = PoolMetrics(pool_hits=75, query_count=150)
        historical_snapshots = [MetricsSnapshot.create(old_metrics)]
        
        # Act
        report = reporter.generate_comparison_report(new_metrics, historical_snapshots)
        
        # Assert
        assert isinstance(report, str)
        assert 'increase' in report.lower() or 'decrease' in report.lower()
        assert '25' in report  # difference in pool_hits


class TestMetricsAggregator:
    """Test MetricsAggregator functionality"""
    
    def test_metrics_aggregator_initialization(self):
        """
        RED: Test MetricsAggregator initialization
        Should create aggregator instance
        """
        # Act
        aggregator = MetricsAggregator()
        
        # Assert
        assert aggregator is not None
        assert hasattr(aggregator, 'add_snapshot')
        assert hasattr(aggregator, 'get_average_metrics')
        assert hasattr(aggregator, 'get_peak_metrics')
    
    def test_metrics_aggregator_add_snapshot(self):
        """
        RED: Test adding snapshots to aggregator
        Should store snapshots for aggregation
        """
        # Arrange
        aggregator = MetricsAggregator()
        metrics = PoolMetrics(total_connections=5)
        snapshot = MetricsSnapshot.create(metrics)
        
        # Act
        aggregator.add_snapshot(snapshot)
        
        # Assert
        assert len(aggregator.snapshots) == 1
        assert aggregator.snapshots[0] == snapshot
    
    def test_metrics_aggregator_average_calculation(self):
        """
        RED: Test average metrics calculation
        Should calculate average across multiple snapshots
        """
        # Arrange
        aggregator = MetricsAggregator()
        
        # Add multiple snapshots
        snapshots = [
            MetricsSnapshot.create(PoolMetrics(pool_hits=10, query_count=100)),
            MetricsSnapshot.create(PoolMetrics(pool_hits=20, query_count=200)),
            MetricsSnapshot.create(PoolMetrics(pool_hits=30, query_count=300))
        ]
        
        for snapshot in snapshots:
            aggregator.add_snapshot(snapshot)
        
        # Act
        avg_metrics = aggregator.get_average_metrics()
        
        # Assert
        assert avg_metrics.pool_hits == 20.0  # (10+20+30)/3
        assert avg_metrics.query_count == 200.0  # (100+200+300)/3
    
    def test_metrics_aggregator_peak_metrics(self):
        """
        RED: Test peak metrics identification
        Should identify peak values across snapshots
        """
        # Arrange
        aggregator = MetricsAggregator()
        
        snapshots = [
            MetricsSnapshot.create(PoolMetrics(pool_hits=10, total_connections=5)),
            MetricsSnapshot.create(PoolMetrics(pool_hits=30, total_connections=8)),
            MetricsSnapshot.create(PoolMetrics(pool_hits=20, total_connections=6))
        ]
        
        for snapshot in snapshots:
            aggregator.add_snapshot(snapshot)
        
        # Act
        peak_metrics = aggregator.get_peak_metrics()
        
        # Assert
        assert peak_metrics.pool_hits == 30  # Maximum pool_hits
        assert peak_metrics.total_connections == 8  # Maximum total_connections
    
    def test_metrics_aggregator_time_range_filtering(self):
        """
        RED: Test filtering snapshots by time range
        Should filter snapshots within specified time range
        """
        # Arrange
        aggregator = MetricsAggregator()
        current_time = time.time()
        
        # Create snapshots with different timestamps
        old_snapshot = MetricsSnapshot(
            metrics=PoolMetrics(pool_hits=10),
            timestamp=current_time - 3600  # 1 hour ago
        )
        
        recent_snapshot = MetricsSnapshot(
            metrics=PoolMetrics(pool_hits=20),
            timestamp=current_time  # Current timestamp
        )
        
        aggregator.add_snapshot(old_snapshot)
        aggregator.add_snapshot(recent_snapshot)
        
        # Act
        recent_snapshots = aggregator.get_snapshots_in_range(
            start_time=current_time - 1800,  # 30 minutes ago
            end_time=current_time + 60  # Small buffer for current time
        )
        
        # Assert
        assert len(recent_snapshots) == 1
        assert recent_snapshots[0] == recent_snapshot
    
    def test_metrics_aggregator_trend_analysis(self):
        """
        RED: Test trend analysis across snapshots
        Should identify trends in metrics over time
        """
        # Arrange
        aggregator = MetricsAggregator()
        base_time = time.time()
        
        # Create snapshots showing increasing trend
        for i in range(5):
            metrics = PoolMetrics(pool_hits=i * 10, query_count=i * 100)
            snapshot = MetricsSnapshot(
                metrics=metrics,
                timestamp=base_time + i  # Sequential timestamps
            )
            aggregator.add_snapshot(snapshot)
        
        # Act
        trends = aggregator.analyze_trends()
        
        # Assert
        assert 'pool_hits' in trends
        assert trends['pool_hits']['direction'] == 'increasing'
        assert trends['query_count']['direction'] == 'increasing'
    
    def test_metrics_aggregator_cleanup_old_snapshots(self):
        """
        RED: Test cleanup of old snapshots
        Should remove snapshots older than specified age
        """
        # Arrange
        aggregator = MetricsAggregator(max_snapshots=2)
        
        # Add more snapshots than the limit
        for i in range(5):
            metrics = PoolMetrics(pool_hits=i * 10)
            snapshot = MetricsSnapshot.create(metrics)
            aggregator.add_snapshot(snapshot)
        
        # Act
        # Cleanup should happen automatically due to max_snapshots limit
        
        # Assert
        assert len(aggregator.snapshots) <= 2  # Should be limited to max_snapshots
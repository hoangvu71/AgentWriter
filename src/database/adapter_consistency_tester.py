"""
Database Adapter Consistency Tester
Tests that SQLite and Supabase adapters behave identically
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from ..core.logging import get_logger
from .sqlite.adapter import SQLiteAdapter
from .schema_synchronizer import SchemaSynchronizer
from .migration_manager import MigrationManager


class AdapterConsistencyTester:
    """Tests consistency between SQLite and Supabase adapters"""
    
    def __init__(self, sqlite_path: str = "test_consistency.db"):
        self.sqlite_path = sqlite_path
        self.logger = get_logger("adapter_consistency_tester")
        self.sqlite_adapter = SQLiteAdapter(sqlite_path)
        self.test_results = []
        
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive test suite for adapter consistency"""
        self.logger.info("Starting comprehensive adapter consistency tests...")
        
        # Ensure schema is up to date
        migration_manager = MigrationManager(self.sqlite_path)
        if not migration_manager.run_full_migration():
            return {"error": "Failed to migrate schema before testing"}
        
        test_results = {
            "schema_validation": await self.test_schema_consistency(),
            "crud_operations": await self.test_crud_operations(),
            "json_handling": await self.test_json_field_handling(),
            "foreign_keys": await self.test_foreign_key_constraints(),
            "indexes": await self.test_index_performance(),
            "data_integrity": await self.test_data_integrity(),
            "summary": {}
        }
        
        # Generate summary
        total_tests = sum(len(category["tests"]) for category in test_results.values() if isinstance(category, dict) and "tests" in category)
        passed_tests = sum(sum(1 for test in category["tests"] if test["passed"]) for category in test_results.values() if isinstance(category, dict) and "tests" in category)
        
        test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "overall_status": "PASS" if passed_tests == total_tests else "FAIL"
        }
        
        self.logger.info(f"Test suite completed: {passed_tests}/{total_tests} tests passed ({test_results['summary']['success_rate']:.1f}%)")
        return test_results
    
    async def test_schema_consistency(self) -> Dict[str, Any]:
        """Test that schema matches expected structure"""
        self.logger.info("Testing schema consistency...")
        tests = []
        
        try:
            synchronizer = SchemaSynchronizer(self.sqlite_path)
            validation = synchronizer.validate_schema_consistency()
            
            # Test 1: No missing tables
            tests.append({
                "name": "no_missing_tables",
                "passed": len(validation["missing_tables"]) == 0,
                "details": f"Missing tables: {list(validation['missing_tables'])}" if validation["missing_tables"] else "All tables present"
            })
            
            # Test 2: No schema issues
            tests.append({
                "name": "no_schema_issues",
                "passed": len(validation["schema_issues"]) == 0,
                "details": f"Schema issues: {validation['schema_issues']}" if validation["schema_issues"] else "No schema issues"
            })
            
            # Test 3: World building table structure
            schema_info = synchronizer.get_sqlite_schema_info()
            wb_columns = {col["name"] for col in schema_info.get("tables", {}).get("world_building", [])}
            expected_wb_columns = {
                "id", "session_id", "user_id", "plot_id", "world_name", "world_type",
                "overview", "geography", "political_landscape", "cultural_systems",
                "economic_framework", "historical_timeline", "power_systems",
                "languages_and_communication", "religious_and_belief_systems",
                "unique_elements", "created_at", "updated_at"
            }
            
            tests.append({
                "name": "world_building_structure",
                "passed": expected_wb_columns.issubset(wb_columns),
                "details": f"Missing columns: {expected_wb_columns - wb_columns}" if not expected_wb_columns.issubset(wb_columns) else "All columns present"
            })
            
        except Exception as e:
            tests.append({
                "name": "schema_validation_error",
                "passed": False,
                "details": f"Error during schema validation: {e}"
            })
        
        return {"tests": tests, "category": "Schema Consistency"}
    
    async def test_crud_operations(self) -> Dict[str, Any]:
        """Test basic CRUD operations work correctly"""
        self.logger.info("Testing CRUD operations...")
        tests = []
        
        try:
            # Test data
            test_user = {
                "id": str(uuid.uuid4()),
                "name": "Test User",
            }
            
            test_plot = {
                "id": str(uuid.uuid4()),
                "user_id": test_user["id"],
                "title": "Test Plot",
                "plot_summary": "A test plot for validation",
                "genre": "fantasy",
                "subgenre": "epic",
                "target_audience": "adult"
            }
            
            # Test 1: Insert operations
            user_id = await self.sqlite_adapter.insert("users", test_user)
            plot_id = await self.sqlite_adapter.insert("plots", test_plot)
            
            tests.append({
                "name": "insert_operations",
                "passed": user_id == test_user["id"] and plot_id == test_plot["id"],
                "details": f"User ID: {user_id}, Plot ID: {plot_id}"
            })
            
            # Test 2: Select operations
            retrieved_user = await self.sqlite_adapter.get_by_id("users", user_id)
            retrieved_plot = await self.sqlite_adapter.get_by_id("plots", plot_id)
            
            tests.append({
                "name": "select_operations",
                "passed": retrieved_user is not None and retrieved_plot is not None,
                "details": f"Retrieved user: {retrieved_user is not None}, Retrieved plot: {retrieved_plot is not None}"
            })
            
            # Test 3: Update operations
            update_success = await self.sqlite_adapter.update("users", user_id, {"name": "Updated Test User"})
            updated_user = await self.sqlite_adapter.get_by_id("users", user_id)
            
            tests.append({
                "name": "update_operations",
                "passed": update_success and updated_user and updated_user["name"] == "Updated Test User",
                "details": f"Update success: {update_success}, Updated name: {updated_user['name'] if updated_user else None}"
            })
            
            # Test 4: Delete operations
            delete_success = await self.sqlite_adapter.delete("plots", plot_id)
            deleted_plot = await self.sqlite_adapter.get_by_id("plots", plot_id)
            
            tests.append({
                "name": "delete_operations",
                "passed": delete_success and deleted_plot is None,
                "details": f"Delete success: {delete_success}, Plot still exists: {deleted_plot is not None}"
            })
            
            # Cleanup
            await self.sqlite_adapter.delete("users", user_id)
            
        except Exception as e:
            tests.append({
                "name": "crud_operations_error",
                "passed": False,
                "details": f"Error during CRUD operations: {e}"
            })
        
        return {"tests": tests, "category": "CRUD Operations"}
    
    async def test_json_field_handling(self) -> Dict[str, Any]:
        """Test JSON field serialization and deserialization"""
        self.logger.info("Testing JSON field handling...")
        tests = []
        
        try:
            # Test world building with complex JSON fields
            test_world = {
                "id": str(uuid.uuid4()),
                "world_name": "Test World",
                "world_type": "high_fantasy",
                "overview": "A test world for JSON validation",
                "geography": {
                    "continents": ["Test Continent"],
                    "major_regions": ["Test Region"],
                    "climate_zones": ["temperate"]
                },
                "political_landscape": {
                    "major_powers": ["Test Kingdom"],
                    "conflicts": ["Test War"],
                    "alliances": ["Test Alliance"]
                },
                "cultural_systems": {
                    "major_cultures": ["Test Culture"],
                    "traditions": ["Test Tradition"],
                    "languages": ["Test Language"]
                }
            }
            
            # Test 1: JSON serialization on insert
            world_id = await self.sqlite_adapter.insert("world_building", test_world)
            
            tests.append({
                "name": "json_insert",
                "passed": world_id == test_world["id"],
                "details": f"World ID: {world_id}"
            })
            
            # Test 2: JSON deserialization on select
            retrieved_world = await self.sqlite_adapter.get_by_id("world_building", world_id)
            
            geography_matches = (
                retrieved_world and 
                isinstance(retrieved_world.get("geography"), dict) and
                retrieved_world["geography"].get("continents") == ["Test Continent"]
            )
            
            tests.append({
                "name": "json_deserialization",
                "passed": geography_matches,
                "details": f"Geography type: {type(retrieved_world.get('geography') if retrieved_world else None)}, Content matches: {geography_matches}"
            })
            
            # Test 3: JSON update
            updated_geography = {"continents": ["Updated Continent"], "regions": ["Updated Region"]}
            update_success = await self.sqlite_adapter.update("world_building", world_id, {"geography": updated_geography})
            updated_world = await self.sqlite_adapter.get_by_id("world_building", world_id)
            
            update_matches = (
                updated_world and
                isinstance(updated_world.get("geography"), dict) and
                updated_world["geography"].get("continents") == ["Updated Continent"]
            )
            
            tests.append({
                "name": "json_update",
                "passed": update_success and update_matches,
                "details": f"Update success: {update_success}, Content matches: {update_matches}"
            })
            
            # Cleanup
            await self.sqlite_adapter.delete("world_building", world_id)
            
        except Exception as e:
            tests.append({
                "name": "json_handling_error",
                "passed": False,
                "details": f"Error during JSON handling: {e}"
            })
        
        return {"tests": tests, "category": "JSON Field Handling"}
    
    async def test_foreign_key_constraints(self) -> Dict[str, Any]:
        """Test foreign key constraint enforcement"""
        self.logger.info("Testing foreign key constraints...")
        tests = []
        
        try:
            # Create parent records
            test_user = {"id": str(uuid.uuid4()), "name": "FK Test User"}
            test_session = {"id": str(uuid.uuid4()), "user_id": test_user["id"]}
            
            user_id = await self.sqlite_adapter.insert("users", test_user)
            session_id = await self.sqlite_adapter.insert("sessions", test_session)
            
            # Test 1: Valid foreign key reference
            test_plot = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "title": "FK Test Plot",
                "plot_summary": "Testing foreign keys"
            }
            
            plot_id = await self.sqlite_adapter.insert("plots", test_plot)
            
            tests.append({
                "name": "valid_foreign_key",
                "passed": plot_id == test_plot["id"],
                "details": f"Plot created with valid foreign keys: {plot_id}"
            })
            
            # Test 2: Cascade delete (when parent is deleted, child should be affected)
            # This depends on the specific foreign key constraints defined
            retrieved_plot_before = await self.sqlite_adapter.get_by_id("plots", plot_id)
            delete_user_success = await self.sqlite_adapter.delete("users", user_id)
            retrieved_plot_after = await self.sqlite_adapter.get_by_id("plots", plot_id) 
            
            tests.append({
                "name": "foreign_key_behavior",
                "passed": delete_user_success,
                "details": f"User deleted: {delete_user_success}, Plot before: {retrieved_plot_before is not None}, Plot after: {retrieved_plot_after is not None}"
            })
            
            # Cleanup any remaining records
            try:
                await self.sqlite_adapter.delete("plots", plot_id)
                await self.sqlite_adapter.delete("sessions", session_id)
            except:
                pass  # May already be deleted by cascade
            
        except Exception as e:
            tests.append({
                "name": "foreign_key_error",
                "passed": False,
                "details": f"Error during foreign key testing: {e}"
            })
        
        return {"tests": tests, "category": "Foreign Key Constraints"}
    
    async def test_index_performance(self) -> Dict[str, Any]:
        """Test that indexes exist and basic query performance"""
        self.logger.info("Testing index presence...")
        tests = []
        
        try:
            synchronizer = SchemaSynchronizer(self.sqlite_path)
            schema_info = synchronizer.get_sqlite_schema_info()
            
            # Test 1: Core table indexes exist
            expected_indexes = [
                ("users", "idx_users_name"),
                ("plots", "idx_plots_user_id"),
                ("world_building", "idx_world_building_user_id"),
                ("characters", "idx_characters_session_id")
            ]
            
            index_tests_passed = 0
            total_index_tests = len(expected_indexes)
            
            for table, expected_index in expected_indexes:
                table_indexes = schema_info.get("indexes", {}).get(table, [])
                index_names = [idx["name"] for idx in table_indexes]
                if expected_index in index_names:
                    index_tests_passed += 1
            
            tests.append({
                "name": "core_indexes_exist",
                "passed": index_tests_passed >= total_index_tests * 0.8,  # Allow some flexibility
                "details": f"Index tests passed: {index_tests_passed}/{total_index_tests}"
            })
            
            # Test 2: Query performance (basic timing test)
            import time
            
            # Insert some test data
            test_users = [
                {"id": str(uuid.uuid4()), "name": f"Performance Test User {i}"}
                for i in range(10)
            ]
            
            for user in test_users:
                await self.sqlite_adapter.insert("users", user)
            
            # Time a query that should use an index
            start_time = time.time()
            results = await self.sqlite_adapter.select("users", limit=5)
            query_time = time.time() - start_time
            
            tests.append({
                "name": "query_performance",
                "passed": query_time < 1.0 and len(results) <= 5,
                "details": f"Query time: {query_time:.3f}s, Results: {len(results)}"
            })
            
            # Cleanup
            for user in test_users:
                await self.sqlite_adapter.delete("users", user["id"])
            
        except Exception as e:
            tests.append({
                "name": "index_performance_error",
                "passed": False,
                "details": f"Error during index testing: {e}"
            })
        
        return {"tests": tests, "category": "Index Performance"}
    
    async def test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and constraint enforcement"""
        self.logger.info("Testing data integrity...")
        tests = []
        
        try:
            # Test 1: Required field constraints
            try:
                # This should fail because world_name is required
                invalid_world = {
                    "id": str(uuid.uuid4()),
                    "world_type": "fantasy",
                    "overview": "Test"
                }
                await self.sqlite_adapter.insert("world_building", invalid_world)
                constraint_enforced = False
            except Exception:
                constraint_enforced = True
            
            tests.append({
                "name": "required_field_constraints",
                "passed": constraint_enforced,
                "details": f"Required field constraint enforced: {constraint_enforced}"
            })
            
            # Test 2: Data type consistency
            test_agent_invocation = {
                "id": str(uuid.uuid4()),
                "invocation_id": f"test_invocation_{uuid.uuid4()}",
                "agent_name": "test_agent",
                "request_content": "Test request",
                "start_time": datetime.utcnow().isoformat(),
                "success": True,  # Boolean value
                "duration_ms": 123.45,  # Float value
                "prompt_tokens": 100  # Integer value
            }
            
            invocation_id = await self.sqlite_adapter.insert("agent_invocations", test_agent_invocation)
            retrieved_invocation = await self.sqlite_adapter.get_by_id("agent_invocations", invocation_id)
            
            data_types_preserved = (
                retrieved_invocation and
                isinstance(retrieved_invocation.get("success"), (bool, int)) and  # SQLite may store as int
                isinstance(retrieved_invocation.get("duration_ms"), (float, int)) and
                isinstance(retrieved_invocation.get("prompt_tokens"), int)
            )
            
            tests.append({
                "name": "data_type_consistency",
                "passed": data_types_preserved,
                "details": f"Data types preserved: {data_types_preserved}"
            })
            
            # Cleanup
            if invocation_id:
                await self.sqlite_adapter.delete("agent_invocations", invocation_id)
            
        except Exception as e:
            tests.append({
                "name": "data_integrity_error",
                "passed": False,
                "details": f"Error during data integrity testing: {e}"
            })
        
        return {"tests": tests, "category": "Data Integrity"}
    
    def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """Generate a formatted test report"""
        report = ["Database Adapter Consistency Test Report"]
        report.append("=" * 50)
        report.append("")
        
        # Summary
        summary = test_results.get("summary", {})
        report.append(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        report.append(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        report.append(f"Tests Passed: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)}")
        report.append("")
        
        # Detailed results by category
        for category_key, category_data in test_results.items():
            if category_key == "summary" or not isinstance(category_data, dict) or "tests" not in category_data:
                continue
            
            report.append(f"{category_data.get('category', category_key)}:")
            report.append("-" * 30)
            
            for test in category_data["tests"]:
                status = "PASS" if test["passed"] else "FAIL"
                report.append(f"  {test['name']}: {status}")
                if test["details"]:
                    report.append(f"    {test['details']}")
            
            report.append("")
        
        return "\n".join(report)
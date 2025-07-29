"""
E2E test runner for AgentWriter.
Orchestrates all E2E test suites and generates comprehensive reports.
"""

import asyncio
import json
import time
import os
from typing import Dict, Any, List
from datetime import datetime

# Import test suites
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_core_functionality import TestCoreFunctionality
from test_agent_workflows import TestAgentWorkflows
from test_browser_interactions import TestBrowserInteractions


class E2ETestRunner:
    """Comprehensive E2E test runner."""
    
    def __init__(self, environment: str = "local", output_dir: str = "test-results"):
        self.environment = environment
        self.output_dir = output_dir
        self.start_time = None
        self.results = {
            "test_run_id": f"e2e_{int(time.time())}",
            "environment": environment,
            "start_time": None,
            "end_time": None,
            "duration_ms": 0,
            "summary": {
                "total_suites": 0,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "partial": 0,
                "skipped": 0
            },
            "suites": []
        }
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    async def run_all_suites(self) -> Dict[str, Any]:
        """Run all E2E test suites."""
        print("🚀 Starting AgentWriter E2E Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        self.results["start_time"] = datetime.now().isoformat()
        
        # Initialize test suites
        test_suites = [
            ("Core Functionality", TestCoreFunctionality(self.environment)),
            ("Agent Workflows", TestAgentWorkflows(self.environment)),
            ("Browser Interactions", TestBrowserInteractions(self.environment))
        ]
        
        self.results["summary"]["total_suites"] = len(test_suites)
        
        # Run each test suite
        for suite_name, suite_instance in test_suites:
            print(f"\n🧪 Running {suite_name} Test Suite...")
            print("-" * 40)
            
            try:
                suite_results = await suite_instance.run_all_tests()
                self.results["suites"].append(suite_results)
                
                # Update summary
                self.results["summary"]["total_tests"] += suite_results.get("total_tests", 0)
                self.results["summary"]["passed"] += suite_results.get("passed", 0)
                self.results["summary"]["failed"] += suite_results.get("failed", 0)
                self.results["summary"]["partial"] += suite_results.get("partial", 0)
                self.results["summary"]["skipped"] += suite_results.get("skipped", 0)
                
                print(f"✅ {suite_name} Suite Completed")
                
            except Exception as e:
                print(f"❌ {suite_name} Suite Failed: {str(e)}")
                error_suite = {
                    "suite_name": suite_name,
                    "status": "error",
                    "error": str(e),
                    "tests": []
                }
                self.results["suites"].append(error_suite)
                self.results["summary"]["failed"] += 1
        
        # Finalize results
        end_time = time.time()
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration_ms"] = int((end_time - self.start_time) * 1000)
        
        return self.results
    
    def generate_summary_report(self) -> str:
        """Generate human-readable summary report."""
        summary = self.results["summary"]
        duration_sec = self.results["duration_ms"] / 1000
        
        report = f"""
🎯 AgentWriter E2E Test Results Summary
{'=' * 50}

Environment: {self.results['environment']}
Duration: {duration_sec:.1f} seconds
Test Run ID: {self.results['test_run_id']}

📊 Overall Results:
   Total Suites: {summary['total_suites']}
   Total Tests: {summary['total_tests']}
   ✅ Passed: {summary['passed']}
   ⚠️ Partial: {summary['partial']}
   ⏭️ Skipped: {summary['skipped']}
   ❌ Failed: {summary['failed']}

Success Rate: {(summary['passed'] / max(summary['total_tests'], 1)) * 100:.1f}%

🔍 Suite Breakdown:
"""
        
        for suite in self.results["suites"]:
            suite_name = suite.get("suite_name", "Unknown Suite")
            if "total_tests" in suite:
                passed = suite.get("passed", 0)
                failed = suite.get("failed", 0)
                partial = suite.get("partial", 0)
                skipped = suite.get("skipped", 0)
                total = suite.get("total_tests", 0)
                
                status_icon = "✅" if failed == 0 else "❌" if passed == 0 else "⚠️"
                report += f"   {status_icon} {suite_name}: {passed}/{total} passed"
                
                if partial > 0:
                    report += f", {partial} partial"
                if skipped > 0:
                    report += f", {skipped} skipped"
                if failed > 0:
                    report += f", {failed} failed"
                report += "\n"
            else:
                report += f"   ❌ {suite_name}: Error during execution\n"
        
        # Performance insights
        report += f"\n⚡ Performance Insights:\n"
        
        total_performance_data = []
        for suite in self.results["suites"]:
            for test in suite.get("tests", []):
                if "performance" in test:
                    total_performance_data.extend(test["performance"].values())
        
        if total_performance_data:
            avg_response = sum(total_performance_data) / len(total_performance_data)
            max_response = max(total_performance_data)
            report += f"   Average Response Time: {avg_response:.0f}ms\n"
            report += f"   Maximum Response Time: {max_response:.0f}ms\n"
        
        # Key findings
        report += f"\n🔑 Key Findings:\n"
        
        if summary["failed"] == 0:
            report += "   🎉 All tests passed! AgentWriter is fully functional.\n"
        else:
            report += f"   ⚠️ {summary['failed']} test(s) failed - review details for issues.\n"
        
        if summary["partial"] > 0:
            report += f"   ℹ️ {summary['partial']} test(s) partially successful - may need attention.\n"
        
        return report
    
    def generate_detailed_report(self) -> str:
        """Generate detailed test report."""
        report = "# AgentWriter E2E Test Detailed Report\n\n"
        report += f"**Test Run ID:** {self.results['test_run_id']}\n"
        report += f"**Environment:** {self.results['environment']}\n"
        report += f"**Start Time:** {self.results['start_time']}\n"
        report += f"**Duration:** {self.results['duration_ms']}ms\n\n"
        
        for suite in self.results["suites"]:
            suite_name = suite.get("suite_name", "Unknown Suite")
            report += f"## {suite_name}\n\n"
            
            for test in suite.get("tests", []):
                test_name = test.get("test_name", "Unknown Test")
                status = test.get("status", "unknown")
                
                status_emoji = {
                    "passed": "✅",
                    "failed": "❌", 
                    "partial": "⚠️",
                    "skipped": "⏭️"
                }.get(status, "❓")
                
                report += f"### {status_emoji} {test_name}\n\n"
                report += f"**Status:** {status.upper()}\n\n"
                
                # Details
                if "details" in test and test["details"]:
                    report += "**Details:**\n"
                    for detail in test["details"]:
                        report += f"- {detail}\n"
                    report += "\n"
                
                # Performance
                if "performance" in test and test["performance"]:
                    report += "**Performance:**\n"
                    for metric, value in test["performance"].items():
                        report += f"- {metric}: {value:.0f}ms\n"
                    report += "\n"
                
                # Artifacts
                if "artifacts" in test and test["artifacts"]:
                    report += "**Artifacts:**\n"
                    for artifact in test["artifacts"]:
                        report += f"- {artifact.get('type', 'Unknown')}: {str(artifact)[:100]}...\n"
                    report += "\n"
                
                report += "---\n\n"
        
        return report
    
    def save_results(self) -> Dict[str, str]:
        """Save test results to files."""
        files_created = {}
        
        # Save JSON results
        json_path = os.path.join(self.output_dir, f"e2e_results_{self.results['test_run_id']}.json")
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        files_created["json"] = json_path
        
        # Save summary report
        summary_path = os.path.join(self.output_dir, f"e2e_summary_{self.results['test_run_id']}.txt")
        with open(summary_path, 'w') as f:
            f.write(self.generate_summary_report())
        files_created["summary"] = summary_path
        
        # Save detailed report
        detailed_path = os.path.join(self.output_dir, f"e2e_detailed_{self.results['test_run_id']}.md")
        with open(detailed_path, 'w') as f:
            f.write(self.generate_detailed_report())
        files_created["detailed"] = detailed_path
        
        return files_created
    
    def print_final_summary(self):
        """Print final test summary."""
        print("\n" + "=" * 60)
        print(self.generate_summary_report())
        print("=" * 60)
        
        # Print file locations
        files = self.save_results()
        print(f"\n📁 Results saved to:")
        for file_type, file_path in files.items():
            print(f"   {file_type}: {file_path}")


async def main():
    """Main entry point for E2E test runner."""
    import sys
    
    # Parse command line arguments
    environment = "local"
    if len(sys.argv) > 1:
        environment = sys.argv[1]
    
    # Create and run test runner
    runner = E2ETestRunner(environment=environment)
    
    try:
        results = await runner.run_all_suites()
        runner.print_final_summary()
        
        # Exit with appropriate code
        summary = results["summary"]
        if summary["failed"] > 0:
            sys.exit(1)  # Failed tests
        elif summary["total_tests"] == 0:
            sys.exit(2)  # No tests run
        else:
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        print("\n⚠️ Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test run failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
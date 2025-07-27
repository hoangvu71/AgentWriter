#!/usr/bin/env python3
"""
Automated Migration Validator and Safety Checker
"""

import re
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class MigrationIssue:
    file_path: str
    line_number: int
    severity: RiskLevel
    issue_type: str
    message: str
    suggestion: str = ""

class MigrationValidator:
    """Validates database migrations for safety and best practices"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.patterns = self._load_risk_patterns()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_risk_patterns(self) -> Dict:
        """Load patterns that indicate risky migration practices"""
        return {
            'critical_patterns': [
                {
                    'pattern': r'DROP\s+TABLE(?!\s+IF\s+EXISTS)',
                    'message': 'Unguarded DROP TABLE statement',
                    'suggestion': 'Use DROP TABLE IF EXISTS or backup data first'
                },
                {
                    'pattern': r'DELETE\s+FROM\s+\w+\s+WHERE.*NOT\s+IN',
                    'message': 'Dangerous bulk deletion using NOT IN',
                    'suggestion': 'Use EXISTS or proper foreign key constraints'
                },
                {
                    'pattern': r'UPDATE\s+\w+\s+SET.*=.*\(SELECT.*LIMIT\s+1\)',
                    'message': 'Arbitrary assignment using LIMIT 1',
                    'suggestion': 'Use proper JOIN conditions or specific criteria'
                }
            ],
            'high_risk_patterns': [
                {
                    'pattern': r'ALTER\s+TABLE.*DROP\s+COLUMN(?!\s+IF\s+EXISTS)',
                    'message': 'Unguarded column deletion',
                    'suggestion': 'Backup data and use IF EXISTS clause'
                },
                {
                    'pattern': r'(?<!--\s)TRUNCATE\s+TABLE',
                    'message': 'TRUNCATE without backup',
                    'suggestion': 'Backup data before truncating'
                },
                {
                    'pattern': r'DELETE\s+FROM\s+\w+(?!\s+WHERE)',
                    'message': 'Unfiltered DELETE statement',
                    'suggestion': 'Add WHERE clause or use TRUNCATE with backup'
                }
            ],
            'medium_risk_patterns': [
                {
                    'pattern': r'^(?!.*BEGIN).*CREATE\s+TABLE',
                    'message': 'Schema change outside transaction',
                    'suggestion': 'Wrap DDL statements in BEGIN/COMMIT block'
                },
                {
                    'pattern': r'ON\s+DELETE\s+CASCADE',
                    'message': 'Cascade deletion enabled',
                    'suggestion': 'Verify cascade behavior is intentional'
                },
                {
                    'pattern': r'UPDATE.*SET.*=.*SELECT',
                    'message': 'Data transformation without validation',
                    'suggestion': 'Add validation checks after UPDATE'
                }
            ],
            'best_practice_patterns': [
                {
                    'pattern': r'CREATE\s+TABLE\s+(?!.*IF\s+NOT\s+EXISTS)',
                    'message': 'Table creation without IF NOT EXISTS',
                    'suggestion': 'Use CREATE TABLE IF NOT EXISTS for idempotency'
                },
                {
                    'pattern': r'CREATE\s+INDEX\s+(?!.*IF\s+NOT\s+EXISTS)',
                    'message': 'Index creation without IF NOT EXISTS',
                    'suggestion': 'Use CREATE INDEX IF NOT EXISTS for idempotency'
                }
            ]
        }
    
    def validate_migration_file(self, file_path: Path) -> List[MigrationIssue]:
        """Validate a single migration file"""
        self.logger.info(f"Validating migration: {file_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return self._analyze_content(str(file_path), content)
        
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return [MigrationIssue(
                file_path=str(file_path),
                line_number=0,
                severity=RiskLevel.CRITICAL,
                issue_type="FILE_ERROR",
                message=f"Could not read migration file: {e}"
            )]
    
    def _analyze_content(self, file_path: str, content: str) -> List[MigrationIssue]:
        """Analyze migration content for issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for transaction boundaries
        has_begin = any('BEGIN' in line.upper() for line in lines)
        has_commit = any('COMMIT' in line.upper() for line in lines)
        
        if not (has_begin and has_commit):
            issues.append(MigrationIssue(
                file_path=file_path,
                line_number=0,
                severity=RiskLevel.HIGH,
                issue_type="TRANSACTION",
                message="Migration lacks proper transaction boundaries",
                suggestion="Wrap migration in BEGIN/COMMIT block"
            ))
        
        # Check for backup creation
        has_backup = any(
            'backup' in line.lower() or 'CREATE TABLE' in line.upper() 
            for line in lines
        )
        
        destructive_operations = any(
            pattern in line.upper() 
            for line in lines 
            for pattern in ['DELETE FROM', 'DROP TABLE', 'DROP COLUMN', 'TRUNCATE']
        )
        
        if destructive_operations and not has_backup:
            issues.append(MigrationIssue(
                file_path=file_path,
                line_number=0,
                severity=RiskLevel.HIGH,
                issue_type="BACKUP",
                message="Destructive operations without data backup",
                suggestion="Create backup tables before destructive operations"
            ))
        
        # Check patterns line by line
        for line_num, line in enumerate(lines, 1):
            line_upper = line.strip().upper()
            
            # Skip comments
            if line_upper.startswith('--') or not line_upper:
                continue
            
            # Check risk patterns
            issues.extend(self._check_line_patterns(
                file_path, line_num, line, line_upper
            ))
        
        return issues
    
    def _check_line_patterns(self, file_path: str, line_num: int, 
                           line: str, line_upper: str) -> List[MigrationIssue]:
        """Check a line against risk patterns"""
        issues = []
        
        pattern_groups = [
            (self.patterns['critical_patterns'], RiskLevel.CRITICAL),
            (self.patterns['high_risk_patterns'], RiskLevel.HIGH),
            (self.patterns['medium_risk_patterns'], RiskLevel.MEDIUM),
            (self.patterns['best_practice_patterns'], RiskLevel.LOW)
        ]
        
        for patterns, risk_level in pattern_groups:
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                
                if re.search(pattern, line_upper, re.IGNORECASE):
                    issues.append(MigrationIssue(
                        file_path=file_path,
                        line_number=line_num,
                        severity=risk_level,
                        issue_type="PATTERN_MATCH",
                        message=pattern_info['message'],
                        suggestion=pattern_info['suggestion']
                    ))
        
        return issues
    
    def validate_all_migrations(self, migrations_dir: Path) -> Dict:
        """Validate all migration files in directory"""
        self.logger.info(f"Validating all migrations in: {migrations_dir}")
        
        migration_files = list(migrations_dir.glob("*.sql"))
        migration_files = [f for f in migration_files 
                          if not f.name.startswith('TEMPLATE')]
        
        all_issues = {}
        summary = {
            'total_files': len(migration_files),
            'files_with_issues': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0
        }
        
        for migration_file in sorted(migration_files):
            issues = self.validate_migration_file(migration_file)
            
            if issues:
                all_issues[str(migration_file)] = issues
                summary['files_with_issues'] += 1
                
                for issue in issues:
                    if issue.severity == RiskLevel.CRITICAL:
                        summary['critical_issues'] += 1
                    elif issue.severity == RiskLevel.HIGH:
                        summary['high_issues'] += 1
                    elif issue.severity == RiskLevel.MEDIUM:
                        summary['medium_issues'] += 1
                    else:
                        summary['low_issues'] += 1
        
        return {
            'summary': summary,
            'issues': all_issues
        }
    
    def generate_report(self, results: Dict, output_file: Optional[Path] = None) -> str:
        """Generate validation report"""
        summary = results['summary']
        issues = results['issues']
        
        report = []
        report.append("=" * 80)
        report.append("DATABASE MIGRATION VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Files Analyzed: {summary['total_files']}")
        report.append(f"Files with Issues: {summary['files_with_issues']}")
        report.append(f"Critical Issues: {summary['critical_issues']} 🚨")
        report.append(f"High Risk Issues: {summary['high_issues']} ⚠️")
        report.append(f"Medium Risk Issues: {summary['medium_issues']} ⚡")
        report.append(f"Low Risk Issues: {summary['low_issues']} ℹ️")
        report.append("")
        
        # Overall risk assessment
        if summary['critical_issues'] > 0:
            report.append("🚨 OVERALL RISK: CRITICAL - Immediate action required")
        elif summary['high_issues'] > 0:
            report.append("⚠️ OVERALL RISK: HIGH - Review and fix before production")
        elif summary['medium_issues'] > 0:
            report.append("⚡ OVERALL RISK: MEDIUM - Consider improvements")
        else:
            report.append("✅ OVERALL RISK: LOW - Good migration practices")
        report.append("")
        
        # Detailed issues
        if issues:
            report.append("📋 DETAILED ISSUES")
            report.append("-" * 40)
            
            for file_path, file_issues in issues.items():
                file_name = Path(file_path).name
                report.append(f"\n📄 {file_name}")
                report.append("   " + "-" * (len(file_name) + 2))
                
                for issue in sorted(file_issues, key=lambda x: x.line_number):
                    severity_icon = {
                        RiskLevel.CRITICAL: "🚨",
                        RiskLevel.HIGH: "⚠️", 
                        RiskLevel.MEDIUM: "⚡",
                        RiskLevel.LOW: "ℹ️"
                    }[issue.severity]
                    
                    report.append(f"   Line {issue.line_number}: {severity_icon} {issue.message}")
                    if issue.suggestion:
                        report.append(f"      💡 Suggestion: {issue.suggestion}")
        
        # Recommendations
        report.append("\n🔧 RECOMMENDATIONS")
        report.append("-" * 40)
        
        if summary['critical_issues'] > 0:
            report.append("1. 🚨 Address all CRITICAL issues immediately")
            report.append("2. 🧪 Test migrations in staging environment")
            report.append("3. 💾 Ensure data backups before production deployment")
        
        if summary['high_issues'] > 0:
            report.append("1. ⚠️ Review all HIGH risk issues")
            report.append("2. 📋 Use SAFE_MIGRATION_TEMPLATE.sql for future migrations")
            report.append("3. 🔄 Implement transaction boundaries")
        
        report.append("1. 📖 Follow migration best practices documentation")
        report.append("2. 🤖 Run this validator before applying migrations")
        report.append("3. ✅ Use automated migration testing in CI/CD")
        report.append("")
        
        report_text = "\n".join(report)
        
        if output_file:
            output_file.write_text(report_text, encoding='utf-8')
            self.logger.info(f"Report saved to: {output_file}")
        
        return report_text

def main():
    """Main execution function"""
    if len(sys.argv) != 2:
        print("Usage: python automated_migration_validator.py <migrations_directory>")
        sys.exit(1)
    
    migrations_dir = Path(sys.argv[1])
    
    if not migrations_dir.exists():
        print(f"Error: Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    validator = MigrationValidator()
    results = validator.validate_all_migrations(migrations_dir)
    
    # Generate report
    report_file = migrations_dir / "migration_validation_report.txt"
    report = validator.generate_report(results, report_file)
    
    # Print to console
    print(report)
    
    # Exit with appropriate code
    critical_count = results['summary']['critical_issues']
    high_count = results['summary']['high_issues']
    
    if critical_count > 0:
        print(f"\n🚨 VALIDATION FAILED: {critical_count} critical issues found")
        sys.exit(2)  # Critical issues
    elif high_count > 0:
        print(f"\n⚠️ VALIDATION WARNING: {high_count} high-risk issues found")
        sys.exit(1)  # High risk issues
    else:
        print("\n✅ VALIDATION PASSED: No critical issues found")
        sys.exit(0)  # Success

if __name__ == "__main__":
    main()
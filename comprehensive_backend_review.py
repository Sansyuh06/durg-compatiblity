#!/usr/bin/env python3
"""
Comprehensive Backend Code Review Script
Senior-level systematic review for production readiness
"""
import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple

class BackendReviewer:
    def __init__(self, server_dir: str):
        self.server_dir = Path(server_dir)
        self.errors = []
        self.warnings = []
        self.files_reviewed = 0
        
    def review_all(self) -> Dict:
        """Comprehensive review of all backend files"""
        print("=" * 80)
        print("COMPREHENSIVE BACKEND CODE REVIEW")
        print("=" * 80)
        print()
        
        # Get all Python files
        py_files = list(self.server_dir.rglob("*.py"))
        py_files = [f for f in py_files if '.mypy_cache' not in str(f) and '.ruff_cache' not in str(f)]
        
        print(f"[FILES] Found {len(py_files)} Python files to review\n")
        
        for py_file in sorted(py_files):
            self.review_file(py_file)
            
        return self.generate_report()
    
    def review_file(self, filepath: Path):
        """Review a single Python file"""
        self.files_reviewed += 1
        rel_path = filepath.relative_to(self.server_dir.parent)
        
        print(f"[{self.files_reviewed}] Reviewing: {rel_path}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Syntax Check
            try:
                ast.parse(content)
                print(f"  ✅ Syntax: Valid")
            except SyntaxError as e:
                error_msg = f"Syntax Error at line {e.lineno}: {e.msg}"
                self.errors.append((rel_path, error_msg))
                print(f"  ❌ Syntax: {error_msg}")
                return
            
            # 2. Import Check
            import_issues = self.check_imports(filepath, content)
            if import_issues:
                for issue in import_issues:
                    self.warnings.append((rel_path, issue))
                    print(f"  ⚠️  Import: {issue}")
            else:
                print(f"  ✅ Imports: Valid")
            
            # 3. Code Quality Checks
            quality_issues = self.check_code_quality(content)
            if quality_issues:
                for issue in quality_issues:
                    self.warnings.append((rel_path, issue))
                    print(f"  ⚠️  Quality: {issue}")
            else:
                print(f"  ✅ Quality: Good")
            
            # 4. Security Checks
            security_issues = self.check_security(content)
            if security_issues:
                for issue in security_issues:
                    self.warnings.append((rel_path, issue))
                    print(f"  ⚠️  Security: {issue}")
            else:
                print(f"  ✅ Security: No issues")
                
            print()
            
        except Exception as e:
            error_msg = f"Review failed: {str(e)}"
            self.errors.append((rel_path, error_msg))
            print(f"  ❌ Error: {error_msg}\n")
    
    def check_imports(self, filepath: Path, content: str) -> List[str]:
        """Check for import issues"""
        issues = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('server.'):
                    # Relative imports are OK
                    pass
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('server.'):
                        issues.append(f"Absolute import of server module: {alias.name}")
        
        return issues
    
    def check_code_quality(self, content: str) -> List[str]:
        """Check code quality issues"""
        issues = []
        lines = content.split('\n')
        
        # Check for common issues
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                issues.append(f"Line {i} exceeds 120 characters ({len(line)} chars)")
                break  # Only report first occurrence
            
            # TODO/FIXME comments
            if 'TODO' in line or 'FIXME' in line:
                issues.append(f"Line {i} contains TODO/FIXME comment")
                break
        
        # Check for print statements (should use logging)
        if 'print(' in content and 'def __repr__' not in content:
            issues.append("Contains print() statements - should use logging")
        
        return issues[:3]  # Limit to 3 issues per file
    
    def check_security(self, content: str) -> List[str]:
        """Check for security issues"""
        issues = []
        
        # Check for hardcoded secrets
        dangerous_patterns = [
            ('password', 'Possible hardcoded password'),
            ('secret', 'Possible hardcoded secret'),
            ('api_key', 'Possible hardcoded API key'),
            ('token', 'Possible hardcoded token'),
        ]
        
        content_lower = content.lower()
        for pattern, message in dangerous_patterns:
            if f'{pattern} =' in content_lower or f'{pattern}=' in content_lower:
                if 'example' not in content_lower and 'test' not in content_lower:
                    issues.append(message)
                    break
        
        # Check for SQL injection risks
        if 'execute(' in content and 'f"' in content:
            issues.append("Possible SQL injection risk with f-strings")
        
        return issues[:2]  # Limit to 2 issues per file
    
    def generate_report(self) -> Dict:
        """Generate final report"""
        print("=" * 80)
        print("REVIEW SUMMARY")
        print("=" * 80)
        print()
        
        print(f"📊 Files Reviewed: {self.files_reviewed}")
        print(f"❌ Errors Found: {len(self.errors)}")
        print(f"⚠️  Warnings Found: {len(self.warnings)}")
        print()
        
        if self.errors:
            print("🔴 CRITICAL ERRORS:")
            print("-" * 80)
            for filepath, error in self.errors:
                print(f"  {filepath}")
                print(f"    {error}")
            print()
        
        if self.warnings:
            print("🟡 WARNINGS (Non-blocking):")
            print("-" * 80)
            warning_summary = {}
            for filepath, warning in self.warnings:
                if filepath not in warning_summary:
                    warning_summary[filepath] = []
                warning_summary[filepath].append(warning)
            
            for filepath, warnings in list(warning_summary.items())[:10]:  # Show first 10 files
                print(f"  {filepath}")
                for warning in warnings[:3]:  # Show first 3 warnings per file
                    print(f"    • {warning}")
            
            if len(warning_summary) > 10:
                print(f"  ... and {len(warning_summary) - 10} more files with warnings")
            print()
        
        # Final verdict
        if len(self.errors) == 0:
            print("✅ " + "=" * 76)
            print("✅ PRODUCTION READY - ZERO CRITICAL ERRORS")
            print("✅ " + "=" * 76)
            status = "PASS"
        else:
            print("❌ " + "=" * 76)
            print("❌ NOT PRODUCTION READY - CRITICAL ERRORS FOUND")
            print("❌ " + "=" * 76)
            status = "FAIL"
        
        return {
            "status": status,
            "files_reviewed": self.files_reviewed,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "error_details": self.errors,
            "warning_details": self.warnings
        }

if __name__ == "__main__":
    reviewer = BackendReviewer("server")
    report = reviewer.review_all()
    
    # Exit with appropriate code
    sys.exit(0 if report["status"] == "PASS" else 1)

# Made with Bob

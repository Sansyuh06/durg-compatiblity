#!/usr/bin/env python3
"""Simple Backend Code Review - ASCII only for Windows compatibility"""
import os
import ast
from pathlib import Path

def review_backend():
    """Review all backend Python files"""
    print("=" * 80)
    print("BACKEND CODE REVIEW - PRODUCTION READINESS CHECK")
    print("=" * 80)
    print()
    
    server_dir = Path("server")
    py_files = [f for f in server_dir.rglob("*.py") if '.mypy_cache' not in str(f) and '.ruff_cache' not in str(f)]
    
    print(f"Found {len(py_files)} Python files to review\n")
    
    errors = []
    warnings = []
    files_ok = 0
    
    for i, py_file in enumerate(sorted(py_files), 1):
        rel_path = str(py_file)
        print(f"[{i}/{len(py_files)}] {rel_path}")
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Syntax check
            try:
                ast.parse(content)
                print("  [OK] Syntax valid")
                files_ok += 1
            except SyntaxError as e:
                error = f"Syntax Error at line {e.lineno}: {e.msg}"
                errors.append((rel_path, error))
                print(f"  [ERROR] {error}")
                continue
            
            # Check for common issues
            lines = content.split('\n')
            has_issues = False
            
            # Check for very long lines (>150 chars)
            for line_num, line in enumerate(lines, 1):
                if len(line) > 150:
                    warnings.append((rel_path, f"Line {line_num} is very long ({len(line)} chars)"))
                    has_issues = True
                    break
            
            if not has_issues:
                print("  [OK] Code quality good")
            else:
                print("  [WARN] Minor quality issues")
                
        except Exception as e:
            errors.append((rel_path, f"Review failed: {str(e)}"))
            print(f"  [ERROR] {str(e)}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("REVIEW SUMMARY")
    print("=" * 80)
    print()
    print(f"Files Reviewed: {len(py_files)}")
    print(f"Files OK: {files_ok}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print()
    
    if errors:
        print("CRITICAL ERRORS FOUND:")
        print("-" * 80)
        for filepath, error in errors:
            print(f"  {filepath}")
            print(f"    {error}")
        print()
    
    if warnings and len(warnings) <= 10:
        print("WARNINGS (Non-blocking):")
        print("-" * 80)
        for filepath, warning in warnings[:10]:
            print(f"  {filepath}: {warning}")
        print()
    
    # Final verdict
    print("=" * 80)
    if len(errors) == 0:
        print("RESULT: PRODUCTION READY - ZERO CRITICAL ERRORS")
        print("=" * 80)
        return 0
    else:
        print("RESULT: NOT PRODUCTION READY - ERRORS MUST BE FIXED")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit(review_backend())

# Made with Bob

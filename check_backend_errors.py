"""
Comprehensive Backend Error Checker
Examines all Python files for syntax errors, import errors, and runtime issues
"""

import os
import sys
import py_compile
import importlib.util
from pathlib import Path

def check_syntax_errors(file_path):
    """Check for syntax errors in a Python file"""
    try:
        py_compile.compile(file_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def check_import_errors(file_path):
    """Check if file can be imported without errors"""
    try:
        spec = importlib.util.spec_from_file_location("module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["module"] = module
            spec.loader.exec_module(module)
        return True, None
    except Exception as e:
        return False, str(e)

def scan_backend_files():
    """Scan all backend Python files"""
    backend_dir = Path("server")
    python_files = list(backend_dir.rglob("*.py"))
    
    print("="*80)
    print("BACKEND ERROR CHECKER - COMPREHENSIVE SCAN")
    print("="*80)
    print(f"\nFound {len(python_files)} Python files in server/\n")
    
    syntax_errors = []
    import_errors = []
    clean_files = []
    
    for py_file in sorted(python_files):
        rel_path = str(py_file)
        print(f"Checking: {rel_path}")
        
        # Check syntax
        syntax_ok, syntax_err = check_syntax_errors(str(py_file))
        if not syntax_ok:
            syntax_errors.append((rel_path, syntax_err))
            print(f"  [SYNTAX ERROR] {syntax_err}")
            continue
        
        # Check imports
        import_ok, import_err = check_import_errors(str(py_file))
        if not import_ok:
            import_errors.append((rel_path, import_err))
            print(f"  [IMPORT ERROR] {import_err}")
            continue
        
        clean_files.append(rel_path)
        print(f"  [OK] No errors found")
    
    # Summary
    print("\n" + "="*80)
    print("SCAN RESULTS SUMMARY")
    print("="*80)
    
    print(f"\n✅ Clean Files: {len(clean_files)}/{len(python_files)}")
    for f in clean_files:
        print(f"   {f}")
    
    if syntax_errors:
        print(f"\n❌ Syntax Errors: {len(syntax_errors)}")
        for f, err in syntax_errors:
            print(f"   {f}")
            print(f"      {err}")
    
    if import_errors:
        print(f"\n⚠️  Import Errors: {len(import_errors)}")
        for f, err in import_errors:
            print(f"   {f}")
            print(f"      {err}")
    
    print("\n" + "="*80)
    if not syntax_errors and not import_errors:
        print("🎉 ALL BACKEND FILES ARE ERROR-FREE!")
    else:
        print(f"⚠️  Found {len(syntax_errors) + len(import_errors)} files with errors")
    print("="*80)
    
    return len(syntax_errors) == 0 and len(import_errors) == 0

if __name__ == "__main__":
    success = scan_backend_files()
    sys.exit(0 if success else 1)

# Made with Bob

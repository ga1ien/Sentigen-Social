#!/usr/bin/env python3
"""
Snake Case Validation Script
Ensures all field names, variable names, and database columns use snake_case.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Set

# Patterns to detect camelCase violations
CAMEL_CASE_PATTERN = re.compile(r'[a-z][A-Z]')
FIELD_PATTERN = re.compile(r'(\w+):\s*.*=\s*Field\(')
ALIAS_PATTERN = re.compile(r'alias=[\'"](.*?)[\'"]')
VARIABLE_PATTERN = re.compile(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=')
SQL_COLUMN_PATTERN = re.compile(r'CREATE TABLE.*?\((.*?)\)', re.DOTALL | re.IGNORECASE)
SQL_FIELD_PATTERN = re.compile(r'(\w+)\s+\w+', re.IGNORECASE)

# Allowed exceptions (React components, constants, etc.)
ALLOWED_EXCEPTIONS = {
    'React', 'Component', 'Props', 'State', 'Ref', 'Element', 'Event', 'Handler',
    'Provider', 'Context', 'Hook', 'Query', 'Mutation', 'Router', 'Navigation',
    'API', 'URL', 'HTTP', 'JSON', 'XML', 'HTML', 'CSS', 'JS', 'TS', 'JSX', 'TSX',
    'UI', 'UX', 'ID', 'UUID', 'AI', 'ML', 'NLP', 'LLM', 'GPT', 'API_KEY',
    'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY'
}

def is_snake_case(name: str) -> bool:
    """Check if a name follows snake_case convention."""
    if name in ALLOWED_EXCEPTIONS:
        return True

    # Allow UPPER_CASE constants
    if name.isupper() and '_' in name:
        return True

    # Check for camelCase violations
    return not CAMEL_CASE_PATTERN.search(name)

def validate_python_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Validate snake_case in Python files."""
    violations = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return violations

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip comments and imports
        if line.startswith('#') or line.startswith('import ') or line.startswith('from '):
            continue

        # Check Pydantic Field definitions
        field_match = FIELD_PATTERN.search(line)
        if field_match:
            field_name = field_match.group(1)
            if not is_snake_case(field_name):
                violations.append((line_num, field_name, f"Pydantic field '{field_name}' should use snake_case"))

        # Check for camelCase aliases
        alias_match = ALIAS_PATTERN.search(line)
        if alias_match:
            alias_name = alias_match.group(1)
            if not is_snake_case(alias_name):
                violations.append((line_num, alias_name, f"Field alias '{alias_name}' should use snake_case"))

        # Check variable assignments
        var_match = VARIABLE_PATTERN.match(line)
        if var_match:
            var_name = var_match.group(2)
            # Skip class names and function names (handled by other tools)
            if not var_name.startswith('_') and not var_name[0].isupper():
                if not is_snake_case(var_name):
                    violations.append((line_num, var_name, f"Variable '{var_name}' should use snake_case"))

    return violations

def validate_sql_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Validate snake_case in SQL files."""
    violations = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return violations

    # Find CREATE TABLE statements
    table_matches = SQL_COLUMN_PATTERN.findall(content)

    for table_def in table_matches:
        fields = SQL_FIELD_PATTERN.findall(table_def)
        for field_name in fields:
            if not is_snake_case(field_name):
                violations.append((0, field_name, f"SQL column '{field_name}' should use snake_case"))

    return violations

def main():
    parser = argparse.ArgumentParser(description='Validate snake_case naming conventions')
    parser.add_argument('files', nargs='*', help='Files to validate')
    parser.add_argument('--database', action='store_true', help='Validate SQL files')
    args = parser.parse_args()

    if not args.files:
        print("No files provided")
        return 0

    total_violations = 0

    for file_path_str in args.files:
        file_path = Path(file_path_str)

        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        if args.database and file_path.suffix == '.sql':
            violations = validate_sql_file(file_path)
        elif file_path.suffix == '.py':
            violations = validate_python_file(file_path)
        else:
            continue

        if violations:
            print(f"\n❌ Snake case violations in {file_path}:")
            for line_num, name, message in violations:
                if line_num > 0:
                    print(f"  Line {line_num}: {message}")
                else:
                    print(f"  {message}")
            total_violations += len(violations)

    if total_violations > 0:
        print(f"\n❌ Found {total_violations} snake_case violations!")
        print("Please fix these violations before committing.")
        return 1
    else:
        print("✅ All naming conventions are correct!")
        return 0

if __name__ == '__main__':
    sys.exit(main())

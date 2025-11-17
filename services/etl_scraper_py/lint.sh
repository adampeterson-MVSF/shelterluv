#!/bin/bash
set -e

echo "Running Python linting and type checking..."

# Check if tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "Warning: $1 is not installed. Skipping $2 checks."
        return 1
    fi
    return 0
}

# Run mypy type checking
if check_tool mypy "type"; then
    echo "Running mypy..."
    # Run mypy on main entry points to avoid module name conflicts
    mypy main.py run_etl_local.py --config-file mypy.ini
    echo "✅ mypy passed"
else
    echo "❌ mypy not available"
fi

# Run flake8 linting
if check_tool flake8 "style"; then
    echo "Running flake8..."
    flake8 .
    echo "✅ flake8 passed"
else
    echo "ℹ️  flake8 not installed - install with: pip install flake8"
fi

# Run black formatting check
if check_tool black "formatting"; then
    echo "Running black check..."
    black --check --diff .
    echo "✅ black formatting check passed"
else
    echo "ℹ️  black not installed - install with: pip install black"
fi

# Run isort import sorting check
if check_tool isort "import sorting"; then
    echo "Running isort check..."
    isort --check-only --diff .
    echo "✅ isort check passed"
else
    echo "ℹ️  isort not installed - install with: pip install isort"
fi

# Run radon complexity check
if check_tool radon "complexity"; then
    echo "Running radon complexity check..."
    # Check for functions/methods with complexity > 10
    if radon cc . --min C --show-complexity --total-average | grep -q "Average complexity"; then
        echo "⚠️  High complexity functions found:"
        radon cc . --min C --show-complexity
        echo "Consider refactoring functions with complexity > 10"
    else
        echo "✅ No high complexity functions found"
    fi
else
    echo "ℹ️  radon not installed - install with: pip install radon"
fi

# Run ruff check for additional linting
if check_tool ruff "advanced linting"; then
    echo "Running ruff check..."
    ruff check . --extend-select C90  # Add McCabe complexity check
    echo "✅ ruff check completed"
else
    echo "ℹ️  ruff not installed - install with: pip install ruff"
fi

echo "All available linting checks completed!"

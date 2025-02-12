#!/bin/bash
echo "Running all test cases across the project with coverage analysis..."

# Initialize a failure counter
failure_count=0

# Exclude tests in `document_classifier` and `functional_tests` directories
excluded_dirs="document_classifier functional_tests"

# Find all test files except those in excluded directories
test_files=$(find . -type f -name "test_*.py" | grep -Ev "$(echo $excluded_dirs | sed 's/ /|/g')")

# Begin coverage tracking
coverage erase  # Clear any existing coverage data

# Setup .coveragerc configuration to include all Python files
echo "[run]
source = .
include = */*.py

[report]
show_missing = True" > .coveragerc

# Run each test file with coverage (without generating report yet)
for test_file in $test_files; do
    echo "Running $test_file..."
    coverage run --append -m pytest "$test_file"  # Collect coverage data

    # Check the exit status of pytest
    if [ $? -ne 0 ]; then
        echo "Test failed: $test_file"
        failure_count=$((failure_count + 1))
    fi
done

# Report the results without generating the coverage report
if [ $failure_count -ne 0 ]; then
    echo "$failure_count test(s) failed. Refer to the terminal output for details."
    exit 1
else
    echo "All tests passed successfully!"
    echo "Coverage data collected. Coverage report will be generated separately."
fi

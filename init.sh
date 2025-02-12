#!/bin/bash
echo "Running all test cases across the project..."

# Initialize a failure counter
failure_count=0

# Exclude tests in `document_classifier` and `functional_tests` directories
excluded_dirs="document_classifier functional_tests"

# Find all test files except those in excluded directories
test_files=$(find . -type f -name "test_*.py" | grep -Ev "$(echo $excluded_dirs | sed 's/ /|/g')")

# Run each test file
for test_file in $test_files; do
    echo "Running $test_file..."
    pytest "$test_file"

    # Check the exit status of pytest
    if [ $? -ne 0 ]; then
        echo "Test failed: $test_file"
        failure_count=$((failure_count + 1))
    fi
done

# Report the results
if [ $failure_count -ne 0 ]; then
    echo "$failure_count test(s) failed."
    exit 1
else
    echo "All tests passed successfully!"
fi

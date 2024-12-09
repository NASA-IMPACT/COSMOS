#!/bin/bash
echo "Running all test cases across the project..."

# Initialize a failure counter
failure_count=0

# Find and run all Python files starting with 'test_' in the entire project directory
for test_file in $(find . -type f -name "test_*.py"); do
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


!/bin/bash
echo "Running all test cases across the project..."

# Find and run all Python files starting with 'test_' in the entire project directory
for test_file in $(find . -type f -name "test_*.py"); do
    echo "Running $test_file..."
    pytest "$test_file"
done

echo "All tests completed!"

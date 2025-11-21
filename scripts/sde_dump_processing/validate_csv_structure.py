import csv
import sys


def analyze_output_csv(filename):
    # Increase CSV field size limit
    csv.field_size_limit(sys.maxsize)

    total_rows = 0
    correct_rows = 0
    incorrect_rows = 0

    with open(filename, encoding="utf-8") as f:
        reader = csv.reader(f)

        # Attempt to read a header row
        header = next(reader, None)
        if header:
            print("Header row:", header)

        for row_index, row in enumerate(reader, start=2):
            total_rows += 1

            # Check for exactly 8 columns
            if len(row) != 8:
                incorrect_rows += 1
                print(f"[WARNING] Row {row_index} has {len(row)} columns (expected 8). Row data")
                continue

            # Optional: ensure last column is strictly 'true' or 'false'
            if row[7] not in ("true", "false"):
                incorrect_rows += 1
                print(f"[WARNING] Row {row_index} last column not 'true' or 'false': {row[0]}, {row[7][:100]}")
                continue

            correct_rows += 1

    print("\n=== ANALYSIS COMPLETE ===")
    print(f"Total data rows (excluding header): {total_rows}")
    print(f"Correctly formatted rows: {correct_rows}")
    print(f"Incorrectly formatted rows: {incorrect_rows}")


def main():
    import sys

    filename = sys.argv[1] if len(sys.argv) > 1 else "outputs/cleaned_dump_delimeter.csv"
    print(f"Analyzing: {filename}")
    analyze_output_csv(filename)


if __name__ == "__main__":
    main()

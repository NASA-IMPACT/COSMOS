import csv
import sys


def write_id_and_url_for_row(filename, row_number, output_file):
    # Increase CSV field size limit so large fields won't cause errors
    csv.field_size_limit(sys.maxsize)

    with open(filename, encoding="utf-8") as f:
        reader = csv.reader(f)

        # Skip the header row
        next(reader, None)

        # IMPORTANT: start=2 to match the validation script's row numbering
        for current_row_index, row in enumerate(reader, start=2):
            if current_row_index == row_number:
                with open(output_file, "w", encoding="utf-8", newline="") as out_f:
                    writer = csv.writer(out_f)
                    writer.writerow(row)
                return

    # If you get here, that row_number didn't exist
    with open(output_file, "w", encoding="utf-8") as out_f:
        out_f.write(f"Row {row_number} does not exist in {filename}.\n")


def main():
    # Example usage:
    filename = "outputs/cleaned_dump_delimeter.csv"
    output_file = "outputs/row_output.csv"
    desired_row_number = 175655  # or wherever you want
    write_id_and_url_for_row(filename, desired_row_number, output_file)


if __name__ == "__main__":
    main()

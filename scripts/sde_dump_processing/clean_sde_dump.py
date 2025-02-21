import csv


def process_large_csv(input_filename, output_filename):
    # Open the input file for reading and the output file for writing.
    # We assume UTF-8 encoding (adjust if necessary).
    with open(input_filename, encoding="utf-8") as infile, open(
        output_filename, "w", encoding="utf-8", newline=""
    ) as outfile:

        writer = csv.writer(outfile)
        # Write header if needed:
        writer.writerow(["id", "url1", "title", "collection", "treepath", "sourcestr56", "text", "sourcebool3"])

        current_record = ""
        for line in infile:
            # Remove the trailing newline from the line.
            line = line.rstrip("\n")
            # If the line starts with /SDE/, it signals the beginning of a new row.
            if line.startswith("/SDE/"):
                # If we already have a record accumulated, process it.
                if current_record:
                    # Split the record into exactly 8 fields.
                    # Using maxsplit=7 ensures that any additional occurrences of '火'
                    # (for example in the text field) remain intact.
                    parts = current_record.split("火", 7)
                    # Optional: normalize the text field if needed.
                    # For example, replace literal newline characters within the text with "\n".
                    if len(parts) == 8:
                        parts[6] = parts[6].replace("\n", "\\n")
                        writer.writerow(parts)
                    else:
                        # Handle unexpected formatting issues (e.g. log or skip the record).
                        print("Warning: Expected 8 fields, got", len(parts))
                # Start a new record with the current line.
                current_record = line
            else:
                # Otherwise, this line is a continuation of the current record.
                current_record += "\n" + line

        # After the loop, process the last accumulated record.
        if current_record:
            parts = current_record.split("火", 7)
            if len(parts) == 8:
                parts[6] = parts[6].replace("\n", "\\n")
                writer.writerow(parts)
            else:
                print("Warning: Expected 8 fields, got", len(parts))


if __name__ == "__main__":
    # Replace with your actual file names.
    # process_large_csv("./dump.csv", "./cleaned_dump.csv")
    process_large_csv("./tests/original.csv", "./actual_script_output.csv")

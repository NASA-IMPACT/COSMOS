import csv


def process_large_csv(input_filename, output_filename):
    # Open the input file for reading and the output file for writing.
    with open(input_filename, encoding="utf-8") as infile, open(
        output_filename, "w", encoding="utf-8", newline=""
    ) as outfile:

        writer = csv.writer(outfile)
        # Write header if needed:
        writer.writerow(["id", "url1", "title", "collection", "treepath", "sourcestr56", "text", "sourcebool3"])

        current_record = ""
        for line in infile:
            line = line.rstrip("\n")
            # Skip lines until the first record is found.
            if not current_record and not (line.startswith("/SDE/") or line.startswith("/SDE-TDAMM/")):
                continue
            if line.startswith("/SDE/") or line.startswith("/SDE-TDAMM/"):
                if current_record:
                    parts = current_record.split("༜", 7)
                    if len(parts) == 8:
                        parts[6] = parts[6].replace("\n", "\\n")
                        writer.writerow(parts)
                    else:
                        print("Warning: Expected 8 fields, got", len(parts))
                current_record = line
            else:
                current_record += "\n" + line

        # After the loop, process the last accumulated record.
        if current_record:
            parts = current_record.split("༜", 7)
            if len(parts) == 8:
                parts[6] = parts[6].replace("\n", "\\n")
                writer.writerow(parts)
            else:
                print("Warning: Expected 8 fields, got", len(parts))


if __name__ == "__main__":
    # Replace with your actual file names.
    process_large_csv("./inputs/dump_delimeter.csv", "./outputs/cleaned_dump_delimeter.csv")

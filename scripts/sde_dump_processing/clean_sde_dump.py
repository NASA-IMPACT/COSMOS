"""
to run
python clean_sde_dump.py inputs/sde_init_dump_04_28_2025.csv outputs/input.csv -v

to compress
7z a -t7z -m0=lzma2 -mx=9 -mmt=on -md=512m outputs/output.7z outputs/input.csv
"""

import argparse
import csv
import logging
import os
import sys
import time
from datetime import timedelta

# Set up logging
# Define a custom formatter to include milliseconds
log_formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
# Get the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Default level
# Create a handler and set the formatter
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
# Add the handler to the logger
# Check if handlers already exist to avoid duplicates in interactive environments
if not logger.hasHandlers():
    logger.addHandler(stream_handler)


def assemble_records_generator(input_filename, skip_header=False, progress_interval=100000):
    """
    Reads the input file line by line and yields assembled multi-line records.
    Optionally skips the first line if it's a header.
    """
    current_record = ""
    record_started = False
    lines_processed = 0
    start_time = time.time()
    last_report_time = start_time
    record_count = 0  # Keep track of records yielded

    logger.info(f"Starting to process lines from {input_filename}")

    try:
        with open(input_filename, encoding="utf-8") as infile:
            # Skip the header line if requested
            if skip_header:
                try:
                    first_line = next(infile)
                    lines_processed += 1
                    logger.info(f"Skipped header line: {first_line.rstrip()}")
                except StopIteration:
                    logger.warning("Input file appears to be empty or only contains a header.")
                    return  # Stop if file is empty after header

            # Process remaining lines
            while True:
                try:
                    line = next(infile)
                    lines_processed += 1

                    # Report progress periodically based on lines read
                    if lines_processed % progress_interval == 0:
                        current_time = time.time()
                        elapsed = current_time - start_time
                        rate = lines_processed / elapsed if elapsed > 0 else 0

                        # Only log if at least 5 seconds have passed since the last report
                        if current_time - last_report_time >= 5:
                            logger.info(f"Read {lines_processed:,} lines - " f"Rate: {rate:.0f} lines/sec")
                            last_report_time = current_time

                    line = line.rstrip("\n")

                    # Check if this line is the start of a new record
                    is_record_start = (
                        line.startswith("/SDE/") or line.startswith("/SDE-TDAMM/") or line.startswith("/scrapers/")
                    )

                    # Skip lines until the first record is found
                    # (This check might be less relevant if the first data line always starts a record)
                    if not record_started and not is_record_start:
                        # If we skipped the header, the first line *should* be a record start
                        # Log a warning if it's not, but continue processing anyway
                        if skip_header and lines_processed == 2:  # Only warn on the first actual data line
                            logger.warning(
                                f"First data line does not start with a recognized record prefix: {line[:100]}..."
                            )
                        # continue -> We should actually process this line if it's part of the first record

                    if is_record_start:
                        # If we've already been building a record, yield it
                        if current_record:
                            yield current_record
                            record_count += 1

                        # Start a new record
                        current_record = line
                        record_started = True
                    elif record_started:  # Only append if a record has started
                        # Append to the current record
                        current_record += "\n" + line
                    # Handle case where a non-starting line is encountered before the first record start
                    # This might happen if skip_header=False and there's preamble before the first /SDE/
                    elif not record_started and not is_record_start:
                        continue  # Explicitly skip lines before the first record start marker

                except StopIteration:  # End of file
                    break
                except UnicodeDecodeError as e:
                    logger.warning(f"Skipping line {lines_processed} due to UnicodeDecodeError: {e}")
                    continue  # Skip the problematic line

        # Yield the last record if there is one
        if current_record:
            yield current_record
            record_count += 1

        elapsed = time.time() - start_time
        logger.info(
            f"Finished reading {lines_processed:,} lines and found {record_count:,} raw records in {elapsed:.2f} seconds"  # noqa
        )

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_filename}")
        raise


def process_records_generator(raw_records_iterator, delimiter="༜", expected_fields=None, batch_size=50000):
    """
    Processes records from an iterator, yielding valid processed records.
    Requires expected_fields to be specified.
    """
    if expected_fields is None:
        raise ValueError("process_records_generator requires 'expected_fields' to be specified.")

    processed_count = 0
    invalid_records = 0
    start_time = time.time()
    last_report_time = start_time
    input_record_index = 0  # Track input records processed for logging

    logger.info(f"Starting record processing (expecting {expected_fields} fields)...")

    for i, record in enumerate(raw_records_iterator):
        input_record_index = i + 1
        # Split into AT MOST expected_fields parts. The last part will contain the rest.
        parts = record.split(delimiter, expected_fields - 1)

        if len(parts) == expected_fields:
            # Replace literal newlines with '\\n' string in the text field
            # The text field is the last one, index expected_fields - 1
            text_field_index = expected_fields - 1
            if text_field_index < len(parts):  # Ensure index exists
                parts[text_field_index] = parts[text_field_index].replace("\n", "\\n")
            else:
                # This case should technically not happen if len(parts) == expected_fields
                # but adding a safeguard.
                logger.warning(
                    f"Record ~{input_record_index}: Field index {text_field_index} out of bounds unexpectedly."
                )

            processed_count += 1
            yield parts  # Yield the valid processed record
        else:
            invalid_records += 1
            if invalid_records <= 10:  # Log only the first 10 invalid records
                logger.warning(
                    f"Record ~{input_record_index}: Expected {expected_fields} fields, got {len(parts)}. Skipping."
                )
                # Optionally log the problematic record content (careful with large fields)
                # logger.debug(f"Problematic record content (first 100 chars): {record[:100]}")
            # Do not yield invalid records

        # Report progress periodically based on input records processed
        if input_record_index % batch_size == 0:
            current_time = time.time()
            if current_time - last_report_time >= 5:
                elapsed = current_time - start_time
                rate = input_record_index / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Processed {input_record_index:,} raw records ({processed_count:,} valid) - "
                    f"Rate: {rate:.0f} records/sec"
                )
                last_report_time = current_time

    if invalid_records > 10:
        logger.warning(f"Additional {invalid_records - 10} invalid records were skipped (not shown in logs)")

    logger.info(
        f"Finished processing {input_record_index:,} raw records. Found {processed_count:,} valid records and {invalid_records:,} invalid records."  # noqa
    )


def write_output_file(output_filename, processed_records_iterator, header=None, batch_size=100000):
    """Write the processed records from an iterator to the output CSV file."""
    # Create the directory if it doesn't exist
    output_dir = os.path.dirname(output_filename)
    # Check if output_dir is not empty before creating
    if output_dir and not os.path.exists(output_dir):
        logger.info(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

    records_written = 0
    start_time = time.time()
    last_report_time = start_time

    logger.info(f"Starting to write records to {output_filename}")

    try:
        with open(output_filename, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)

            # Write header if provided
            if header:
                logger.info(f"Writing header: {header}")
                writer.writerow(header)
            else:
                logger.warning("No header provided for output file.")

            # Write records as they come from the iterator
            for i, record in enumerate(processed_records_iterator):
                writer.writerow(record)
                records_written += 1

                # Report progress periodically
                if records_written % batch_size == 0:
                    current_time = time.time()
                    if current_time - last_report_time >= 5:
                        elapsed = current_time - start_time
                        rate = records_written / elapsed if elapsed > 0 else 0
                        logger.info(f"Wrote {records_written:,} records - " f"Rate: {rate:.0f} records/sec")
                        last_report_time = current_time

        total_time = time.time() - start_time
        logger.info(f"Finished writing {records_written:,} records in {total_time:.2f} seconds")

    except OSError as e:
        logger.error(f"Error writing to output file {output_filename}: {e}")
        raise

    return records_written


def process_large_csv(input_filename, output_filename, delimiter="༜", verbose=False):
    """
    Process a large CSV file iteratively using generators.
    Determines header and field count from the first line of the input file.
    """
    # Adjust logging level based on verbosity - should be set in main()
    if verbose:
        logger.setLevel(logging.INFO)

    logger.info(f"Processing {input_filename} to {output_filename} with delimiter '{delimiter}'")
    total_start_time = time.time()

    header = None
    expected_fields = 0

    # --- Read header and determine expected fields ---
    try:
        with open(input_filename, encoding="utf-8") as infile:
            first_line = next(infile).rstrip("\n")
            header = first_line.split(delimiter)
            expected_fields = len(header)
            logger.info(f"Detected header: {header}")
            logger.info(f"Expecting {expected_fields} fields based on header.")
            if expected_fields == 0:
                logger.error("Header line is empty or could not be split. Cannot proceed.")
                return -1
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_filename}")
        return -1  # Indicate file not found error
    except StopIteration:
        logger.error(f"Input file is empty: {input_filename}")
        return -1  # Indicate empty file error
    except Exception as e:
        logger.error(f"Error reading header from {input_filename}: {e}", exc_info=True)
        return -1  # Indicate general error during header read
    # --- End header reading ---

    try:
        # Create iterators/generators
        # Pass skip_header=True to avoid processing the header line again
        raw_records_iter = assemble_records_generator(input_filename, skip_header=True)
        # Pass the dynamically determined expected_fields
        processed_records_iter = process_records_generator(raw_records_iter, delimiter, expected_fields)

        # Write to output file by consuming the processed records iterator, using the detected header
        records_written = write_output_file(output_filename, processed_records_iter, header)

        total_elapsed = time.time() - total_start_time
        rate = records_written / total_elapsed if total_elapsed > 0 else 0
        logger.info(
            f"Complete! Processed {records_written:,} valid records in {timedelta(seconds=int(total_elapsed))} "
            f"(Average rate: {rate:.1f} records/sec)"
        )
        return records_written

    except FileNotFoundError:
        # Error already logged by assemble_records_generator if it happens later
        # This is unlikely if header reading succeeded, but kept for safety
        logger.error(f"Input file disappeared after reading header: {input_filename}")
        return -1
    except Exception as e:
        logger.error(f"An unexpected error occurred during processing: {e}", exc_info=True)
        return -1  # Indicate general error


def main():
    """Main entry point for the script."""
    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Process large CSV files with special formatting efficiently, detecting header automatically."
    )
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")
    parser.add_argument("--delimiter", default="༜", help="Field delimiter character (default: '༜')")
    # Removed --fields argument
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed progress information (INFO level)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress all output except errors (ERROR level)")

    args = parser.parse_args()

    # Adjust logging level based on args BEFORE calling processing function
    if args.quiet:
        logger.setLevel(logging.ERROR)
    elif args.verbose:
        logger.setLevel(logging.INFO)
    else:
        # Default level if neither -v nor -q is specified
        logger.setLevel(logging.WARNING)

    # Process the CSV file using the arguments passed
    # No longer passing expected_fields
    records_processed = process_large_csv(
        args.input, args.output, delimiter=args.delimiter, verbose=args.verbose  # Pass verbose flag
    )

    if records_processed >= 0 and not args.quiet:
        # Use standard print for final user confirmation message
        print(f"Successfully processed {records_processed:,} records.")
        return 0
    elif records_processed < 0:
        # Error messages already logged
        print("Processing failed. Check logs for details.", file=sys.stderr)
        return 1
    else:  # records_processed == 0, potentially valid but maybe unexpected
        if not args.quiet:
            print("Processing finished, but 0 valid records were written.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

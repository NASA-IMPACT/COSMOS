"""
this is meant to be run from within a shell. you can do it in the following way:

establish a coding container

```shell
tmux new -s docker_django
tmux attach -t docker_django
tmux kill-session -t docker_django
```

```bash
dmshell
```

copy paste this code into the shell and run it

getting the info out of the container

```bash
docker cp 593dab064a15:/tmp/curated_urls_status.json ./curated_urls_status.json
```

move it onto local
```bash
scp sde:/home/ec2-user/sde_indexing_helper/curated_urls_status.json .
```

"""

import concurrent.futures
import json
import os
from collections import defaultdict

from django.db import connection

from sde_collections.models.delta_url import CuratedUrl


def process_chunk(chunk_start, chunk_size, total_count):
    """Process a chunk of curated URLs and return data grouped by collection"""
    # Close any existing DB connections to avoid sharing connections between processes
    connection.close()

    # Get the chunk of data with collection information
    curated_urls_chunk = (
        CuratedUrl.objects.select_related("collection")
        .all()
        .with_exclusion_status()
        .order_by("url")[chunk_start : chunk_start + chunk_size]
    )

    # Group URLs by collection folder name
    collection_data = defaultdict(list)
    for url in curated_urls_chunk:
        collection_folder = url.collection.config_folder
        included = not url.excluded  # Convert to boolean inclusion status

        collection_data[collection_folder].append({"url": url.url, "included": included})

    # Save to a temporary file
    temp_path = f"/tmp/chunk{chunk_start}.json"
    with open(temp_path, "w") as f:
        json.dump(dict(collection_data), f)

    processed = min(chunk_start + chunk_size, total_count)
    print(f"Processed {processed}/{total_count} URLs")

    return temp_path


def export_curated_urls_with_status():
    """Export all curated URLs with their inclusion status, grouped by collection"""
    output_path = "/tmp/curated_urls_status.json"

    # Get the total count and status statistics
    curated_urls = CuratedUrl.objects.all().with_exclusion_status()
    total_count = curated_urls.count()
    excluded_count = curated_urls.filter(excluded=True).count()
    included_count = curated_urls.filter(excluded=False).count()

    print(f"Total URLs: {total_count}")
    print(f"  Excluded: {excluded_count}")
    print(f"  Included: {included_count}")

    # Define chunk size and calculate number of chunks
    chunk_size = 10000
    chunk_starts = list(range(0, total_count, chunk_size))

    # Process chunks in parallel
    temp_files = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_chunk = {
            executor.submit(process_chunk, chunk_start, chunk_size, total_count): chunk_start
            for chunk_start in chunk_starts
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_start = future_to_chunk[future]
            try:
                temp_file = future.result()
                temp_files.append(temp_file)
            except Exception as e:
                print(f"Chunk starting at {chunk_start} generated an exception: {e}")

    # Combine all temp files into final output
    combined_data = {}

    # Sort temp files by chunk start position
    temp_files.sort(key=lambda x: int(os.path.basename(x).replace("chunk", "").split(".")[0]))

    for temp_file in temp_files:
        with open(temp_file) as infile:
            chunk_data = json.load(infile)
            # Merge chunk data into combined data
            for collection_folder, urls in chunk_data.items():
                if collection_folder not in combined_data:
                    combined_data[collection_folder] = []
                combined_data[collection_folder].extend(urls)

        # Clean up temp file
        os.unlink(temp_file)

    # Write the final combined data
    with open(output_path, "w") as outfile:
        json.dump(combined_data, outfile, indent=2)

    # Verify export completed successfully
    if os.path.exists(output_path):
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Export complete. File saved to: {output_path}")
        print(f"File size: {file_size_mb:.2f} MB")

        # Sanity check: Count the total included and excluded URLs in the final file
        final_included = 0
        final_excluded = 0

        # Read the file back and count
        with open(output_path) as infile:
            file_data = json.load(infile)
            for collection_folder, urls in file_data.items():
                for url_data in urls:
                    if url_data["included"]:
                        final_included += 1
                    else:
                        final_excluded += 1

        print("\nSanity check on final file:")
        print(f"Total URLs in file: {final_included + final_excluded}")
        print(f"  Included: {final_included}")
        print(f"  Excluded: {final_excluded}")

        # Check if counts match
        if final_included == included_count and final_excluded == excluded_count:
            print("✅ Counts match database query results!")
        else:
            print("⚠️ Warning: Final counts don't match initial database query!")
            print(f"  Database included: {included_count}, File included: {final_included}")
            print(f"  Database excluded: {excluded_count}, File excluded: {final_excluded}")
    else:
        print("ERROR: Output file was not created!")


# Run the export function
export_curated_urls_with_status()

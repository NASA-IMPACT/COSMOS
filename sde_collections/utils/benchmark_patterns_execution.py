# Run the following command for execution
# docker compose -f local.yml run --rm django python3 manage.py test sde_collections.utils.benchmark_patterns_execution


import cProfile
import io
import pstats
import random
from functools import wraps
from time import time
from typing import Any

from django.db import transaction
from django.test import TestCase

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import Divisions, DocumentTypes
from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
    DeltaIncludePattern,
    DeltaTitlePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl


def profile_function(func):
    """Decorator to profile a function and all its called functions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()

        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats()

        return result, s.getvalue()

    return wrapper


class DeltaPatternsDetailedBenchmark(TestCase):
    """Detailed benchmark suite for Delta Patterns including all called functions."""

    def setUp(self):
        """Set up test data with varying sizes using bulk operations."""
        start_time = time()
        print("\nSetting up test data...")

        with transaction.atomic():
            # Create collection
            self.collection = Collection.objects.create(
                name="Test Collection",
                division=Divisions.ASTROPHYSICS,
                document_type=DocumentTypes.DATA,
            )

            self.url_sizes = [10, 100, 1000, 10000, 50000, 100000, 150000, 200000]
            max_size = max(self.url_sizes)

            # Bulk create CuratedUrls in batches
            batch_size = 1000
            for i in range(0, max_size, batch_size):
                batch_end = min(i + batch_size, max_size)
                print(f"Creating CuratedUrls batch {i} to {batch_end}")

                curated_urls = [
                    CuratedUrl(
                        collection=self.collection,
                        url=f"https://example.com/doc/{j}",
                        scraped_title=f"Document {j}",
                        generated_title=f"Generated Document {j}",
                        document_type=random.choice(list(DocumentTypes.values)),
                        division=random.choice(list(Divisions.values)),
                    )
                    for j in range(i, batch_end)
                ]
                CuratedUrl.objects.bulk_create(curated_urls)

        setup_time = time() - start_time
        print(f"Setup completed in {setup_time:.2f} seconds")

    def tearDown(self):
        """Clean up test data."""
        print("\nCleaning up test data...")
        start_time = time()

        with transaction.atomic():
            DeltaUrl.objects.all().delete()
            CuratedUrl.objects.all().delete()
            Collection.objects.all().delete()

        cleanup_time = time() - start_time
        print(f"Cleanup completed in {cleanup_time:.2f} seconds")

    def _get_pattern_metrics(self, profile_output: str) -> dict[str, list[dict[str, Any]]]:
        """Parse cProfile output and categorize metrics by operation type."""
        metrics = []
        lines = [line for line in profile_output.split("\n") if line.strip() and "function calls" not in line]

        for line in lines:
            if line.strip() and len(line.split()) >= 6:
                parts = line.split()
                try:
                    metrics.append(
                        {
                            "ncalls": parts[0],
                            "tottime": float(parts[1]),
                            "percall": float(parts[2]),
                            "cumtime": float(parts[3]),
                            "percall_cum": float(parts[4]),
                            "function_name": " ".join(parts[5:]),
                        }
                    )
                except (ValueError, IndexError):
                    continue

        # Categorize metrics
        categorized_metrics = {
            "curated_url_ops": [m for m in metrics if "CuratedUrl" in m["function_name"]],
            "delta_url_ops": [m for m in metrics if "DeltaUrl" in m["function_name"]],
            "pattern_ops": [m for m in metrics if "Pattern" in m["function_name"]],
            "db_ops": [m for m in metrics if "django.db" in m["function_name"]],
            "other_ops": [
                m
                for m in metrics
                if not any(x in m["function_name"] for x in ["CuratedUrl", "DeltaUrl", "Pattern", "django.db"])
            ],
        }

        return categorized_metrics

    def _benchmark_pattern_with_profiling(self, pattern_class, pattern_data):
        """Run detailed benchmarks with categorized metrics."""
        results = []

        for size in self.url_sizes:
            print(f"\nTesting with dataset size: {size}")
            pattern_instance = pattern_class.objects.create(
                collection=self.collection, match_pattern="https://example.com/doc/*", **pattern_data
            )

            # Profile operations
            apply_func = profile_function(pattern_instance.apply)
            unapply_func = profile_function(pattern_instance.unapply)

            _, apply_profile = apply_func()
            _, unapply_profile = unapply_func()

            # Get categorized metrics
            apply_metrics = self._get_pattern_metrics(apply_profile)
            unapply_metrics = self._get_pattern_metrics(unapply_profile)

            results.append(
                {
                    "pattern_type": pattern_class.__name__,
                    "dataset_size": size,
                    "apply_metrics": apply_metrics,
                    "unapply_metrics": unapply_metrics,
                }
            )

            pattern_instance.delete()

        return results

    def _print_detailed_results(self, pattern_name: str, results: list[dict[str, Any]]):
        """Print detailed profiling results with categorized metrics."""
        print(f"\n{'='*100}")
        print(f"Detailed Profile for {pattern_name}")
        print(f"{'='*100}")

        categories = ["curated_url_ops", "delta_url_ops", "pattern_ops", "db_ops", "other_ops"]

        for result in results:
            size = result["dataset_size"]
            print(f"\nDataset Size: {size}")

            for operation in ["apply_metrics", "unapply_metrics"]:
                op_name = operation.upper().replace("_METRICS", "")
                print(f"\n{op_name} OPERATION")

                for category in categories:
                    metrics = result[operation][category]
                    if metrics:
                        print(f"\n{category.replace('_', ' ').title()}:")
                        print(f"{'Function Name':<50} | {'Calls':<8} | {'Total Time':<12} | {'Cumulative':<12}")
                        print("-" * 86)

                        sorted_metrics = sorted(metrics, key=lambda x: float(x["cumtime"]), reverse=True)
                        for metric in sorted_metrics[:5]:  # Show top 5 for each category
                            print(
                                f"{metric['function_name']:<50} | "
                                f"{metric['ncalls']:<8} | "
                                f"{metric['tottime']:<12.4f} | "
                                f"{metric['cumtime']:<12.4f}"
                            )

    def test_all_patterns(self):
        """Run benchmarks for all pattern types."""
        pattern_configs = [
            (DeltaExcludePattern, {"reason": "Test exclusion"}, "Exclude Pattern"),
            (DeltaIncludePattern, {}, "Include Pattern"),
            (DeltaDivisionPattern, {"division": Divisions.ASTROPHYSICS}, "Division Pattern"),
            (DeltaDocumentTypePattern, {"document_type": DocumentTypes.DATA}, "Document Type Pattern"),
            (DeltaTitlePattern, {"title_pattern": "{title} - {collection}"}, "Title Pattern"),
        ]

        all_results = []
        for pattern_class, pattern_data, pattern_name in pattern_configs:
            print(f"\nBenchmarking {pattern_name}...")
            results = self._benchmark_pattern_with_profiling(pattern_class, pattern_data)
            self._print_detailed_results(pattern_name, results)
            all_results.extend(results)

        self._print_comparative_summary(all_results)

    def _print_comparative_summary(self, all_results):
        """Print a comparative summary with operation categories."""
        print("\n" + "=" * 100)
        print("COMPARATIVE SUMMARY")
        print("=" * 100)

        for size in self.url_sizes:
            print(f"\nDataset Size: {size}")
            size_results = [r for r in all_results if r["dataset_size"] == size]

            for result in size_results:
                pattern_type = result["pattern_type"]
                print(f"\n{pattern_type}")

                for operation in ["apply_metrics", "unapply_metrics"]:
                    op_name = operation.upper().replace("_METRICS", "")
                    metrics = result[operation]

                    total_time = sum(sum(float(m["tottime"]) for m in category) for category in metrics.values())

                    curated_time = sum(float(m["tottime"]) for m in metrics["curated_url_ops"])
                    delta_time = sum(float(m["tottime"]) for m in metrics["delta_url_ops"])
                    pattern_time = sum(float(m["tottime"]) for m in metrics["pattern_ops"])
                    db_time = sum(float(m["tottime"]) for m in metrics["db_ops"])

                    print(f"\n{op_name}:")
                    print(f"{'Operation Type':<20} | {'Time (s)':<10} | {'% of Total':<10}")
                    print("-" * 50)
                    print(f"{'CuratedUrl Ops':<20} | {curated_time:<10.4f} | {(curated_time/total_time)*100:<10.1f}")
                    print(f"{'DeltaUrl Ops':<20} | {delta_time:<10.4f} | {(delta_time/total_time)*100:<10.1f}")
                    print(f"{'Pattern Ops':<20} | {pattern_time:<10.4f} | {(pattern_time/total_time)*100:<10.1f}")
                    print(f"{'Database Ops':<20} | {db_time:<10.4f} | {(db_time/total_time)*100:<10.1f}")
                    print(f"{'Total':<20} | {total_time:<10.4f} | 100.0")

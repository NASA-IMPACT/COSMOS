# docker-compose -f local.yml run --rm django python manage.py deduplicate_patterns
# docker-compose -f production.yml run --rm django python manage.py deduplicate_patterns

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count

from sde_collections.models.pattern import (
    DivisionPattern,
    DocumentTypePattern,
    ExcludePattern,
    IncludePattern,
    TitlePattern,
)


class Command(BaseCommand):
    help = "Remove duplicate patterns within collections for all pattern types"

    def handle(self, *args, **kwargs):
        pattern_models = [ExcludePattern, IncludePattern, TitlePattern, DocumentTypePattern, DivisionPattern]

        deletion_counts = defaultdict(int)

        for model in pattern_models:
            # Get all collections that have duplicate patterns
            collections_with_dupes = (
                model.objects.values("collection", "match_pattern")
                .annotate(pattern_count=Count("id"))
                .filter(pattern_count__gt=1)
            )

            for group in collections_with_dupes:
                # Get all patterns for this collection/match_pattern combo
                patterns = model.objects.filter(collection_id=group["collection"], match_pattern=group["match_pattern"])

                # Keep one pattern, delete the rest
                patterns_to_delete = patterns[1:]
                for pattern in patterns_to_delete:
                    pattern.delete()
                    deletion_counts[model.__name__] += 1

        # Print final summary
        for model_name, count in deletion_counts.items():
            self.stdout.write(f"{model_name}: {count}")
        self.stdout.write(f"Total: {sum(deletion_counts.values())}")

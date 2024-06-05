# flake8: noqa
"""this script is used to find all the xpath patterns in the database, so that they can be mapped to new patterns in xpath_mappings.py"""

from sde_collections.models.pattern import TitlePattern

print(
    "there are", TitlePattern.objects.filter(title_pattern__contains="xpath").count(), "xpath patterns in the database"
)

# Get all the xpath patterns and their candidate urls
xpath_patterns = TitlePattern.objects.filter(title_pattern__contains="xpath")
for xpath_pattern in xpath_patterns:
    print(xpath_pattern.title_pattern)
    # for url in xpath_pattern.candidate_urls.all():
    #     print(url.url)
    print()

# not every xpath pattern has a candidate url, but I went ahead and fixed all of them anyway

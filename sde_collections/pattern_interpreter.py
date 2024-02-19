def interpret_title_pattern(url, scraped_title, title_pattern):
    """Interpret a title pattern."""
    # If "{title}" is in the title_pattern, replace it with scraped_title
    if "{title}" in title_pattern:
        return title_pattern.replace("{title}", scraped_title)
    # If "{title}" is not in the title_pattern, return title_pattern as is
    else:
        return title_pattern

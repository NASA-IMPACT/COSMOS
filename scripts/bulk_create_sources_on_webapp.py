from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import Divisions

DIVISION_MAPPING = {
    "Helio": Divisions.HELIOPHYSICS,
    "Astro": Divisions.ASTROPHYSICS,
    "PDS": Divisions.PLANETARY,
    "Earth": Divisions.EARTH_SCIENCE,
    "BPS": Divisions.BIOLOGY,
    "Multiple": Divisions.GENERAL,
}

sources = [
    {
        "Name": "Source name",
        "Link": "Base link to the source",
        "Division": "Division of the source from the spread sheet",
        "Notes": "Any notes available from the spreadsheet",
    },
]


def get_division_id(division_name):
    division_name = division_name.strip()
    return DIVISION_MAPPING.get(division_name, None)


def create_collection(source):
    name = source["Name"]
    link = source["Link"]
    division_text = source["Division"]
    notes = source["Notes"]

    division_id = get_division_id(division_text)
    if division_id is None:
        print(f"No valid division found for '{division_text}'. Skipping creation for {name}.")
        return False

    try:
        if Collection.objects.filter(name=name).exists():
            print(f"Collection with name '{name}' already exists. Skipping.")
            return False
        if Collection.objects.filter(url=link).exists():
            print(f"Collection with link '{link}' already exists. Skipping.")
            return False
        new_collection = Collection(name=name, url=link, division=division_id, notes=notes)
        new_collection.save()
        print(f"Collection '{name}' created successfully.")
        return True
    except Exception as e:
        print(f"Failed to create collection '{name}': {e}")
        return False


def main():
    created_count = 0
    for source in sources:
        if create_collection(source):
            created_count += 1
    print(f"Total new collections created: {created_count}")


if __name__ == "__main__":
    main()

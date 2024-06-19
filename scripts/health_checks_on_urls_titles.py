from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection
from sde_collections.sinequa_api import Api


def _health_check_on_urls_titles(server_name: str):
    if server_name == "test":
        url_field = "download_url"
        status_field = "present_on_test"
        title_field = "test_title"
    elif server_name == "production":
        url_field = "url1"
        status_field = "present_on_prod"
        title_field = "production_title"
    else:
        # Handle invalid server name
        raise ValueError(f"Invalid server name: {server_name}")

    api = Api(server_name=server_name)

    collection_config_folders = [
        collection.config_folder for collection in Collection.objects.all()
    ]

    for collection_config_folder in collection_config_folders:
        page = 1
        urls_server_info_dict = {}
        while True:
            response = api.query(
                page=page, collection_config_folder=collection_config_folder
            )
            if (
                response.get("cursorRowCount", 0) == 0
            ):  # Safeguard against missing 'cursorRowCount'
                break
            for record in response.get(
                "records", []
            ):  # Safeguard against missing 'records'
                url = record.get(url_field)
                title = record.get("title")
                if url and title:  # Ensure both url and title are present
                    urls_server_info_dict[url] = {"title": title}
            page += 1
        print(
            f"Finished collecting URLs from {server_name} server for config folder {collection_config_folder}"
        )

        collection_object = Collection.objects.filter(
            config_folder=collection_config_folder
        )
        candidate_urls_objects = CandidateURL.objects.filter(
            collection=collection_object[0]
        )
        for candidate_urls_object in candidate_urls_objects:
            is_present_on_server = (
                candidate_urls_object.url in urls_server_info_dict.keys()
            )
            if getattr(candidate_urls_object, status_field) != is_present_on_server:
                setattr(candidate_urls_object, status_field, is_present_on_server)
            try:
                setattr(
                    candidate_urls_object,
                    title_field,
                    urls_server_info_dict.get(candidate_urls_object.url)["title"],
                )
            except TypeError:
                setattr(candidate_urls_object, title_field, "Unavailable")
            candidate_urls_object.save()
        print(
            f"Finished updating urls within collection config folder {collection_config_folder}"
        )


if __name__ == "__main__":
    _health_check_on_urls_titles(server_name="test")
    _health_check_on_urls_titles(server_name="production")

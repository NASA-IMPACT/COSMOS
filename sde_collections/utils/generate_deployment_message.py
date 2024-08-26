from ..models.collection import Collection


def generate_deployment_message(collection_config_folders):
    # generate deployment message
    collections = Collection.objects.filter(config_folder__in=collection_config_folders)

    message_start = """:rocket: Production Deployment Update :rocket:
Hello Team,

I'm pleased to announce that we have successfully moved several key collections
to our production environment as part of our latest deployment! :tada:\n
Collections Now Live in Prod:\n"""

    message_middle = "\n\n".join([f"- {collection.name} | {collection.server_url_prod}" for collection in collections])

    message_end = """
If you find something needs changing, please let us know.

Dev Team"""

    content = f"{message_start}\n{message_middle}\n{message_end}"

    return content

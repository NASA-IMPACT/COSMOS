from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Return JSON response for all exceptions.
    """
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "error": response.data,
            "status_code": response.status_code,
        }
        response.content_type = "application/json"

    return response

import boto3
from django.conf import settings


def get_boto3_session():
    """Default credential chain (instance role in AWS); explicit SDE keys only if set (local dev).

    Deliberately does NOT read the DJANGO_AWS_* / AWS_ACCESS_KEY_ID settings — those are the
    django-storages static-assets credentials, a different scope (and absent under test settings).
    """
    if settings.SDE_AWS_ACCESS_KEY_ID and settings.SDE_AWS_SECRET_ACCESS_KEY:
        return boto3.Session(
            aws_access_key_id=settings.SDE_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SDE_AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
    return boto3.Session(region_name=settings.AWS_REGION)

"""Dispatch a WEB_COSMOS indexing run via cross-account ecs:RunTask.

COSMOS assumes CosmosIndexingDispatchRole-{env} and starts one Fargate task with a
command override (not container-env overrides). Target->endpoint resolution is
tier-capped on the indexer side, so a dev dispatch can never reach prod AOSS.
"""

import boto3
from django.conf import settings

from ..utils.aws import get_boto3_session


def run_index_task(collection, target: str, run_id: str) -> str:
    """Assume the dispatch role and RunTask; returns the task ARN."""
    for name in ("INDEXING_DISPATCH_ROLE_ARN", "INDEXING_ECS_CLUSTER", "INDEXING_TASK_FAMILY"):
        if not getattr(settings, name):
            raise ValueError(f"{name} is not configured — cannot dispatch an index run")

    sts = get_boto3_session().client("sts")
    session_name = f"cosmos-index-{target}-{collection.config_folder}"[:64]
    credentials = sts.assume_role(
        RoleArn=settings.INDEXING_DISPATCH_ROLE_ARN,
        RoleSessionName=session_name,
    )["Credentials"]

    ecs = boto3.client(
        "ecs",
        region_name=settings.AWS_REGION,
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )

    kwargs = {
        "cluster": settings.INDEXING_ECS_CLUSTER,
        "taskDefinition": settings.INDEXING_TASK_FAMILY,
        "launchType": "FARGATE",
        "count": 1,
        "overrides": {
            "containerOverrides": [
                {
                    "name": settings.INDEXING_CONTAINER_NAME,
                    # An ECS command override replaces the task definition's command
                    # wholesale, and the indexer image has no ENTRYPOINT — so the
                    # executable must be restated here, not just the flags.
                    "command": [
                        "python3", "api_scraper.py",
                        "--source", "WEB_COSMOS",
                        "--collection", collection.config_folder,
                        "--target", target,
                        "--run-id", run_id,
                    ],
                }
            ]
        },
    }
    if settings.INDEXING_SUBNETS:
        kwargs["networkConfiguration"] = {
            "awsvpcConfiguration": {
                "subnets": [s for s in settings.INDEXING_SUBNETS.split(",") if s],
                "securityGroups": [s for s in settings.INDEXING_SECURITY_GROUPS.split(",") if s],
                "assignPublicIp": "ENABLED",
            }
        }

    response = ecs.run_task(**kwargs)
    if response.get("failures"):
        raise RuntimeError(f"ecs:RunTask reported failures: {response['failures']}")
    return response["tasks"][0]["taskArn"]

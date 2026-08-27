"""Dispatch a WEB_COSMOS indexing run via cross-account ecs:RunTask.

COSMOS assumes CosmosIndexingDispatchRole-{env} (or, with no role configured, uses its
own pipeline credentials — local dev) and starts one Fargate task with a command
override (not container-env overrides). Target->endpoint resolution is
tier-capped on the indexer side, so a dev dispatch can never reach prod AOSS.
"""

import boto3
from django.conf import settings

from ..utils.aws import get_boto3_session


def _ecs_client(collection, target: str):
    """ECS client under the dispatch role when INDEXING_DISPATCH_ROLE_ARN is set (the
    deployed path: the instance role is the only principal the role trusts). With it
    blank, the pipeline session's own credentials are used directly — local dev with
    SDE_AWS_* keys that already carry ecs:RunTask + iam:PassRole."""
    session = get_boto3_session()
    if not settings.INDEXING_DISPATCH_ROLE_ARN:
        return session.client("ecs")

    session_name = f"cosmos-index-{target}-{collection.config_folder}"[:64]
    credentials = session.client("sts").assume_role(
        RoleArn=settings.INDEXING_DISPATCH_ROLE_ARN,
        RoleSessionName=session_name,
    )["Credentials"]
    return boto3.client(
        "ecs",
        region_name=settings.AWS_REGION,
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )


def run_index_task(collection, target: str, run_id: str) -> str:
    """Assume the dispatch role (if configured) and RunTask; returns the task ARN."""
    for name in ("INDEXING_ECS_CLUSTER", "INDEXING_TASK_FAMILY"):
        if not getattr(settings, name):
            raise ValueError(f"{name} is not configured — cannot dispatch an index run")

    ecs = _ecs_client(collection, target)

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
                        "python3",
                        "api_scraper.py",
                        "--source",
                        "WEB_COSMOS",
                        "--collection",
                        collection.config_folder,
                        "--target",
                        target,
                        "--run-id",
                        run_id,
                    ],
                }
            ]
        },
    }
    subnets = [s for s in settings.INDEXING_SUBNETS.split(",") if s]
    security_groups = [s for s in settings.INDEXING_SECURITY_GROUPS.split(",") if s]
    if subnets or security_groups:
        if not (subnets and security_groups):
            raise ValueError("INDEXING_SUBNETS and INDEXING_SECURITY_GROUPS must both be set (or both blank)")
        kwargs["networkConfiguration"] = {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": security_groups,
                # Public subnets (dev's default VPC) need a public IP to reach S3/AOSS;
                # a private subnet with NAT should set INDEXING_ASSIGN_PUBLIC_IP=False.
                "assignPublicIp": "ENABLED" if settings.INDEXING_ASSIGN_PUBLIC_IP else "DISABLED",
            }
        }

    response = ecs.run_task(**kwargs)
    if response.get("failures"):
        raise RuntimeError(f"ecs:RunTask reported failures: {response['failures']}")
    return response["tasks"][0]["taskArn"]

"""Deliver a job JSON into the crawler's inbox on EC2 via SSM.

Mirrors sde-crawl4ai-scraper-v1/scripts/drop_job.sh: AWS-RunShellScript writing to
{CRAWLER_INBOX_PATH}/{config_folder}.json, chowned to ec2-user. The JSON is passed
through shlex.quote — seed URLs contain characters that would break a heredoc — and
written to a .tmp path first so the inbox watcher can never read a partial file.
"""

import json
import shlex

from django.conf import settings

from ..utils.aws import get_boto3_session
from .job_builder import build_job_json


def send_job_to_crawler(collection) -> str:
    """Build and drop the job JSON for `collection`; returns the SSM command id."""
    job_json = json.dumps(build_job_json(collection))
    dest = f"{settings.CRAWLER_INBOX_PATH}/{collection.config_folder}.json"
    script = (
        f"printf '%s' {shlex.quote(job_json)} > {shlex.quote(dest + '.tmp')}\n"
        f"chown ec2-user:ec2-user {shlex.quote(dest + '.tmp')}\n"
        f"mv -f {shlex.quote(dest + '.tmp')} {shlex.quote(dest)}\n"
    )

    ssm = get_boto3_session().client("ssm")
    response = ssm.send_command(
        InstanceIds=[settings.CRAWLER_INSTANCE_ID],
        DocumentName="AWS-RunShellScript",
        Comment=f"COSMOS scrape dispatch: {collection.config_folder}"[:100],
        Parameters={"commands": [script]},
    )
    return response["Command"]["CommandId"]

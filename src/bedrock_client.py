from __future__ import annotations
import boto3
from botocore.config import Config
from src import config

_client = None

_RETRY_CONFIG = Config(retries={"max_attempts": 8, "mode": "adaptive"})

def get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "bedrock-runtime",
            region_name=config.BEDROCK_REGION,
            config=_RETRY_CONFIG,
        )
    return _client

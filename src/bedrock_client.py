from __future__ import annotations
import boto3
from src import config

_client = None

def get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=config.BEDROCK_REGION)
    return _client

"""
Shared Amazon Bedrock Runtime client.

A single boto3 client instance is created lazily on first use and reused
across all requests — one connection pool for the lifetime of the process.
"""
from __future__ import annotations

import boto3

from src import config

_client = None


def get_client():
    """Return the shared boto3 bedrock-runtime client."""
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=config.BEDROCK_REGION)
    return _client

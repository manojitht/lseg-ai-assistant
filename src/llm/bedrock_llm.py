from __future__ import annotations
import json
import logging
from botocore.exceptions import ClientError
from src import config
from src.bedrock_client import get_client

logger = logging.getLogger(__name__)


def invoke(prompt: dict) -> str:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens":        config.MAX_TOKENS,
        "temperature":       config.TEMPERATURE,
        "system":            prompt["system"],
        "messages":          prompt["messages"],
    })
    try:
        response = get_client().invoke_model(
            modelId=config.LLM_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ThrottlingException":
            logger.warning("bedrock llm throttled after retries exhausted")
            raise RateLimitError("Bedrock LLM rate limit exceeded — try again shortly.") from e
        raise
    return json.loads(response["body"].read())["content"][0]["text"]


class RateLimitError(Exception):
    pass

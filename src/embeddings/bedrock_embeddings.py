from __future__ import annotations
import json
import logging
from botocore.exceptions import ClientError
from src import config
from src.bedrock_client import get_client
from src.llm.bedrock_llm import RateLimitError

logger = logging.getLogger(__name__)


def embed(text: str) -> list[float]:
    body = json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
    try:
        response = get_client().invoke_model(
            modelId=config.EMBEDDING_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ThrottlingException":
            logger.warning("bedrock embeddings throttled after retries exhausted")
            raise RateLimitError("Bedrock embeddings rate limit exceeded — try again shortly.") from e
        raise
    return json.loads(response["body"].read())["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    return [embed(t) for t in texts]

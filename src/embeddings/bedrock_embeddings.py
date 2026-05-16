"""
Embedding logic — Amazon Bedrock Titan Embeddings v2.

Model  : amazon.titan-embed-text-v2:0
Output : 1024-dim normalised float vector (unit vector → inner product = cosine)
Auth   : IAM role attached to ECS task (LsegEcsTaskRole)
Region : us-east-1
"""
from __future__ import annotations

import json

from src import config
from src.bedrock_client import get_client


def embed(text: str) -> list[float]:
    """Embed a single string and return a 1024-dim normalised vector."""
    body = json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
    response = get_client().invoke_model(
        modelId=config.EMBEDDING_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(response["body"].read())["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts sequentially (Titan v2 has no batch endpoint)."""
    return [embed(t) for t in texts]

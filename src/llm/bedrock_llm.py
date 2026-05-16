from __future__ import annotations
import json
from src import config
from src.bedrock_client import get_client


def invoke(prompt: dict) -> str:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens":        config.MAX_TOKENS,
        "temperature":       config.TEMPERATURE,
        "system":            prompt["system"],
        "messages":          prompt["messages"],
    })
    response = get_client().invoke_model(
        modelId=config.LLM_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(response["body"].read())["content"][0]["text"]

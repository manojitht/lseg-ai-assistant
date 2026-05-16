"""
LLM invocation — Amazon Bedrock Claude 3.5 Sonnet (Messages API).

Model  : anthropic.claude-3-5-sonnet-20241022-v2:0
Auth   : IAM role attached to ECS task (LsegEcsTaskRole)
Region : us-east-1
"""
from __future__ import annotations

import json

from src import config
from src.bedrock_client import get_client


def invoke(prompt: dict) -> str:
    """
    Call Claude 3.5 Sonnet via the Bedrock Messages API.

    prompt format (from prompt_templates.build_prompt):
      { "system": str, "messages": [{"role": "user", "content": str}] }

    Returns the assistant's reply text.
    """
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

import os

BEDROCK_REGION     = os.environ.get("BEDROCK_REGION", "eu-west-2")
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
LLM_MODEL_ID       = "anthropic.claude-3-7-sonnet-20250219-v1:0"

FAISS_INDEX_PATH   = os.environ.get("FAISS_INDEX_PATH", ".cache/faiss_index")

CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.30"))
TOP_K                = int(os.environ.get("TOP_K", "5"))

MAX_TOKENS  = 5000
TEMPERATURE = 0.0   # deterministic — compliance requirement

DOCS_DIR = os.environ.get("DOCS_DIR", "docs")

"""
Entry point — starts the FastAPI server via uvicorn.

Local (mock mode, no AWS credentials needed):
    uv run python main.py

Live AWS mode (real Bedrock + real embeddings):
    AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... uv run python main.py

The app will:
  1. Load / build the FAISS vector index from docs/
  2. Start serving on http://localhost:8000
  3. Interactive docs available at http://localhost:8000/docs
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )

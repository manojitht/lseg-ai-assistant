import boto3
import json
import os

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION               = os.environ["AWS_REGION"]
EMBEDDING_MODEL_ID   = "amazon.titan-embed-text-v2:0"
OPENSEARCH_ENDPOINT  = os.environ["OPENSEARCH_ENDPOINT"]
INDEX_NAME           = os.environ.get("OPENSEARCH_INDEX", "lseg-rag-index")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
s3      = boto3.client("s3")


def _get_os_client():
    session = boto3.Session()
    auth = AWS4Auth(region=REGION, service="aoss", credentials=session.get_credentials())
    return OpenSearch(
        hosts=[{"host": OPENSEARCH_ENDPOINT, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        connection_class=RequestsHttpConnection,
    )


def _embed(text: str) -> list[float]:
    body = json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
    resp = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(resp["body"].read())["embedding"]


def _chunk_document(content: str, filename: str) -> list[dict]:
    """Replicates the chunker logic from src/ingestion/chunker.py."""
    import re
    chunks = []
    if filename.endswith(".md"):
        # SOP: split on ## headers
        parts   = re.split(r"(?m)^##\s+", content)
        sop_id  = filename.split("-")[0] + "-" + filename.split("-")[1]
        for part in parts[1:]:
            lines   = part.strip().splitlines()
            heading = lines[0].strip() if lines else "unknown"
            body    = "\n".join(lines[1:]).strip()
            chunks.append({
                "text":     f"## {heading}\n\n{body}",
                "source":   sop_id,
                "section":  heading,
                "doc_type": "sop",
            })
    elif filename.endswith(".csv"):
        # Tickets: one chunk per row
        import csv, io
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            text = (
                f"{row['ID']} | Category: {row['Category']} | "
                f"Priority: {row['Priority']} | Status: {row['Status']} | "
                f"Description: {row['Description']}"
            )
            chunks.append({
                "text":     text,
                "source":   row["ID"],
                "section":  "",
                "doc_type": "ticket",
                "category": row["Category"],
                "priority": row["Priority"],
                "status":   row["Status"],
            })
    return chunks


def handler(event, context):
    """Lambda entry point — called on S3 PUT events."""
    os_client = _get_os_client()

    for record in event.get("Records", []):
        bucket   = record["s3"]["bucket"]["name"]
        key      = record["s3"]["object"]["key"]
        print(f"Processing s3://{bucket}/{key}")

        obj     = s3.get_object(Bucket=bucket, Key=key)
        content = obj["Body"].read().decode("utf-8")
        chunks  = _chunk_document(content, key)

        for chunk in chunks:
            embedding = _embed(chunk["text"])
            doc = {**chunk, "embedding": embedding}
            doc_id = f"{chunk['source']}_{chunk.get('section', '')}".replace(" ", "_")
            os_client.index(index=INDEX_NAME, id=doc_id, body=doc)

        print(f"Indexed {len(chunks)} chunks from {key}")

    return {"statusCode": 200, "body": "Ingestion complete"}

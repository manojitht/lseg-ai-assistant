"""
PSEUDOCODE — Amazon OpenSearch Serverless Setup
Creates the vector search collection and k-NN index.
Replaces FAISS in production — the retriever interface is unchanged.
"""
import boto3
import json
import time

REGION          = "eu-west-2"
COLLECTION_NAME = "lseg-rag-store"
INDEX_NAME      = "lseg-rag-index"
ACCOUNT_ID      = "<your-account-id>"

aoss = boto3.client("opensearchserverless", region_name=REGION)

aoss.create_security_policy(
    name=f"{COLLECTION_NAME}-enc",
    type="encryption",
    policy=json.dumps({
        "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]}],
        "AWSOwnedKey": True,
    }),
)

aoss.create_security_policy(
    name=f"{COLLECTION_NAME}-net",
    type="network",
    policy=json.dumps([{
        "Rules": [
            {"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]},
            {"ResourceType": "dashboard",  "Resource": [f"collection/{COLLECTION_NAME}"]},
        ],
        "AllowFromPublic": True,  # restrict to VPC CIDR in production
    }]),
)

response = aoss.create_collection(
    name=COLLECTION_NAME,
    type="VECTORSEARCH",
    description="LSEG DSM RAG vector store",
)
collection_id       = response["createCollectionDetail"]["id"]
collection_endpoint = f"{collection_id}.{REGION}.aoss.amazonaws.com"
print(f"Collection endpoint: {collection_endpoint}")

# Wait for collection to be active (typically 2-3 minutes)
time.sleep(180)

aoss.create_access_policy(
    name=f"{COLLECTION_NAME}-access",
    type="data",
    policy=json.dumps([{
        "Rules": [
            {
                "ResourceType": "index",
                "Resource":     [f"index/{COLLECTION_NAME}/*"],
                "Permission":   ["aoss:ReadDocument", "aoss:WriteDocument",
                                 "aoss:CreateIndex", "aoss:DescribeIndex"],
            },
            {
                "ResourceType": "collection",
                "Resource":     [f"collection/{COLLECTION_NAME}"],
                "Permission":   ["aoss:DescribeCollectionItems"],
            },
        ],
        "Principal": [
            f"arn:aws:iam::{ACCOUNT_ID}:role/LsegEcsTaskRole",
            f"arn:aws:iam::{ACCOUNT_ID}:role/LsegLambdaIngestionRole",
        ],
    }]),
)

# Uses requests + requests-aws4auth for SigV4 signing
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

session = boto3.Session()
auth = AWS4Auth(
    region=REGION,
    service="aoss",
    credentials=session.get_credentials(),
)
os_client = OpenSearch(
    hosts=[{"host": collection_endpoint, "port": 443}],
    http_auth=auth,
    use_ssl=True,
    connection_class=RequestsHttpConnection,
)

index_body = {
    "settings": {"index.knn": True},
    "mappings": {
        "properties": {
            "embedding": {
                "type":   "knn_vector",
                "dimension": 1024,
                "method": {
                    "engine":     "faiss",
                    "name":       "hnsw",
                    "space_type": "innerproduct",   # cosine on normalised vectors
                },
            },
            "text":     {"type": "text"},
            "source":   {"type": "keyword"},
            "section":  {"type": "keyword"},
            "doc_type": {"type": "keyword"},
            "category": {"type": "keyword"},
            "priority": {"type": "keyword"},
            "status":   {"type": "keyword"},
        }
    },
}
os_client.indices.create(index=INDEX_NAME, body=index_body)
print(f"Index '{INDEX_NAME}' created.")
print(f"\nSet OPENSEARCH_ENDPOINT={collection_endpoint} in SSM Parameter Store.")

"""
PSEUDOCODE — AWS S3 Setup
Creates the lseg-ai-docs bucket and uploads all source documents.
Not executed locally; documents are read from docs/ directly.
"""
import boto3
import os

S3_BUCKET = "lseg-ai-docs"
REGION    = "eu-west-2"
DOCS_DIR  = "docs"

s3 = boto3.client("s3", region_name=REGION)

# Create bucket
s3.create_bucket(
    Bucket=S3_BUCKET,
    CreateBucketConfiguration={"LocationConstraint": REGION},
)

# Block all public access
s3.put_public_access_block(
    Bucket=S3_BUCKET,
    PublicAccessBlockConfiguration={
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True,
    },
)

# Enable versioning so document history is preserved
s3.put_bucket_versioning(
    Bucket=S3_BUCKET,
    VersioningConfiguration={"Status": "Enabled"},
)

# Upload all docs
for filename in os.listdir(DOCS_DIR):
    filepath = os.path.join(DOCS_DIR, filename)
    if os.path.isfile(filepath):
        s3.upload_file(filepath, S3_BUCKET, filename)
        print(f"Uploaded: {filename}")

print(f"S3 bucket '{S3_BUCKET}' ready.")

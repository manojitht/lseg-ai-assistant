import json

ACCOUNT_ID      = "<your-account-id>"
REGION          = "eu-west-2"
COLLECTION_ARN  = f"arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/<collection-id>"

LAMBDA_TRUST = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole",
    }],
}

LAMBDA_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockEmbeddings",
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": [
                f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0"
            ],
        },
        {
            "Sid": "S3ReadDocs",
            "Effect": "Allow",
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::lseg-ai-docs/*"],
        },
        {
            "Sid": "OpenSearchWrite",
            "Effect": "Allow",
            "Action": ["aoss:APIAccessAll"],
            "Resource": [COLLECTION_ARN],
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": ["arn:aws:logs:*:*:*"],
        },
    ],
}

ECS_TRUST = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole",
    }],
}

ECS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockEmbeddingsAndLLM",
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": [
                f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0",
                f"arn:aws:bedrock:{REGION}::foundation-model/anthropic.claude-3-7-sonnet-20250219-v1:0",
            ],
        },
        {
            "Sid": "OpenSearchRead",
            "Effect": "Allow",
            "Action": ["aoss:APIAccessAll"],
            "Resource": [COLLECTION_ARN],
        },
        {
            "Sid": "S3ReadDocs",
            "Effect": "Allow",
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::lseg-ai-docs/*"],
        },
        {
            "Sid": "SSMConfig",
            "Effect": "Allow",
            "Action": ["ssm:GetParameter", "ssm:GetParameters"],
            "Resource": [f"arn:aws:ssm:{REGION}:{ACCOUNT_ID}:parameter/lseg-ai/*"],
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": ["arn:aws:logs:*:*:*"],
        },
    ],
}

if __name__ == "__main__":
    print("=== LsegLambdaIngestionRole — Trust Policy ===")
    print(json.dumps(LAMBDA_TRUST, indent=2))
    print("\n=== LsegLambdaIngestionRole — Permission Policy ===")
    print(json.dumps(LAMBDA_POLICY, indent=2))
    print("\n=== LsegEcsTaskRole — Trust Policy ===")
    print(json.dumps(ECS_TRUST, indent=2))
    print("\n=== LsegEcsTaskRole — Permission Policy ===")
    print(json.dumps(ECS_POLICY, indent=2))

#!/usr/bin/env python3
import argparse
import json
import time
from urllib.parse import urlparse

import boto3
try:
    from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection
    from opensearchpy.exceptions import AuthorizationException, TransportError
except ImportError as exc:
    raise SystemExit("opensearch-py is required. Install it with `pip install opensearch-py`.") from exc


FORBIDDEN_HINT = (
    "OpenSearch Serverless 403 Forbidden: 현재 AWS principal이 data access policy의 Principal에 "
    "포함되어 있는지 확인하세요. aws sts get-caller-identity로 ARN을 확인하고, "
    "Terraform access policy Principal에 추가해야 합니다. IAM policy에 aoss:APIAccessAll도 필요합니다."
)


def normalize_endpoint(endpoint):
    if endpoint.startswith("https://"):
        return endpoint.rstrip("/")
    return f"https://{endpoint.rstrip('/')}"


def mapping(dimension):
    return {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": dimension,
                    "method": {"name": "hnsw", "engine": "faiss", "space_type": "l2"},
                },
                "text": {"type": "text"},
                "metadata": {"type": "text", "index": False},
            }
        },
    }


def build_client(endpoint, region, profile):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    credentials = session.get_credentials()
    if credentials is None:
        raise SystemExit("AWS credentials not found for OpenSearch index creation.")

    caller_identity = session.client("sts", region_name=region).get_caller_identity()
    print(f"AWS caller identity: {json.dumps(caller_identity, ensure_ascii=False)}")
    print(f"OpenSearch endpoint: {endpoint}")
    print(f"AWS region: {region}")

    parsed = urlparse(endpoint)
    auth = AWSV4SignerAuth(credentials, region, "aoss")
    client = OpenSearch(
        hosts=[{"host": parsed.hostname, "port": parsed.port or 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
    )
    return client


def handle_transport_error(exc, index_name):
    info = getattr(exc, "info", "")
    status_code = getattr(exc, "status_code", None)
    error = getattr(exc, "error", "")
    if status_code == 403 or "AuthorizationException" in str(info) or "AuthorizationException" in str(error):
        print(str(exc))
        raise SystemExit(f"Failed to create index {index_name}: 403 Forbidden\n{FORBIDDEN_HINT}")
    return status_code, error, info


def ensure_index(endpoint, index_name, region, dimension, profile):
    endpoint = normalize_endpoint(endpoint)
    print(f"OpenSearch index name: {index_name}")
    client = build_client(endpoint, region, profile)
    request_body = mapping(dimension)

    for attempt in range(1, 25):
        try:
            exists = client.indices.exists(index=index_name)
        except AuthorizationException as exc:
            print(str(exc))
            raise SystemExit(f"Failed to create index {index_name}: 403 Forbidden\n{FORBIDDEN_HINT}")
        except TransportError as exc:
            status_code, error, info = handle_transport_error(exc, index_name)
            print(f"Index exists check failed. attempt={attempt} status={status_code} error={error} info={info}")
            time.sleep(5)
            continue

        if exists:
            print(f"Index already exists: {index_name}")
            return

        try:
            client.indices.create(index=index_name, body=request_body)
            print(f"Index create accepted: {index_name}")
        except AuthorizationException as exc:
            print(str(exc))
            raise SystemExit(f"Failed to create index {index_name}: 403 Forbidden\n{FORBIDDEN_HINT}")
        except TransportError as exc:
            status_code, error, info = handle_transport_error(exc, index_name)
            if status_code == 400 and "resource_already_exists_exception" in str(info):
                print(f"Index already exists: {index_name}")
                return
            print(
                f"Waiting for collection/access policy readiness. attempt={attempt} "
                f"status={status_code} error={error} info={info}"
            )
            time.sleep(5)
            continue

        for verify_attempt in range(1, 25):
            try:
                if client.indices.exists(index=index_name):
                    print(f"Index is ready: {index_name}")
                    return
            except AuthorizationException as exc:
                print(str(exc))
                raise SystemExit(f"Failed to create index {index_name}: 403 Forbidden\n{FORBIDDEN_HINT}")
            except TransportError as exc:
                status_code, error, info = handle_transport_error(exc, index_name)
                print(
                    f"Waiting for index visibility. attempt={verify_attempt} "
                    f"status={status_code} error={error} info={info}"
                )
            time.sleep(5)
        raise SystemExit(f"Index {index_name} was not visible after retries")

    raise SystemExit(f"Failed to create index {index_name}: retries exhausted")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--index-name", default="codebuddy-index")
    parser.add_argument("--region", default="ap-northeast-2")
    parser.add_argument("--dimension", type=int, default=1024)
    parser.add_argument("--profile", default="")
    args = parser.parse_args()
    ensure_index(args.endpoint, args.index_name, args.region, args.dimension, args.profile or None)


if __name__ == "__main__":
    main()

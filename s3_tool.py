#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def load_dotenv_if_present(dotenv_path: str = ".env"):
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def create_s3_client():
    load_dotenv_if_present()
    region = os.getenv("AWS_REGION", "us-east-1")
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    return boto3.client("s3", region_name=region, endpoint_url=endpoint_url)


def upload_file(client, bucket: str, local_path: str, object_key: str):
    try:
        client.upload_file(local_path, bucket, object_key)
        print(f"OK: uploaded '{local_path}' to s3://{bucket}/{object_key}")
    except ClientError as exc:
        print(f"ERROR: upload failed: {exc}")
        raise SystemExit(1) from exc


def list_objects(client, bucket: str, prefix: str):
    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    except ClientError as exc:
        print(f"ERROR: list failed: {exc}")
        raise SystemExit(1) from exc

    contents = response.get("Contents", [])
    if not contents:
        print("Bucket/prefix is empty.")
        return

    for item in contents:
        print(f"{item['Key']}\t{item['Size']} bytes")


def download_file(client, bucket: str, object_key: str, output_path: str):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        client.download_file(bucket, object_key, output_path)
        print(f"OK: downloaded s3://{bucket}/{object_key} -> '{output_path}'")
    except ClientError as exc:
        print(f"ERROR: download failed: {exc}")
        raise SystemExit(1) from exc


def build_parser():
    parser = argparse.ArgumentParser(description="Simple S3 CLI example")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload = subparsers.add_parser("upload", help="Upload file to S3")
    upload.add_argument("--bucket", required=True)
    upload.add_argument("--file", required=True, help="Local path")
    upload.add_argument("--key", required=True, help="S3 object key")

    ls_cmd = subparsers.add_parser("list", help="List objects in S3 bucket")
    ls_cmd.add_argument("--bucket", required=True)
    ls_cmd.add_argument("--prefix", default="")

    download = subparsers.add_parser("download", help="Download file from S3")
    download.add_argument("--bucket", required=True)
    download.add_argument("--key", required=True)
    download.add_argument("--out", required=True, help="Local output path")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    client = create_s3_client()

    if args.command == "upload":
        upload_file(client, args.bucket, args.file, args.key)
    elif args.command == "list":
        list_objects(client, args.bucket, args.prefix)
    elif args.command == "download":
        download_file(client, args.bucket, args.key, args.out)


if __name__ == "__main__":
    main()

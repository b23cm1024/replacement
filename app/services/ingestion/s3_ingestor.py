"""
S3 Bucket Ingestor
------------------
Full pipeline: S3 Bucket → Download Files → Existing Ingestion Pipeline
           → Chunking → Embedding → PostgreSQL (pgvector) storage.

Reads all supported document files from a given S3 bucket prefix,
downloads each one to a temp directory, and passes them through the
same document_ingestor pipeline used for manual uploads.

Entry point: ingest_from_s3(bucket_name, prefix) -> dict
"""

import os
import tempfile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

from app.services.ingestion.document_ingestor import ingest_document

# Supported file extensions (same as the /upload endpoint)
SUPPORTED_EXTENSIONS = {"pdf", "docx", "pptx", "xlsx", "md"}


def _get_s3_client():
    """
    Build an S3 client. Uses env vars for credentials.
    On EC2 with an IAM Role attached, boto3 picks up credentials automatically
    without needing explicit keys.
    """
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "ap-south-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def list_s3_files(bucket_name: str, prefix: str = "") -> list[dict]:
    """
    List all supported document files under a given S3 prefix.

    Returns a list of dicts with keys:
        - key:  full S3 object key  (e.g. "raw_data/report.pdf")
        - name: just the filename   (e.g. "report.pdf")
        - ext:  file extension      (e.g. "pdf")
        - size: file size in bytes
    """
    client = _get_s3_client()
    files = []

    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # Skip "folder" placeholder objects (keys ending with /)
            if key.endswith("/"):
                continue

            filename = key.split("/")[-1]
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

            if ext in SUPPORTED_EXTENSIONS:
                files.append({
                    "key":  key,
                    "name": filename,
                    "ext":  ext,
                    "size": obj["Size"],
                })

    return files


def ingest_from_s3(bucket_name: str, prefix: str = "raw_data/") -> dict:
    """
    End-to-end S3 ingestion pipeline.

    For every supported file found under bucket_name/prefix:
      1. Download to a temp directory
      2. Run through the existing document_ingestor pipeline
         (parse → vision → chunk → embed → store in PostgreSQL)
      3. Clean up temp file

    Args:
        bucket_name: S3 bucket name  (e.g. "zephyr-wings")
        prefix:      S3 key prefix   (e.g. "raw_data/")

    Returns:
        {
            "files_found":    int,
            "files_ingested": int,
            "files_skipped":  int,
            "total_chunks":   int,
            "results":        list of per-file result dicts
        }
    """
    print(f"\n{'='*60}")
    print(f"[S3 Ingestor] Starting ingestion from s3://{bucket_name}/{prefix}")
    print(f"{'='*60}")

    client = _get_s3_client()

    # 1. List all supported files in the prefix
    print("[S3 Ingestor] Step 1/3 — Listing files in S3 bucket...")
    try:
        files = list_s3_files(bucket_name, prefix)
    except NoCredentialsError:
        raise RuntimeError(
            "AWS credentials not found. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY environment variables, or attach an "
            "IAM Role to the EC2 instance."
        )
    except ClientError as e:
        raise RuntimeError(f"S3 access error: {e.response['Error']['Message']}")

    print(f"[S3 Ingestor]   -> {len(files)} supported file(s) found.")

    if not files:
        return {
            "files_found":    0,
            "files_ingested": 0,
            "files_skipped":  0,
            "total_chunks":   0,
            "results":        [],
        }

    # 2. Download and ingest each file
    print("[S3 Ingestor] Step 2/3 — Downloading and ingesting files...")
    results = []
    files_ingested = 0
    files_skipped  = 0
    total_chunks   = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        images_base_dir = os.path.join(tmp_dir, "images")
        os.makedirs(images_base_dir, exist_ok=True)

        for file_info in files:
            key      = file_info["key"]
            filename = file_info["name"]
            local_path = os.path.join(tmp_dir, filename)
            image_dir  = os.path.join(images_base_dir, os.path.splitext(filename)[0])

            print(f"\n[S3 Ingestor]   Downloading: s3://{bucket_name}/{key}")
            try:
                client.download_file(bucket_name, key, local_path)
                print(f"[S3 Ingestor]   -> Downloaded to {local_path} ({file_info['size']} bytes)")

                result = ingest_document(local_path, image_dir)

                results.append({
                    "s3_key":        key,
                    "filename":      filename,
                    "status":        "success",
                    "source_id":     result["source_id"],
                    "chunks_stored": result["chunks_stored"],
                })
                files_ingested += 1
                total_chunks   += result["chunks_stored"]

            except Exception as e:
                print(f"[S3 Ingestor]   [ERROR] Failed to ingest '{filename}': {e}")
                results.append({
                    "s3_key":   key,
                    "filename": filename,
                    "status":   "error",
                    "error":    str(e),
                })
                files_skipped += 1

    # 3. Summary
    print(f"\n[S3 Ingestor] Step 3/3 — Done!")
    print(f"[S3 Ingestor] Ingested: {files_ingested} files | "
          f"Skipped: {files_skipped} | Total chunks: {total_chunks}")
    print(f"{'='*60}\n")

    return {
        "files_found":    len(files),
        "files_ingested": files_ingested,
        "files_skipped":  files_skipped,
        "total_chunks":   total_chunks,
        "results":        results,
    }

import os
import csv
import json
import logging
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import boto3
from botocore.client import Config

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devops-case-study-key")

UPLOAD_FOLDER = "/app/uploads"
PROCESSED_FOLDER = "/app/processed"
ALLOWED_EXTENSIONS = {"csv"}

# ── Storage config ────────────────────────────────────────────────────────────
# Supports three modes controlled by env vars:
#   1. MinIO  (STORAGE_BACKEND=minio)  – for local Minikube testing
#   2. AWS S3 (STORAGE_BACKEND=s3)    – for production
#   3. Local  (STORAGE_BACKEND=local) – no upload, file-only
STORAGE_BACKEND   = os.environ.get("STORAGE_BACKEND", "local")   # minio | s3 | local
S3_BUCKET         = os.environ.get("S3_BUCKET", "csv-uploads")
AWS_REGION        = os.environ.get("AWS_REGION", "us-east-1")

# MinIO specific settings
MINIO_ENDPOINT    = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY  = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY  = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def get_s3_client():
    """
    Returns an S3-compatible client.
    MinIO uses the same boto3 API as AWS S3 – only the endpoint differs.
    """
    if STORAGE_BACKEND == "minio":
        return boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
    # AWS S3 – uses IAM role / env-var credentials
    return boto3.client("s3", region_name=AWS_REGION)


def ensure_bucket_exists(client, bucket):
    """Create bucket if it doesn't exist (MinIO only – S3 bucket pre-created)."""
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:
        client.create_bucket(Bucket=bucket)
        logger.info(f"Created bucket: {bucket}")


def upload_to_storage(filepath, filename):
    """Upload processed CSV to MinIO or S3."""
    if STORAGE_BACKEND == "local":
        logger.info("STORAGE_BACKEND=local – skipping upload")
        return None

    try:
        client = get_s3_client()
        if STORAGE_BACKEND == "minio":
            ensure_bucket_exists(client, S3_BUCKET)

        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        key = f"processed/{date_path}/{filename}"
        client.upload_file(filepath, S3_BUCKET, key)

        endpoint = MINIO_ENDPOINT if STORAGE_BACKEND == "minio" else f"https://s3.amazonaws.com"
        logger.info(f"Uploaded → {endpoint}/{S3_BUCKET}/{key}")
        return key
    except Exception as e:
        logger.error(f"Storage upload failed ({STORAGE_BACKEND}): {e}")
        return None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_csv(filepath):
    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            cleaned = [cell.strip().strip('"') for cell in row]
            if any(cleaned):
                rows.append(cleaned)
    return rows


def get_processed_files():
    meta_path = os.path.join(PROCESSED_FOLDER, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            return json.load(f)
    return []


def save_metadata(filename, row_count, storage_key):
    meta_path = os.path.join(PROCESSED_FOLDER, "metadata.json")
    files = get_processed_files()
    files.insert(0, {
        "filename": filename,
        "processed_at": datetime.utcnow().isoformat(),
        "row_count": row_count,
        "storage_key": storage_key,
        "backend": STORAGE_BACKEND,
    })
    with open(meta_path, "w") as f:
        json.dump(files, f, indent=2)


@app.route("/")
def index():
    return render_template(
        "index.html",
        processed_files=get_processed_files(),
        storage_backend=STORAGE_BACKEND,
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file selected", "danger")
        return redirect(url_for("index"))

    file = request.files["file"]
    if not file.filename:
        flash("No file selected", "danger")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Only CSV files are allowed", "danger")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    filename = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    rows = parse_csv(filepath)
    storage_key = upload_to_storage(filepath, filename)
    save_metadata(filename, len(rows), storage_key)

    return render_template(
        "result.html",
        filename=filename,
        rows=rows,
        storage_key=storage_key,
        storage_backend=STORAGE_BACKEND,
        s3_bucket=S3_BUCKET,
        minio_endpoint=MINIO_ENDPOINT,
    )


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "csv-processor",
        "storage_backend": STORAGE_BACKEND,
        "version": "1.0.0",
    }), 200


@app.route("/ready")
def ready():
    """Readiness probe – verify storage reachability."""
    if STORAGE_BACKEND != "local":
        try:
            client = get_s3_client()
            client.list_buckets()
        except Exception as e:
            return jsonify({"status": "not ready", "reason": str(e)}), 503
    return jsonify({"status": "ready"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

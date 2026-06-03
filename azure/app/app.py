import os
import csv
import json
import logging
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "azure-devops-case-study-key")

UPLOAD_FOLDER = "/app/uploads"
PROCESSED_FOLDER = "/app/processed"
ALLOWED_EXTENSIONS = {"csv"}

# Azure Blob Storage config
AZURE_STORAGE_ACCOUNT  = os.environ.get("AZURE_STORAGE_ACCOUNT", "")
AZURE_CONTAINER_NAME   = os.environ.get("AZURE_CONTAINER_NAME", "csv-uploads")
# Workload Identity client ID (set via Helm/K8s annotation)
AZURE_CLIENT_ID        = os.environ.get("AZURE_CLIENT_ID", "")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_blob_client():
    """
    Returns Azure BlobServiceClient using:
    1. Workload Identity (AKS pod - IRSA equivalent via OIDC federation)
    2. Managed Identity (VM/VMSS)
    3. Connection string fallback (local dev)
    """
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    if conn_str:
        return BlobServiceClient.from_connection_string(conn_str)

    account_url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net"
    if AZURE_CLIENT_ID:
        # Use user-assigned managed identity (Workload Identity in AKS)
        credential = ManagedIdentityCredential(client_id=AZURE_CLIENT_ID)
    else:
        # DefaultAzureCredential tries: env vars → managed identity → CLI
        credential = DefaultAzureCredential()

    return BlobServiceClient(account_url=account_url, credential=credential)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_csv(filepath):
    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            cleaned = [cell.strip().strip('"') for cell in row]
            if cleaned:
                rows.append(cleaned)
    return rows


def upload_to_azure_blob(filepath, filename):
    """Upload processed CSV to Azure Blob Storage."""
    try:
        client = get_blob_client()
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        blob_name = f"processed/{date_path}/{filename}"

        container_client = client.get_container_client(AZURE_CONTAINER_NAME)
        with open(filepath, "rb") as data:
            container_client.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True,
                metadata={
                    "uploaded_by": "csv-processor",
                    "environment": os.environ.get("APP_ENV", "production"),
                }
            )
        blob_url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}"
        logger.info(f"Uploaded {filename} → {blob_url}")
        return blob_name, blob_url
    except Exception as e:
        logger.error(f"Azure Blob upload failed: {e}")
        return None, None


def get_processed_files():
    files = []
    meta_path = os.path.join(PROCESSED_FOLDER, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            files = json.load(f)
    return files


def save_processed_metadata(filename, row_count, blob_name, blob_url):
    meta_path = os.path.join(PROCESSED_FOLDER, "metadata.json")
    files = get_processed_files()
    files.insert(0, {
        "filename": filename,
        "processed_at": datetime.utcnow().isoformat(),
        "row_count": row_count,
        "blob_name": blob_name,
        "blob_url": blob_url,
    })
    with open(meta_path, "w") as f:
        json.dump(files, f, indent=2)


@app.route("/")
def index():
    return render_template("index.html", processed_files=get_processed_files())


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file selected", "danger")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "danger")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        rows = parse_csv(filepath)
        blob_name, blob_url = upload_to_azure_blob(filepath, filename)
        save_processed_metadata(filename, len(rows), blob_name, blob_url)

        return render_template("result.html", filename=filename, rows=rows,
                               blob_name=blob_name, blob_url=blob_url)

    flash("Only CSV files are allowed", "danger")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "csv-processor", "platform": "azure"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

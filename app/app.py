import os
import csv
import json
import boto3
import logging
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devops-case-study-key")

UPLOAD_FOLDER = "/app/uploads"
PROCESSED_FOLDER = "/app/processed"
ALLOWED_EXTENSIONS = {"csv"}
S3_BUCKET = os.environ.get("S3_BUCKET", "devops-csv-uploads")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def upload_to_s3(filepath, filename):
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3_key = f"processed/{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"
        s3.upload_file(filepath, S3_BUCKET, s3_key)
        logger.info(f"Uploaded {filename} to s3://{S3_BUCKET}/{s3_key}")
        return s3_key
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return None


def get_processed_files():
    files = []
    meta_path = os.path.join(PROCESSED_FOLDER, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            files = json.load(f)
    return files


def save_processed_metadata(filename, row_count, s3_key):
    meta_path = os.path.join(PROCESSED_FOLDER, "metadata.json")
    files = get_processed_files()
    files.insert(0, {
        "filename": filename,
        "processed_at": datetime.utcnow().isoformat(),
        "row_count": row_count,
        "s3_key": s3_key,
    })
    with open(meta_path, "w") as f:
        json.dump(files, f, indent=2)


@app.route("/")
def index():
    processed_files = get_processed_files()
    return render_template("index.html", processed_files=processed_files)


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
        s3_key = upload_to_s3(filepath, filename)
        save_processed_metadata(filename, len(rows), s3_key)

        return render_template("result.html", filename=filename, rows=rows, s3_key=s3_key)

    flash("Only CSV files are allowed", "danger")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "csv-processor"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

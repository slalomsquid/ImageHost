from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import json
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
METADATA_FILE = "metadata.json"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure metadata.json exists
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "w") as f:
        json.dump({}, f)


def load_metadata():
    with open(METADATA_FILE, "r") as f:
        return json.load(f)


def save_metadata(data):
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_exif_date(file_path):
    """Try to extract original capture date from EXIF metadata."""
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "DateTimeOriginal":
                    # Format: "YYYY:MM:DD HH:MM:SS"
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print("No EXIF date:", e)
    return None


@app.route("/")

def index():
    metadata = load_metadata()
    images = []
    # --- NEW: Get search query from URL ---
    search_query = request.args.get("q", "").lower()
    # --------------------------------------

    for filename, data in metadata.items():
        # Prepare the image data dictionary
        image_data = {
            "filename": filename,
            "name": data.get("name", "Untitled"),
            "description": data.get("description", ""),
            "original_date": data.get("original_date", "Unknown"),
            "upload_date": data.get("upload_date", "Unknown")
        }

        # --- NEW: Filtering Logic ---
        # If a search query exists, check if it's in the name or description
        if search_query:
            if (search_query in image_data["name"].lower() or
                search_query in image_data["description"].lower()):
                images.append(image_data)
        else:
            # If no query, add all images
            images.append(image_data)
        # ----------------------------

    # --- NEW: Pass the search query back to the template ---
    return render_template("index.html", images=images, search_query=search_query)



@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return redirect(url_for("index"))

    file = request.files["file"]
    name = request.form.get("name", "Untitled")
    description = request.form.get("description", "")

    if file.filename == "":
        return redirect(url_for("index"))

    if file:
        filename = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        # Load or create metadata
        metadata = load_metadata()

        # Extract EXIF original date
        original_date = get_exif_date(save_path)

        # Add metadata
        metadata[filename] = {
            "name": name,
            "description": description,
            "original_date": original_date or "Unknown",
            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        save_metadata(metadata)

    return redirect(url_for("index"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(host='192.168.1.109', port=8080, debug=True)

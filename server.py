import os
import subprocess
import sys
import uuid
from flask import Flask, request, send_file, abort

app = Flask(__name__, static_url_path="", static_folder=".")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(BASE_DIR, "serverReplace.py")

SUPPORTED_EXTENSIONS = [".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"]
VALID_COUNTS = {"2", "3", "4", "6", "8"}


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    count = request.form.get("count")
    image = request.files.get("image")

    if count not in VALID_COUNTS:
        abort(400, f"Invalid label count: {count}")
    if not image:
        abort(400, "No image uploaded")

    ext = os.path.splitext(image.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        abort(400, f"Unsupported image type: {ext}")

    # Clear any existing customLabels.* so only one is picked up
    for existing_ext in SUPPORTED_EXTENSIONS:
        stale = os.path.join(BASE_DIR, f"customLabels{existing_ext}")
        if os.path.exists(stale):
            os.remove(stale)

    image_path = os.path.join(BASE_DIR, f"customLabels{ext}")
    image.save(image_path)

    output_name = f"generated_{uuid.uuid4().hex}.pdf"
    output_path = os.path.join(BASE_DIR, output_name)

    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, count, output_name],
        cwd=BASE_DIR, capture_output=True, text=True
    )

    # Trust the output file's existence over the exit code: the PDF can be
    # written successfully even if something else in the script errors
    # afterward (e.g. a console-encoding crash on a trailing print).
    if not os.path.exists(output_path):
        abort(500, result.stdout + result.stderr)

    response = send_file(output_path, as_attachment=True, download_name=f"AtemoAquaLabels_{count}each.pdf")

    @response.call_on_close
    def cleanup():
        if os.path.exists(output_path):
            os.remove(output_path)

    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)
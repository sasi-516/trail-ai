from flask import Flask, request, render_template, flash
import subprocess
import os
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to a secure key in production
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"exe", "csv"}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def run_executable(exe_path, csv_path):
    try:
        # Simulate loading for UI feedback
        time.sleep(1)  # Adjust delay as needed
        result = subprocess.run([exe_path, csv_path], capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split('\n')
        table_data = []
        for line in output_lines:
            if line:
                columns = line.split('\t')
                if columns[0].startswith('F(X)'):  # Preserve section headers
                    table_data.append([columns[0]] + columns[1:])  # Keep F(X)n and data
                else:
                    table_data.append(columns[1:])  # Remove Xn labels, keep data
        return table_data
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except FileNotFoundError:
        return f"Error: Executable {exe_path} not found."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    output = None
    loading = False
    if request.method == "POST":
        loading = True
        if "exe_file" not in request.files or "csv_file" not in request.files:
            flash("Please upload both an .exe and a .csv file.", "error")
        else:
            exe_file = request.files["exe_file"]
            csv_file = request.files["csv_file"]

            if exe_file.filename == "" or csv_file.filename == "":
                flash("No file selected.", "error")
            elif not (allowed_file(exe_file.filename) and allowed_file(csv_file.filename)):
                flash("Invalid file type. Only .exe and .csv files are allowed.", "error")
            else:
                exe_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(exe_file.filename))
                csv_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(csv_file.filename))
                exe_file.save(exe_path)
                csv_file.save(csv_path)

                exe_output = run_executable(exe_path, csv_path)
                if isinstance(exe_output, str):
                    flash(exe_output, "error")
                else:
                    output = exe_output

                # Clean up files after processing
                os.remove(exe_path)
                os.remove(csv_path)
        loading = False

    return render_template("index.html", output=output, loading=loading)

if __name__ == "__main__":
    app.run(debug=True)
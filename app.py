from flask import Flask, request, render_template, flash
import subprocess
import os
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()  # Secure random key for production
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"exe", "csv"}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def run_executable(exe_path, csv_path):
    try:
        print(f"Attempting to execute: {exe_path} {csv_path}")  # Debug
        # Simulate loading
        time.sleep(1)
        result = subprocess.run([exe_path, csv_path], capture_output=True, text=True, check=True)
        print(f"Execution output: {result.stdout}")  # Debug
        output_lines = result.stdout.strip().split('\n')
        table_data = []
        for line in output_lines:
            if line:
                columns = line.split('\t')
                if columns[0].startswith('F(X)'):  # Preserve section headers
                    table_data.append([columns[0]] + columns[1:])
                else:
                    table_data.append(columns[1:])  # Remove Xn labels, keep data
        return table_data
    except subprocess.CalledProcessError as e:
        print(f"Subprocess Error: {e.stderr}")  # Debug
        return f"Error: {e.stderr}"
    except FileNotFoundError:
        print(f"FileNotFoundError: {exe_path}")  # Debug
        return f"Error: Executable {exe_path} not found."
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")  # Debug
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

                # Make executable runnable (Linux permission)
                os.chmod(exe_path, 0o755)

                exe_output = run_executable(exe_path, csv_path)
                if isinstance(exe_output, str):
                    flash(exe_output, "error")
                else:
                    output = exe_output

                # Clean up files after processing
                try:
                    os.remove(exe_path)
                    os.remove(csv_path)
                except OSError:
                    pass  # Ignore cleanup errors
        loading = False

    return render_template("index.html", output=output, loading=loading)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
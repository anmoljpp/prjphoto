from flask import Flask, request, render_template, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

UPLOAD_FOLDER = "photo_project"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Dummy credentials (you can replace these with a database)
USERNAME = "admin"
PASSWORD = "q1w2e3r4t5y6"

@app.route("/", methods=["GET", "POST"])
def login():
    """Login Page"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username == USERNAME and password == PASSWORD:
            session["user"] = username  # Store session
            return redirect(url_for("upload_file"))  # Redirect to upload page
        else:
            return "Invalid credentials. Try again."

    return render_template("login.html")

@app.route("/upload_page")
def upload_file():
    """Check if user is logged in before allowing access to upload"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload():
    """Handle File Upload"""
    if "user" not in session:
        return redirect(url_for("login"))

    if "file" not in request.files:
        return "No file part"

    file = request.files["file"]
    
    if file.filename == "":
        return "No selected file"

    if file:
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], "frame4.png")
        file.save(save_path)
        return "File uploaded successfully as frame4.png"

@app.route("/logout")
def logout():
    """Logout and clear session"""
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

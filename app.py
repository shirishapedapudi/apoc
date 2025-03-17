from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import datetime
import os

# Your Speech-to-Text and NLP functions
from speech import convert_audio_to_text, extract_complaint_details

app = Flask(__name__)
CORS(app)  # Enable CORS

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["airport_complaints"]
complaints_collection = db["complaints"]

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'wav', 'mp3'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    try:
        # Save audio file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        print(f"Audio file saved at: {file_path}")

        # Convert audio to text
        text = convert_audio_to_text(file_path)
        if not text:
            return jsonify({"error": "Failed to transcribe audio"}), 500
        print("Transcribed Text:", text)

        # Extract complaint details using NLP
        details = extract_complaint_details(text)
        if not details:
            return jsonify({"error": "Failed to extract complaint details"}), 500

        # Add metadata
        details["timestamp"] = datetime.datetime.now()
        details["status"] = "open"
        details["audio_file"] = file.filename
        details["transcription"] = text  # Save transcription into DB too

        # Insert into MongoDB
        result = complaints_collection.insert_one(details)
        print("Inserted into MongoDB:", details)

        # Clean response (remove ObjectId)
        response_details = details.copy()
        if "_id" in response_details:
            del response_details["_id"]

        # Return everything including transcription
        return jsonify({
            "message": "Complaint registered successfully",
            "data": response_details,
            "transcription": text
        }), 200

    except Exception as e:
        print("Error during upload:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/complaints', methods=['GET'])
def get_complaints():
    try:
        urgency = request.args.getlist('urgency')
        location = request.args.get('location')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = {}

        if start_date and end_date:
            query["timestamp"] = {
                "$gte": datetime.datetime.fromisoformat(start_date),
                "$lte": datetime.datetime.fromisoformat(end_date)
            }
        if urgency:
            query["urgency"] = {"$in": urgency}
        if location:
            query["location"] = location

        complaints = list(complaints_collection.find(query, {"_id": 0}))

        return jsonify(complaints), 200

    except Exception as e:
        print("Error fetching complaints:", str(e))
        return jsonify({"error": f"Error fetching complaints: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)

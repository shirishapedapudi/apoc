import speech_recognition as sr
import spacy
from pydub import AudioSegment
import os
import re

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Supported audio formats
AUDIO_FORMATS = [".wav", ".mp3", ".ogg", ".flac", ".m4a"]

# Speech-to-text function
def convert_audio_to_text(audio_file_path):
    recognizer = sr.Recognizer()

    # Convert to .wav if needed
    ext = os.path.splitext(audio_file_path)[1]
    if ext not in [".wav"]:
        sound = AudioSegment.from_file(audio_file_path)
        audio_file_path = audio_file_path.rsplit(".", 1)[0] + ".wav"
        sound.export(audio_file_path, format="wav")

    with sr.AudioFile(audio_file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Audio could not be understood."
        except sr.RequestError as e:
            return f"Could not request results; {e}"

# NLP extraction (extended keyword spotting)
def extract_complaint_details(transcribed_text):
    doc = nlp(transcribed_text.lower())

    issue_types = ["baggage", "delay", "cleaning", "security", "staff", "maintenance", "toilet", "gate"]
    urgency_levels = ["urgent", "immediate", "high", "low", "normal"]

    issue = None
    urgency = "normal"
    location = None

    # Search for issue & urgency keywords in the text
    for token in doc:
        if not issue and token.lemma_ in issue_types:
            issue = token.lemma_
        if token.lemma_ in urgency_levels:
            urgency = token.lemma_

    # Extract location from Named Entities
    for ent in doc.ents:
        if ent.label_ in ["GPE", "FACILITY", "LOC"]:
            location = ent.text.title()
            break

    # Fallback: extract something that looks like "Gate 3" or "Terminal 2"
    if not location:
        loc_match = re.search(r"(gate\s\d+|terminal\s\d+)", transcribed_text.lower())
        if loc_match:
            location = loc_match.group(0).title()

    return {
        "issue": issue or "general",
        "urgency": urgency,
        "location": location or "unknown",
        "raw_text": transcribed_text
    }

# Testing block
if __name__ == "__main__":
    test_audio = "text_audio.wav"
    if os.path.exists(test_audio):
        text = convert_audio_to_text(test_audio)
        print("Transcribed Text:", text)
        details = extract_complaint_details(text)
        print("Extracted Details:", details)
    else:
        print(f"Audio file '{test_audio}' not found.")

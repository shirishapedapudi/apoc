import random
import datetime
from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["airport_complaints"]
complaints_collection = db["complaints"]

# Sample values
locations = ['Terminal 1', 'Terminal 2', 'Terminal 3', 'Baggage Claim', 'Check-in', 'Security', 'Parking Lot']
urgencies = ['low', 'medium', 'high', 'urgent']
issues = [
    "Lost baggage at Terminal",
    "Flight delay announcement missing",
    "Unhygienic restroom conditions",
    "Long security queue",
    "Parking payment machine not working",
    "Broken escalator",
    "Noise complaint from announcements",
    "Unauthorized access reported"
]

# Seed 100 fake complaints
for i in range(100):
    complaint = {
        "location": random.choice(locations),
        "urgency": random.choice(urgencies),
        "issue": random.choice(issues),
        "status": random.choice(["open", "closed"]),
        "timestamp": datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30)),
        "audio_file": f"dummy_audio_{i}.wav"
    }
    complaints_collection.insert_one(complaint)

print("✅ Inserted 100 fake complaints into MongoDB!")

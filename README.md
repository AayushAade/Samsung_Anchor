# 🧠 The "External Hippocampus" System

A zero-friction, continuous context-restoration wearable system designed to protect the dignity and independence of Alzheimer’s patients.

🚨 The Problem

Alzheimer’s disease systematically strips away a person's immediate context, leading to a continuous loop of disorientation. Patients suffer from three primary deficits:

The Intent Deficit: Forgetting why they entered a room (the private panic of losing your goal).

The Object Deficit: Losing track of vital daily items (glasses, keys, phone), leading to anxiety loops.

The Identity Deficit: Failing to recognize loved ones, resulting in social withdrawal and shame.

Current solutions (like 24/7 nursing) are financially ruinous for underserved communities, highly intrusive, and prone to caregiver burnout.

💡 The Solution

The External Hippocampus is a context-restoration system. It acts as an external memory bank, proactively supplying missing context via a discreet audio-first interface. It requires absolutely zero technical interaction from the patient.

For this prototype phase, we are using a Smartphone Proxy Architecture (a phone worn on a lanyard) to simulate the eventual AR Smart Glasses form factor.

✨ Core Features

📍 Context Restoration (Spatial Audio Cues): Logs user intent via voice ("I'm getting water") and uses BLE beacon hysteresis to detect room transitions, whispering a gentle reminder ("Getting water") upon entry.

🔍 Passive Object Tracking (Visual Ledger): Uses Edge AI (YOLOv8-nano) to continuously track high-value items. It logs coordinates in a Spatial Hash Map, allowing users to ask, "Where is my phone?" and get an instant, historically accurate answer.

👤 Identity Anchoring: Uses local OpenCV facial recognition to match approaching faces against a pre-recorded, multi-angle vector database. It whispers the person's name and a "core memory" context (e.g., "This is Arjun, your grandson.") before social panic sets in.

⏰ Proactive Time/Context Anchoring: Helps mitigate "sundowning" by providing gentle ambient grounding statements about the time of day and schedule (e.g., doctor appointments).

🔋 The "Cold Start" Smart Dock: Detects the sleep-wake transition using motion tracking from the charging dock, playing a familiar greeting to ensure the user puts the device on first thing in the morning.

🏗️ Technical Architecture (MVP)

Sensors (The Eyes & Ears): A Smartphone Proxy running a Mobile Web App (HTML5/JS), capturing audio and streaming camera frames.

Brain (The Edge Server): A local Python/Flask backend running on a laptop.

Spatial Tracking: ESP32/Wi-Fi hotspots acting as BLE Beacons tracking RSSI signal strength.

AI/ML Stack:

Intent Parsing: Gemini API (LLM) forcing strict JSON outputs.

Object Detection: YOLOv8-nano (Supervised fine-tuning).

Face Recognition: OpenCV + MobileFaceNet (128-D vector embeddings via Euclidean distance).

Database: SQLite (local context ledger).

🚀 Getting Started

Follow these instructions to run the Smartphone Proxy MVP locally on your network.

Prerequisites

Python 3.9+

A smartphone and laptop connected to the same local Wi-Fi network.

Gemini API Key

Installation

Clone the repository:

git clone https://github.com/YOUR_USERNAME/external-hippocampus.git
cd external-hippocampus


Set up a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`


Install dependencies:

pip install -r requirements.txt


Environment Variables:
Create a .env file in the root directory and add your Gemini API key:

GEMINI_API_KEY=your_api_key_here


Running the System

Start the Flask Edge Server:

python app.py


Note: The server will bind to 0.0.0.0:5000. Note the local IPv4 address of your laptop (e.g., 192.168.1.15).

Connect the Smartphone Proxy:

Open the browser on your smartphone.

Navigate to https://<YOUR_LAPTOP_IP>:5000 (e.g., https://192.168.1.15:5000).

Grant Camera and Microphone permissions when prompted.

Simulate:

Speak your intent into the phone interface.

Walk near your designated BLE/Hotspot zones.

Point the camera at registered objects/faces to test the local visual ledger.

🗺️ Roadmap to Production

[x] Phase 1: Software MVP (Flask + LLM Intent Parsing)

[x] Phase 2: Computer Vision Pipeline (YOLO + OpenCV local database)

[ ] Phase 3: Hardware Migration (Porting to Raspberry Pi backpack rig)

[ ] Phase 4: AR Glasses Integration (Samsung XR/Vuzix)

🤝 Acknowledgments

Built for the Samsung Solve for Tomorrow Hackathon.
Theme: Health and Education - Enable affordable, tech-driven healthcare and learning → Improve access for underserved communities.

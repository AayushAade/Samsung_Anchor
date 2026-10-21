# MEMORA (Samsung Anchor) Cross-Platform Deployment Guide

Comprehensive deployment guide for deploying MEMORA across macOS, Linux, Windows, and Raspberry Pi 4/5 hardware.

---

## 1. Environment & Hardware Requirements

### System Requirements
| Hardware Component | Minimum Requirement | Recommended Specification |
| :--- | :--- | :--- |
| **CPU** | Dual-core 2.0 GHz (x86_64 / ARM64) | Quad-core 2.8+ GHz (Apple Silicon / Intel i7 / ARM Cortex-A76) |
| **RAM** | 2.0 GB RAM | 4.0+ GB RAM |
| **Camera** | USB Web Camera (720p 30fps) | Integrated Camera / USB HD Webcam (1080p) |
| **Microphone** | Standard Audio Interface / Mic | Far-field Array Microphone |
| **Speaker** | Native Audio Driver / Speaker | Standard Stereo Speaker |
| **Storage** | 500 MB free disk space | 2.0 GB SSD storage |

---

## 2. Platform Setup Procedures

### A. macOS (Apple Silicon / Intel)
```bash
# 1. Clone repository & setup Python environment
git clone https://github.com/AayushAade/Samsung_Anchor.git
cd Samsung_Anchor
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Grant Camera & Microphone permissions in macOS System Settings -> Privacy & Security

# 4. Set Gemini API Key (Optional LLM Mode)
export GEMINI_API_KEY="your-gemini-api-key"

# 5. Run MEMORA
python app.py --live-hardware
```

### B. Linux (Ubuntu / Debian x86_64)
```bash
# 1. Install system audio and video dependencies
sudo apt-get update && sudo apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    libopencv-dev libportaudio2 libasound2-dev \
    ffmpeg v4l-utils

# 2. Add user to video and audio groups
sudo usermod -aG video,audio $USER

# 3. Setup virtual environment & install requirements
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Run MEMORA
python app.py --live-hardware
```

### C. Raspberry Pi 4 / 5 (Raspberry Pi OS ARM64)
```bash
# 1. Install ARM64 system libraries
sudo apt-get update && sudo apt-get install -y \
    python3-pip python3-venv libatlas-base-dev \
    libportaudio2 libopenblas-dev v4l-utils

# 2. Enable Camera interface via raspi-config
sudo raspi-config  # Enable Legacy Camera / libcamera

# 3. Setup venv with system site-packages for OpenCV/ONNX
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Run MEMORA in edge lightweight mode
python app.py --live-hardware
```

### D. Windows 11 (x86_64)
```powershell
# 1. Open PowerShell as Administrator
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install PyAudio wheel and requirements
pip install -r requirements.txt

# 3. Set Environment Variable for Gemini
$env:GEMINI_API_KEY="your-gemini-api-key"

# 4. Run MEMORA
python app.py --live-hardware
```

---

## 3. Environment Variables Reference

| Variable Name | Purpose | Default | Recommended |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API Key | None (Local Reasoner Mode) | Valid API key for cloud LLM |
| `DB_PATH` | SQLite Database Path | `memora_db_v2.sqlite` | `memora_db_v2.sqlite` |
| `ORT_LOGGING_LEVEL` | ONNX Runtime verbosity | `3` (Error) | `3` |
| `OPENCV_LOG_LEVEL` | OpenCV logging level | `OFF` | `OFF` |
| `LOG_LEVEL` | Application logger level | `INFO` | `INFO` |

---

## 4. Verification Commands

```bash
# Run Database & FAISS Audit
python inspect_database.py --audit

# Run Runtime Stability Profiler
python app.py --validate-runtime --max-cycles 25

# Run Real Patient End-to-End Demonstration
python demo_real_patient.py

# Run Full PyTest Suite (532+ tests)
pytest
```

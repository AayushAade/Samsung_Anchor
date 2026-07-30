# Memora Multi-Platform Deployment Guide

## Deployment Options

### Option 1: Standalone Shell Script
To launch Memora on any desktop or laptop using local Python environment:
```bash
export MEMORA_PROFILE=SIMULATION
./deployment/scripts/start.sh
```

### Option 2: Docker Compose (Recommended for Production)
To launch Memora using containerized services:
```bash
docker-compose -f deployment/compose/docker-compose.yml up --build
```
Access points:
- **Dashboard UI**: `http://localhost:3000`
- **Core Event Stream**: `http://localhost:8000`
- **Health Check Endpoint**: `http://localhost:8000/health`

### Option 3: Raspberry Pi Deployment
Set profile environment variable:
```bash
export MEMORA_PROFILE=RASPBERRY_PI
python demo_experience.py --scenario
```

### Option 4: NVIDIA Jetson Edge Deployment
Set CUDA-accelerated profile:
```bash
export MEMORA_PROFILE=JETSON
python demo_experience.py --scenario
```

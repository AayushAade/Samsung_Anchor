#!/usr/bin/env bash
echo "🛑 Stopping Memora Edge Platform..."
pkill -f "demo_experience.py" || true
echo "Memora stopped cleanly."

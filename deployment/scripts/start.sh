#!/usr/bin/env bash
set -e

echo "🚀 Starting Memora Edge Platform..."
export MEMORA_PROFILE=${MEMORA_PROFILE:-SIMULATION}

echo "Profile: $MEMORA_PROFILE"
python demo_experience.py --scenario

#!/usr/bin/env bash
echo "🔍 Running Memora Health Check..."
python -c "
from deployment.health.health_checker import HealthChecker
hc = HealthChecker()
print('Health Status:', hc.check_health())
"

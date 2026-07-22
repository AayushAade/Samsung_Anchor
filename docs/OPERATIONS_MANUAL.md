# Memora Operations & Troubleshooting Manual

## Health & Monitoring
Run the health check script to inspect system component readiness:
```bash
./deployment/scripts/health_check.sh
```

Sample output:
```json
{
  "overall_status": "Healthy",
  "runtime_ready": true,
  "perception_ready": true,
  "cognition_ready": true,
  "clinical_ready": true
}
```

## Logging & Observability
Logs are emitted in structured JSON format:
```json
{
  "timestamp": "2026-07-22T10:15:00.123456",
  "level": "INFO",
  "module": "MemoraCore",
  "message": "Cognitive cycle complete",
  "context": {
    "cycle_id": 12,
    "latency_ms": 42.5
  }
}
```

## Emergency Overrides
If fall detection or a medical emergency triggers:
1. `EmergencyManager` overrides assistance policies to **Level 5: Safety Override**.
2. Direct, calm safety guidance is delivered to the patient.
3. Designated primary caregiver (e.g. Sarah Jenkins) receives instant notification.

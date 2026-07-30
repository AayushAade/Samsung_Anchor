# MEMORA Technical Debt Registry

- **Document Status**: Active Repository Documentation
- **Last Updated**: 2026-07-30
- **Scope**: Identified Architectural Limitations, Trade-Offs, and Future Implementation Recommendations

---

## Technical Debt Items

### TD-001: In-Memory Ring Buffer Overflow Spilling
- **Description**: Subsystem repositories (`ExperienceRepository`, `CognitiveBlackboard`, `GoalManager`) cap active items in memory buffers (`MAX_RECORDS = 300..500`). Excess records are evicted to maintain $< 1\text{ms}$ query latency.
- **Architectural Impact**: Long-term execution history over weeks of continuous operation is truncated in memory unless archived asynchronously to SQLite.
- **Priority**: Medium
- **Recommended Solution**: Implement an asynchronous background worker queue flushing evicted records to SQLite database via SQLAlchemy ORM.
- **Estimated Effort**: 2 Engineering Days

### TD-002: Hardcoded Substring Matching in Pattern Library
- **Description**: `PatternLibrary` matches historical patterns via string substring search (`kw in p.goal_title.lower()`).
- **Architectural Impact**: Variations in goal titles (e.g., "Find Glasses" vs "Locate Spectacles") are treated as separate patterns.
- **Priority**: Low
- **Recommended Solution**: Introduce a canonical goal taxonomy mapping title variants to standard category keys before pattern lookup.
- **Estimated Effort**: 1 Engineering Day

### TD-003: Single Active Plan Focus in Execution Monitor
- **Description**: `ExecutionMonitor` tracks reality divergence for a single top active plan at a time.
- **Architectural Impact**: Multi-task scenarios cannot monitor secondary background goals concurrently.
- **Priority**: Low
- **Recommended Solution**: Expand `ExecutionMonitor` into a multi-plan tracking registry (`Dict[str, Plan]`).
- **Estimated Effort**: 2 Engineering Days

---

## Maintenance Guidelines

1. **Never Claim Zero Debt**: Every real-world system exhibits engineering trade-offs.
2. **Review Schedule**: Re-evaluate this registry prior to launching major version milestones.

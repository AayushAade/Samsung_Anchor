"""
Global project configuration.

This module contains shared runtime configuration used by the
Memory, Vision, Audio, and future Reasoning subsystems.

Only stable, project-wide configuration values should be defined here.
"""

# ==========================================================
# Memory Configuration
# ==========================================================

# SQLite database location.
# Uses a relative path so the project remains portable across
# different operating systems and developer machines.
DB_PATH = "memora_db.sqlite"

# Default face-matching threshold.
#
# Used when no explicit tolerance is provided to the
# face recognition pipeline.
#
# NOTE:
# This is an initial prototype value and should be
# calibrated after collecting real recognition data.
FACE_TOLERANCE = 0.60


# ==========================================================
# Vision Configuration
# ==========================================================
# (Reserved for future project settings)


# ==========================================================
# Audio Configuration
# ==========================================================
# (Reserved for future project settings)


# ==========================================================
# Reasoning Configuration
# ==========================================================
# (Reserved for future project settings)
"""
Memory Development Harness

This script is used by the Memory Lead to verify that the
Memory subsystem can initialize correctly without requiring
Vision, Audio, or the full application.
"""

from src.memory.database import MemoraDatabase


def main():
    """Entry point for the Memory Development Harness."""

    print("=" * 60)
    print("        ANCHOR MEMORY DEVELOPMENT HARNESS")
    print("=" * 60)
    print("Starting Memory Module Verification...\n")

    try:
        print("[INFO] Initializing Memory Database...")

        db = MemoraDatabase()

        print("[SUCCESS] Memory Database initialized successfully.")

    except Exception as e:
        print("[ERROR] Failed to initialize Memory Database.")
        print(f"Reason: {e}")


if __name__ == "__main__":
    main()
import os


def test_release_manifests_exist():
    root = os.path.dirname(os.path.dirname(__file__))

    changelog_path = os.path.join(root, "CHANGELOG.md")
    release_notes_path = os.path.join(root, "RELEASE_NOTES.md")
    docs_dir = os.path.join(root, "docs")

    assert os.path.exists(changelog_path)
    assert os.path.exists(release_notes_path)
    assert os.path.exists(docs_dir)

import json
import shutil
from pathlib import Path

import pytest

import package

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def root(tmp_path):
    for part in (".claude-plugin", "shared", "tools", "skills"):
        if (REPO / part).exists():
            shutil.copytree(REPO / part, tmp_path / part)
    (tmp_path / "INSTALL.md").write_text("install")
    package.sync(tmp_path)  # tests must not depend on whether the working copy was synced
    return tmp_path


def skill_md(root, name="fp-lead"):
    return root / "skills" / name / "SKILL.md"


def test_real_repository_passes_and_builds_identical_zips(root, tmp_path):
    first = package.build(root, tmp_path / "a")
    second = package.build(root, tmp_path / "b")
    assert first == second
    for name in first:
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


def test_name_must_match_folder(root):
    p = skill_md(root)
    p.write_text(p.read_text().replace("name: fp-lead", "name: FP-Lead", 1))
    with pytest.raises(package.PackageError, match="must equal the folder"):
        package.build(root, check_only=True)


def test_description_length_is_enforced(root):
    p = skill_md(root)
    text = p.read_text()
    start = text.index("description:")
    end = text.index("\n", start)
    p.write_text(text[:start] + "description: " + "x" * 1025 + text[end:])
    with pytest.raises(package.PackageError, match="1-1024"):
        package.build(root, check_only=True)


def test_broken_link_is_reported(root):
    p = skill_md(root)
    p.write_text(p.read_text() + "\nSee [missing](references/nowhere.md).\n")
    with pytest.raises(package.PackageError, match="missing references/nowhere.md"):
        package.build(root, check_only=True)


def test_drifted_copy_is_reported_by_check_and_repaired_by_sync(root):
    copy = root / "skills" / "fp-lead" / "references" / "operating-rules.md"
    copy.write_text(copy.read_text() + "drift")
    with pytest.raises(package.PackageError, match="differs from its original"):
        package.build(root, check_only=True)
    package.sync(root)
    package.build(root, check_only=True)


def test_hidden_files_are_refused(root):
    (root / "skills" / "fp-lead" / ".DS_Store").write_bytes(b"x")
    with pytest.raises(package.PackageError, match="hidden file"):
        package.build(root, check_only=True)


def test_manifest_version_is_checked(root):
    path = root / ".claude-plugin" / "plugin.json"
    data = json.loads(path.read_text())
    data["version"] = "latest"
    path.write_text(json.dumps(data))
    with pytest.raises(package.PackageError, match="version"):
        package.build(root, check_only=True)

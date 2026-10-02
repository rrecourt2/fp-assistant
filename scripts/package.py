"""Build the skills-only preview and individual-skill fallback using the stdlib."""

from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]


def archive(files):
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as output:
        for name, data in sorted(files.items()):
            assert not name.startswith("/") and ".." not in Path(name).parts, name
            output.writestr(name, data)
    result = buffer.getvalue()
    with ZipFile(BytesIO(result)) as check:
        assert check.testzip() is None
        assert set(check.namelist()) == set(files)
        assert all(check.read(name) == data for name, data in files.items())
    return result


def main():
    manifest_path = ROOT / ".claude-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["name"] == "fp-assistant"
    version = manifest["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    assert len(skills) == 8, "Review package contents when adding or removing skills"
    package = {".claude-plugin/plugin.json": manifest_path.read_bytes(),
               "INSTALL.md": (ROOT / "INSTALL.md").read_bytes()}
    individual = {}
    for skill in skills:
        assert (skill / "SKILL.md").is_file()
        for shared in ("operating-rules.md", "workflow-contract.md"):
            assert (skill / "references" / shared).read_bytes() == (ROOT / "shared" / shared).read_bytes()
        files = {}
        for path in sorted(skill.rglob("*")):
            assert not path.is_symlink(), path
            if path.is_file():
                name = path.relative_to(skill).as_posix()
                assert not any(part.startswith(".") for part in Path(name).parts), name
                files[name] = path.read_bytes()
        assert len(files) - 1 <= 20
        assert all(len(data) <= 5 * 1024**2 for name, data in files.items() if name != "SKILL.md")
        assert sum(len(data) for name, data in files.items() if name != "SKILL.md") <= 10 * 1024**2
        individual[f"{skill.name}.zip"] = archive(files)
        package.update({f"skills/{skill.name}/{name}": data for name, data in files.items()})
    for skill in ("fp-lead", "investment-grill"):
        assert (ROOT / "skills" / skill / "references/review-protocol.md").read_bytes() == (ROOT / "shared/review-protocol.md").read_bytes()
    individual["INSTALL.md"] = package["INSTALL.md"]
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    for name, files in ((f"fp-assistant-{version}.zip", package),
                        (f"fp-assistant-individual-skills-{version}.zip", individual)):
        data = archive(files)
        (destination / name).write_bytes(data)
        print(f"{destination / name}: {len(data):,} bytes; {len(files)} entries; readback passed")


if __name__ == "__main__":
    main()

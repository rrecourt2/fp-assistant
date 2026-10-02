"""Check the skills and build the Cowork upload ZIPs (standard library only).

  python3 scripts/package.py          # sync shared files into skills, check, build dist/
  python3 scripts/package.py --check  # check only

shared/*.md and tools/*.py are the maintained originals. A skill gets a copy of one when its
SKILL.md links to references/<name> or scripts/<name>; the copies must stay byte-identical.
"""
import json
import re
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
STAMP = (2026, 1, 1, 0, 0, 0)  # fixed timestamps: the same sources always give the same ZIP bytes
LINK = re.compile(r"\]\(((?:references|scripts)/[^)#\s]+)\)")


class PackageError(Exception):
    pass


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise PackageError("SKILL.md must start with --- frontmatter ---")
    fields = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def originals(root):
    return {f"references/{p.name}": p for p in (root / "shared").glob("*.md")} | \
           {f"scripts/{p.name}": p for p in (root / "tools").glob("*.py")}


def sync(root):
    """Copy maintained originals into each skill that links to them."""
    canon = originals(root)
    for skill in sorted((root / "skills").iterdir()):
        if not skill.is_dir():
            continue
        for rel in LINK.findall((skill / "SKILL.md").read_text(encoding="utf-8")):
            if rel in canon:
                target = skill / rel
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(canon[rel].read_bytes())


def check_skill(skill, canon):
    """Microsoft's upload rules plus our copy and link rules. Returns {zip path: bytes}."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    fm = frontmatter(text)
    name, desc = fm.get("name", ""), fm.get("description", "")
    if name != skill.name:
        raise PackageError(f"{skill.name}: frontmatter name {name!r} must equal the folder name")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        raise PackageError(f"{skill.name}: name must be kebab-case, at most 64 characters")
    if not 1 <= len(desc) <= 1024:
        raise PackageError(f"{skill.name}: description must be 1-1024 characters (has {len(desc)})")
    for rel in LINK.findall(text):
        if not (skill / rel).is_file():
            raise PackageError(f"{skill.name}: SKILL.md links to missing {rel}")
    files = {}
    for path in sorted(skill.rglob("*")):
        if path.is_symlink():
            raise PackageError(f"{path}: symlinks are not allowed")
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(skill).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            raise PackageError(f"{skill.name}: hidden file {rel} (delete it)")
        if rel in canon and path.read_bytes() != canon[rel].read_bytes():
            raise PackageError(f"{skill.name}: {rel} differs from its original; run package.py to sync")
        files[rel] = path.read_bytes()
    companions = {k: v for k, v in files.items() if k != "SKILL.md"}
    if len(companions) > 20:
        raise PackageError(f"{skill.name}: {len(companions)} companion files (maximum 20)")
    if any(len(v) > 5 * 1024 ** 2 for v in companions.values()) or sum(map(len, companions.values())) > 10 * 1024 ** 2:
        raise PackageError(f"{skill.name}: companion files exceed 5 MB each or 10 MB in total")
    return files


def archive(files):
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = ZipInfo(name, STAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])
    data = buffer.getvalue()
    with ZipFile(BytesIO(data)) as z:
        if z.testzip() is not None or {n: z.read(n) for n in z.namelist()} != files:
            raise PackageError("archive read-back failed")
    return data


def build(root=ROOT, dest=None, check_only=False):
    manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
    if manifest.get("name") != "fp-assistant" or not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        raise PackageError("plugin.json needs name 'fp-assistant' and a version like 0.3.0")
    if not check_only:
        sync(root)
    canon = originals(root)
    skills = {s.name: check_skill(s, canon) for s in sorted((root / "skills").iterdir()) if s.is_dir()}
    if check_only:
        return {name: len(files) for name, files in skills.items()}
    package = {".claude-plugin/plugin.json": (root / ".claude-plugin/plugin.json").read_bytes(),
               "INSTALL.md": (root / "INSTALL.md").read_bytes()}
    individual = {"INSTALL.md": package["INSTALL.md"]}
    for name, files in skills.items():
        package.update({f"skills/{name}/{rel}": data for rel, data in files.items()})
        individual[f"{name}.zip"] = archive(files)
    dest = Path(dest or root / "dist")
    dest.mkdir(exist_ok=True)
    out = {}
    for name, files in ((f"fp-assistant-{manifest['version']}.zip", package),
                        (f"fp-assistant-individual-skills-{manifest['version']}.zip", individual)):
        (dest / name).write_bytes(archive(files))
        out[name] = len(files)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        result = build(check_only="--check" in argv)
    except PackageError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    for name, count in result.items():
        print(f"{name}: {count} files OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

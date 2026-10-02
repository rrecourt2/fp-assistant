# FP Assistant: working tools and cleanup — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make FP Assistant prove useful on a real FP in Microsoft Copilot Cowork on the work laptop. Three things must hold:
- your writing is protected;
- unresolved questions stay visible;
- the correct figures are transferred.

Then show it working end to end on one historical deal.

**Architecture:** The eight skills keep their analysis and writing method. Three scripts in `tools/` do the exact work:
- `register.py`: a JSON record with Excel and Markdown views, rules, and a one-screen summary.
- `fp_docx.py`: read, build and check Word files by byte-splicing `document.xml`, never re-serialising XML it did not write.
- `fin_table.py`: an identified spreading export → the FP table, with cell references.

`scripts/package.py` copies `shared/` and `tools/` into the skills that link to them and builds the upload zips. Skills stay model-neutral.

**Tech stack:**
- Runtime: Python 3.9+ standard library only.
- Development: `uv`, `pytest`, and `python-docx` and `openpyxl` as independent readers in tests only.

**Status of this plan's code:** written and verified on 2 October 2026 in a scratch copy of the repository at commit `ba62f3b`, after review feedback from Astra:
- 55 tests pass;
- `package.py` builds the zips;
- the three self-tests pass on Python 3.9.6 with no third-party libraries, including from inside the unzipped plugin.

The code blocks are those exact files.

## Problems this plan fixes

| Problem | Task |
|---|---|
| The register, Word and financial-table programs did not exist | 1–5 |
| Your edit to section A could be overwritten two rounds after the assistant updated section B (reproduced by a test) | 2 |
| Reviewers could not read kept tables; cover-field filling ignored comments, tracked changes and tables inside sections | 2 |
| New questions and sources had no default state; answered or promised questions dropped out of the lists | 3 |
| The tool itself printed "Ready: yes"; readiness should be the officer's recorded decision for a named Word version | 3, 5 |
| An interrupted run could leave the Excel and Markdown views stale | 3 |
| Financial table: duplicate labels or periods were resolved silently; formula values were trusted silently; the export was not identified | 4 |
| Skill id `meeting-evidence-review` for "Deal Updates"; overlapping triggers | 5 |
| 21,500 words of layered documents for 8,800 words of skills | 6 |
| No early Cowork test, and no proof that a complete FP is useful | 7, 8 |
| Testing every case on two models after every change was excessive | 9 |

## Global constraints

- Runtime code in `tools/` uses the Python standard library only and must run on Python 3.9.
- Scripts never overwrite their inputs, write atomically and refuse rather than guess.
- Skills: `name` equals the folder name and is kebab-case (at most 64 characters); `description` is 1–1,024 characters.
- Per skill: at most 20 companion files, each at most 5 MB, at most 10 MB in total, and no hidden files.
- `shared/*.md` and `tools/*.py` are the originals. Copies inside skills come from `scripts/package.py` and must stay byte-identical. Run it after changing an original.
- Skills contain no model-specific instructions.
- Add Word support only for features the real template needs.
- No confidential deal data, real transcripts, private audience notes or institutional templates in the repository. The replay in Task 8 runs in the work tenant.
- Work on a branch; commit after every task.

## File structure

| Path | Responsibility |
|---|---|
| `pyproject.toml` | No runtime dependencies; test-only dev group; pytest paths |
| `scripts/package.py` | Sync originals into skills, check upload rules, build reproducible zips |
| `tools/fp_docx.py` | Word: `inspect`, `build`, `check`, `selftest` |
| `tools/register.py` | Register: `init`, `summary`, `show`, `apply`, `lists`, `check`, `selftest` |
| `tools/fin_table.py` | Identified spreading export → FP table; `selftest` |
| `tests/test_*.py` | One test file per script |
| `shared/workflow-contract.md` | How the skills use the tools (rewritten) |
| `skills/deal-updates/` | Renamed from `skills/meeting-evidence-review/` |
| `docs/design.md` | The one current design |
| `docs/archive/` | Superseded documents |
| `evaluations/README.md`, `evaluations/results.md` | Evaluation procedure and results log |

---

### Task 1: Setup and packaging checks

**Files:**
- Create: `pyproject.toml`
- Modify (replace): `scripts/package.py`
- Test: `tests/test_package.py`

**Interfaces:**
- Produces: `package.build(root, dest=None, check_only=False) -> dict[str, int]`, `package.sync(root)`, `package.PackageError`. Command line: `python3 scripts/package.py [--check]`.

- [ ] **Step 1: Branch and `pyproject.toml`**

```bash
cd /Users/rikrecourt/fp-assistant
git switch -c tools-and-cleanup
```

````toml
[project]
name = "fp-assistant"
version = "0.3.0"
requires-python = ">=3.9"
dependencies = []  # tools/ use the Python standard library only

[dependency-groups]
dev = ["pytest>=8", "python-docx>=1.1", "openpyxl>=3.1"]  # independent readers for tests only

[tool.pytest.ini_options]
pythonpath = ["tools", "scripts"]
testpaths = ["tests"]
````

Run: `uv run python -c "import docx, openpyxl, pytest; print('ok')"`
Expected: `ok` (and `uv.lock` is created)

- [ ] **Step 2: Write the failing tests** — `tests/test_package.py`

````python
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
````

- [ ] **Step 3: Run them to see them fail**

Run: `uv run pytest tests/test_package.py -q`
Expected: FAIL — `AttributeError: module 'package' has no attribute 'sync'` (the old script has neither `sync` nor `build`).

- [ ] **Step 4: Replace `scripts/package.py`**

````python
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
````

- [ ] **Step 5: Run the tests and the check**

Run: `uv run pytest tests/test_package.py -q && python3 scripts/package.py --check`
Expected: `7 passed`, then one `OK` line per skill.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock scripts/package.py tests/test_package.py
git commit -m "Add dev setup; check skill frontmatter and links, sync shared copies, reproducible zips"
```

---

### Task 2: Word tool (`tools/fp_docx.py`)

**Files:**
- Create: `tools/fp_docx.py`
- Test: `tests/test_fp_docx.py`

**Interfaces:**
- Produces: `build(base, content, out, first=False, fields=None) -> dict` (keys `out, written, frozen, unmatched, missing_fields, proposals, sha256`), `inspect(path) -> dict`, `to_markdown(path) -> str`, `check(path, template=None) -> dict`, `signature(section) -> str`, `Doc(path)`, `Refuse`, `make_template(path, comment_on=None)`, `edit_text(path, old, new)`, `selftest() -> str`.
- Files next to `OUT.docx`: `OUT.sections.json` (owner and signature per section) and, when needed, `OUT.proposals.md`.
- Command line: `inspect DOCX [--markdown]`, `build --base --content --out [--first] [--fields]`, `check DOCX [--template]`, `selftest`. Exit codes: 0 ok, 1 check problems, 3 refused.

Behaviour:
- A section is the body between one heading and the next heading of any level.
- `--first` fills every section without comments or tracked changes.
- A later build replaces a section only if the assistant wrote it and nobody changed it since. "Assistant-owned" is carried forward only while the section's signature is unchanged.
- Fixed objects (template tables, images, fields, content controls, bookmarks, captions, section breaks) are never deleted; `{{keep:N}}` places them.
- `inspect --markdown` shows kept tables in read-only `<!-- -->` notes, which `build` ignores.
- Cover fields are filled only before the first heading, and only in cells without comments, tracked changes, fields or content controls.
- Signatures ignore Word's save noise (revision ids, split runs) but catch text, style, bold, italic, underline, comments and tracked changes.

- [ ] **Step 1: Write the failing tests** — `tests/test_fp_docx.py`

````python
import json
import zipfile

import docx  # dev-only independent reader; the tool itself uses the standard library
import pytest

import fp_docx


@pytest.fixture
def tpl(tmp_path):
    path = tmp_path / "template.docx"
    fp_docx.make_template(path)
    return path


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


FIRST = ("## summary\nCedar Foods seeks EUR 12m. [S-001 p.2]\n\n"
         "## financial-analysis\nRevenue rose 20%. [S-002 p.20]\n\n| EUR m | FY2025 |\n|---|---|\n| Revenue | 120 |\n\n"
         "{{keep:1}}\n\n## market-risk\n- Milk prices rose. [S-003]\n\n## recommendation\nApprove.\n")


def test_first_build_fills_sections_fields_and_keeps_fixed_table(tpl, tmp_path):
    out = tmp_path / "FP-v01.docx"
    r = fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), out, first=True,
                      fields={"Borrower": "Cedar Foods", "Amount": "EUR 12m", "Tenor": "5 years"})
    assert r["written"] == ["summary", "financial-analysis", "market-risk", "recommendation"]
    assert r["missing_fields"] == ["Tenor"]
    d = docx.Document(out)  # opens in an independent reader
    text = "\n".join(p.text for p in d.paragraphs)
    assert "Cedar Foods seeks EUR 12m." in text and "[S-001" not in text
    assert "[Summarise the proposal]" not in text
    cells = [c.text for t in d.tables for row in t.rows for c in row.cells]
    assert "Cedar Foods" in cells and "EUR 12m" in cells   # cover fields
    assert "FY2025 (template)" in cells and "Revenue" in cells   # template table kept + new table added
    side = json.loads((tmp_path / "FP-v01.sections.json").read_text())
    assert side["sections"]["summary"]["owner"] == "ai"
    assert side["sections"]["summary"]["ids"] == ["S-001"]
    assert fp_docx.check(out, tpl)["problems"] == []


def test_second_round_freezes_officer_edits_and_writes_proposals(tpl, tmp_path):
    v1 = tmp_path / "FP-v01.docx"
    fp_docx.build(tpl, write(tmp_path / "c1.md", FIRST), v1, first=True)
    fp_docx.edit_text(v1, "Approve.", "Approve, subject to two conditions.")
    v2 = tmp_path / "FP-v02.docx"
    r = fp_docx.build(v1, write(tmp_path / "c2.md", "## summary\nNew summary.\n\n## recommendation\nDecline.\n"), v2)
    assert r["written"] == ["summary"]
    assert r["frozen"] == {"recommendation": "edited since the assistant wrote it"}
    md = fp_docx.to_markdown(v2)
    assert "Approve, subject to two conditions." in md and "Decline." not in md
    assert "Decline." in (tmp_path / "FP-v02.proposals.md").read_text()
    side = json.loads((tmp_path / "FP-v02.sections.json").read_text())["sections"]
    assert side["recommendation"]["owner"] == "other" and side["market-risk"]["owner"] == "ai"


def test_commented_section_is_never_replaced(tmp_path):
    tpl = tmp_path / "template.docx"
    fp_docx.make_template(tpl, comment_on="market-risk")
    r = fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), tmp_path / "out.docx", first=True)
    assert "market-risk" in r["frozen"]
    info = fp_docx.inspect(tmp_path / "out.docx")
    assert info["comments"][0]["section"] == "market-risk"
    assert info["comments"][0]["text"] == "Check the FX exposure"


def test_unknown_section_goes_to_proposals(tpl, tmp_path):
    r = fp_docx.build(tpl, write(tmp_path / "c.md", "## annex-9\nText\n"), tmp_path / "o.docx", first=True)
    assert r["unmatched"] == ["annex-9"] and r["proposals"]


def test_refuses_to_overwrite(tpl, tmp_path):
    out = tmp_path / "o.docx"
    out.write_bytes(b"x")
    with pytest.raises(fp_docx.Refuse):
        fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), out, first=True)


def test_fields_only_on_first_build(tpl, tmp_path):
    v1 = tmp_path / "v1.docx"
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, first=True)
    with pytest.raises(fp_docx.Refuse):
        fp_docx.build(v1, tmp_path / "c.md", tmp_path / "v2.docx", fields={"Borrower": "X"})


def test_signature_ignores_word_save_noise(tpl, tmp_path):
    v1 = tmp_path / "v1.docx"
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, first=True)
    before = {s["id"]: fp_docx.signature(s) for s in fp_docx.Doc(v1).sections}
    with zipfile.ZipFile(v1) as z:
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    xml = parts["word/document.xml"]
    # Word adds revision ids and splits runs when it saves; meaning is unchanged.
    xml = xml.replace(b"<w:p>", b'<w:p w:rsidR="00AB12CD">')
    xml = xml.replace(b'<w:t xml:space="preserve">Approve.</w:t>',
                      b'<w:t xml:space="preserve">Appr</w:t></w:r><w:r><w:t xml:space="preserve">ove.</w:t>')
    parts["word/document.xml"] = xml
    with zipfile.ZipFile(v1, "w") as z:
        for name, data in parts.items():
            z.writestr(name, data)
    after = {s["id"]: fp_docx.signature(s) for s in fp_docx.Doc(v1).sections}
    assert before == after


def test_bold_change_counts_as_an_edit(tpl, tmp_path):
    v1 = tmp_path / "v1.docx"
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, first=True)
    fp_docx.edit_text(v1, '<w:r><w:t xml:space="preserve">Approve.</w:t>',
                      '<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">Approve.</w:t>')
    assert fp_docx.inspect(v1)["sections"][-1]["changed_since_build"] is True


def test_cli_selftest_and_check_exit_codes(tpl, tmp_path, capsys):
    assert fp_docx.main(["selftest"]) == 0
    assert "PASS" in capsys.readouterr().out
    assert fp_docx.main(["check", str(tpl), "--template", str(tpl)]) == 1   # template still has guidance


def test_officer_edit_survives_a_round_that_touched_another_section(tpl, tmp_path):
    # Review finding: officer edits A in v1; v2 updates B only; v3 must still refuse to overwrite A.
    v1, v2, v3 = (tmp_path / f"v{n}.docx" for n in (1, 2, 3))
    fp_docx.build(tpl, write(tmp_path / "c1.md", FIRST), v1, first=True)
    fp_docx.edit_text(v1, "Approve.", "Approve, in the officer's words.")
    fp_docx.build(v1, write(tmp_path / "c2.md", "## summary\nNew summary.\n"), v2)
    r = fp_docx.build(v2, write(tmp_path / "c3.md", "## recommendation\nDecline.\n"), v3)
    assert "recommendation" in r["frozen"]
    assert "officer's words" in fp_docx.to_markdown(v3)


def test_reviewer_can_read_kept_tables_and_reusing_the_text_does_not_duplicate_them(tpl, tmp_path):
    v1, v2 = tmp_path / "v1.docx", tmp_path / "v2.docx"
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, first=True)
    md = fp_docx.to_markdown(v1)
    assert "FY2025 (template)" in md                     # the template's kept table is readable
    fp_docx.build(v1, write(tmp_path / "again.md", md), v2)
    assert len(docx.Document(v2).tables) == len(docx.Document(v1).tables)


def test_cover_fields_fill_only_unprotected_cover_cells(tpl, tmp_path):
    fp_docx.edit_text(tpl, "<w:r><w:t>[amount]</w:t></w:r>",
                      '<w:ins w:id="9" w:author="Officer" w:date="2026-10-01T09:00:00Z"><w:r><w:t>[amount]</w:t></w:r></w:ins>')
    r = fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), tmp_path / "v1.docx", first=True,
                      fields={"Borrower": "Cedar Foods", "Amount": "EUR 12m", "EUR m": "overwritten?"})
    cells = [c.text for t in docx.Document(tmp_path / "v1.docx").tables for row in t.rows for c in row.cells]
    assert "Cedar Foods" in cells                        # ordinary cover cell is filled
    assert "EUR 12m" not in cells                        # a cell with tracked changes is protected
    assert "FY2025 (template)" in cells and "overwritten?" not in cells   # tables inside sections are not cover fields
    assert sorted(r["missing_fields"]) == ["Amount", "EUR m"]
````

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_fp_docx.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'fp_docx'`

- [ ] **Step 3: Create `tools/fp_docx.py`**

````python
#!/usr/bin/env python3
"""Read, build and check FP Word files with the Python standard library only.

document.xml is changed by splicing byte ranges; XML this tool did not generate is
never re-serialised, and every other file inside the .docx is copied unchanged.
A section is the body between one heading and the next heading of any level.

  fp_docx.py inspect DOCX [--markdown]
  fp_docx.py build --base BASE.docx --content CONTENT.md --out OUT.docx [--first] [--fields FIELDS.json]
  fp_docx.py check DOCX [--template TEMPLATE.docx]
  fp_docx.py selftest
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.parsers import expat
from xml.sax.saxutils import escape

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
AI_TAG = "fp-assistant"
ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
TAG = re.compile(r"\s*\[[SRMOGT]-\d+[^\]]*\]")
TAG_ID = re.compile(r"\b[SRMOGT]-\d+\b")
TRACKED = {"ins", "del", "moveFrom", "moveTo", "pPrChange", "rPrChange", "tblPrChange",
           "trPrChange", "tcPrChange", "sectPrChange", "cellIns", "cellDel"}
COMMENT = {"commentRangeStart", "commentRangeEnd", "commentReference"}
FIXED = {"drawing", "pict", "object", "fldChar", "fldSimple", "instrText", "sectPr", "sdt",
         "AlternateContent", "oMath"}


class Refuse(Exception):
    """A requested change is unsafe or impossible; nothing was written."""


# ---------- reading: byte-exact element tree ----------

def tag_end(buf, pos):
    """Index just past the '>' of the tag starting at pos, honouring quoted attributes."""
    quote, i = None, pos + 1
    while True:
        c = buf[i]
        if quote:
            if c == quote:
                quote = None
        elif c in (34, 39):
            quote = c
        elif c == 62:
            return i + 1
        i += 1


class Node:
    __slots__ = ("uri", "tag", "attrs", "start", "end", "parent", "kids", "text")

    def __init__(self, uri, tag, attrs, start, parent):
        self.uri, self.tag, self.attrs, self.start, self.parent = uri, tag, attrs, start, parent
        self.end, self.kids, self.text = None, [], []

    def iter(self):
        yield self
        for k in self.kids:
            yield from k.iter()

    def find(self, *path):
        n = self
        for t in path:
            n = next((k for k in n.kids if k.uri == W and k.tag == t), None)
            if n is None:
                return None
        return n

    def wattr(self, name):
        return self.attrs.get(f"{W} {name}")

    def deleted(self):
        n = self.parent
        while n is not None:
            if n.tag in ("del", "moveFrom"):
                return True
            n = n.parent
        return False

    def plain(self):
        """Text as if tracked changes were accepted."""
        return "".join("".join(n.text) for n in self.iter()
                       if n.uri == W and n.tag == "t" and not n.deleted())


def scan(buf):
    parser = expat.ParserCreate(namespace_separator=" ")
    parser.buffer_text = True
    stack, roots = [], []

    def start(name, attrs):
        uri, _, tag = name.rpartition(" ")
        node = Node(uri, tag, attrs, parser.CurrentByteIndex, stack[-1] if stack else None)
        (stack[-1].kids if stack else roots).append(node)
        stack.append(node)

    def end(name):
        node = stack.pop()
        se = tag_end(buf, node.start)
        node.end = se if buf[se - 2:se] == b"/>" else buf.index(b">", parser.CurrentByteIndex) + 1

    def data(text):
        if stack:
            stack[-1].text.append(text)

    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.CharacterDataHandler = data
    parser.Parse(buf, True)
    return roots[0]


def norm(text):
    text = re.sub(r"^\s*\d+(\.\d+)*\.?\s+", "", text or "")
    return re.sub(r"\s+", " ", text).strip().rstrip(":").strip().casefold()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", norm(text)).strip("-") or "section"


def style_info(styles_xml):
    """styleId -> (name, heading level or None); levels follow basedOn chains."""
    if not styles_xml:
        return {}
    w = "{%s}" % W
    raw = {}
    for s in ET.fromstring(styles_xml).iter(w + "style"):
        sid = s.get(w + "styleId")
        name = s.find(w + "name")
        lvl = s.find(f"{w}pPr/{w}outlineLvl")
        base = s.find(w + "basedOn")
        raw[sid] = (name.get(w + "val") if name is not None else sid,
                    int(lvl.get(w + "val")) if lvl is not None else None,
                    base.get(w + "val") if base is not None else None)

    def level(sid, seen=()):
        if sid not in raw or sid in seen:
            return None
        _, lvl, base = raw[sid]
        if lvl is not None:
            return lvl + 1 if lvl < 9 else None
        return level(base, seen + (sid,)) if base else None

    return {sid: (v[0], level(sid)) for sid, v in raw.items()}


class Doc:
    """A .docx opened for reading: zip entries, document.xml bytes, tree, styles, sections."""

    def __init__(self, path):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as z:
            self.infos = z.infolist()
            self.parts = {i.filename: z.read(i.filename) for i in self.infos}
        self.xml = self.parts["word/document.xml"]
        self.root = scan(self.xml)
        head = self.xml[self.root.start:tag_end(self.xml, self.root.start)]
        m = re.search(rb'xmlns:(\w+)="' + re.escape(W.encode()) + b'"', head)
        if not m:
            raise Refuse("the Word main namespace has no prefix; refusing to guess")
        self.w = m.group(1).decode()
        self.styles = style_info(self.parts.get("word/styles.xml"))
        self.style_id = {name: sid for sid, (name, _) in self.styles.items()}
        self.body = self.root.find("body")
        self.sections = self._sections()

    def level(self, node):
        if node.tag != "p":
            return None
        lvl = node.find("pPr", "outlineLvl")
        if lvl is not None:
            v = int(lvl.wattr("val"))
            return v + 1 if v < 9 else None
        ps = node.find("pPr", "pStyle")
        return self.styles.get(ps.wattr("val"), (None, None))[1] if ps is not None else None

    def _sections(self):
        kids = self.body.kids
        heads = [i for i, k in enumerate(kids) if self.level(k)]
        out, seen = [], {}
        for n, i in enumerate(heads):
            j = heads[n + 1] if n + 1 < len(heads) else len(kids)
            body = [k for k in kids[i + 1:j] if k.tag != "sectPr"]
            sid = slug(kids[i].plain())
            seen[sid] = seen.get(sid, 0) + 1
            if seen[sid] > 1:
                sid = f"{sid}-{seen[sid]}"
            out.append({"id": sid, "heading": kids[i].plain().strip(), "level": self.level(kids[i]),
                        "head": kids[i], "body": body})
        return out

    def comments(self):
        """Comment id -> {author, date, text}."""
        xml = self.parts.get("word/comments.xml")
        if not xml:
            return {}
        return {c.wattr("id"): {"author": c.wattr("author") or "", "date": c.wattr("date") or "",
                                "text": c.plain().strip()}
                for c in scan(xml).kids if c.tag == "comment"}


def para_sig(p):
    style = p.find("pPr", "pStyle")
    segs = []
    for r in (n for n in p.iter() if n.tag == "r"):
        rpr = r.find("rPr")
        fmt = "".join(k for k in ("b", "i", "u") if rpr is not None and rpr.find(k) is not None
                      and (rpr.find(k).wattr("val") or "true") not in ("0", "false", "none"))
        text = "".join("".join(n.text) for n in r.kids if n.tag in ("t", "delText"))
        if r.deleted():
            fmt += "-"
        if segs and segs[-1][1] == fmt:
            segs[-1][0] += text
        elif text:
            segs.append([text, fmt])
    marks = sorted({n.tag for n in p.iter()} & (FIXED | TRACKED | COMMENT))
    return f"P|{style.wattr('val') if style is not None else ''}|{segs}|{marks}"


def node_sig(k):
    if k.tag == "p":
        return para_sig(k)
    if k.tag == "tbl":
        rows = [[c.plain() for c in tr.kids if c.tag == "tc"] for tr in k.kids if tr.tag == "tr"]
        return f"T|{is_fixed(k)}|{rows}"
    return f"X|{k.tag}|{k.plain()}"


def signature(sec):
    data = "\n".join([node_sig(sec["head"])] + [node_sig(k) for k in sec["body"]])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def is_fixed(k):
    """Content this tool must keep in place: template tables, objects, fields, controls, breaks."""
    if k.tag == "tbl":
        d = k.find("tblPr", "tblDescription")
        return not (d is not None and d.wattr("val") == AI_TAG)
    if k.tag != "p":
        return True
    tags = {n.tag for n in k.iter()}
    if tags & FIXED:
        return True
    if any(n.tag == "bookmarkStart" and n.wattr("name") != "_GoBack" for n in k.iter()):
        return True
    style = k.find("pPr", "pStyle")
    return style is not None and "caption" in (style.wattr("val") or "").lower()


def flags(sec):
    tags = {n.tag for k in [sec["head"]] + sec["body"] for n in k.iter()}
    return {"has_comments": bool(tags & COMMENT), "has_tracked_changes": bool(tags & TRACKED),
            "fixed_objects": sum(is_fixed(k) for k in sec["body"])}


def section_comment_ids(sec):
    return sorted({n.wattr("id") for k in [sec["head"]] + sec["body"] for n in k.iter()
                   if n.tag in COMMENT})


def sidecar_path(docx):
    return Path(docx).with_suffix(".sections.json")


def load_sidecar(docx):
    p = sidecar_path(docx)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"sections": {}}


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- content markdown ----------

def parse_content(text):
    """'## section' blocks -> {section_id: {"blocks": [...], "raw": str, "ids": [...]}}."""
    raw, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(\S.*?)\s*$", line)
        if m and not line.startswith("###"):
            cur = slug(m.group(1))
            raw[cur] = []
        elif cur is not None:
            raw[cur].append(line)
    return {k: {"blocks": blocks(v), "raw": "\n".join(v).strip(),
                "ids": sorted(set(TAG_ID.findall("\n".join(v))))} for k, v in raw.items()}


def blocks(lines):
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append(("p", " ".join(para)))
            para.clear()

    while i < len(lines):
        s = lines[i].strip()
        keep = re.fullmatch(r"\{\{keep:(\d+)\}\}", s)
        if s.startswith("<!--"):  # read-only notes from inspect --markdown are never written
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if not s:
            flush()
        elif keep:
            flush()
            out.append(("keep", int(keep.group(1))))
        elif re.match(r"^[-*]\s+", s):
            flush()
            out.append(("bullet", re.sub(r"^[-*]\s+", "", s)))
        elif re.match(r"^\d+[.)]\s+", s):
            flush()
            out.append(("p", s))
        elif s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append(("table", rows))
            continue
        else:
            para.append(s)
        i += 1
    flush()
    return out


# ---------- writing ----------

class Gen:
    """WordprocessingML strings using the document's own prefix for the main namespace."""

    def __init__(self, doc):
        self.w, self.ids = doc.w, doc.style_id

    def runs(self, text):
        w, out = self.w, []
        text = ILLEGAL.sub("", TAG.sub("", text))
        for part in re.split(r"(\*\*[^*]+\*\*)", text):
            bold = len(part) > 4 and part.startswith("**") and part.endswith("**")
            body = part[2:-2] if bold else part
            if body:
                rpr = f"<{w}:rPr><{w}:b/></{w}:rPr>" if bold else ""
                out.append(f'<{w}:r>{rpr}<{w}:t xml:space="preserve">{escape(body)}</{w}:t></{w}:r>')
        return "".join(out)

    def p(self, text, style_id):
        w = self.w
        ppr = f'<{w}:pPr><{w}:pStyle {w}:val="{style_id}"/></{w}:pPr>' if style_id else ""
        return f"<{w}:p>{ppr}{self.runs(text)}</{w}:p>"

    def table(self, rows, width=9000):
        w, n = self.w, max(len(r) for r in rows)
        cw = width // n
        style = self.ids.get("Table Grid")
        tstyle = f'<{w}:tblStyle {w}:val="{style}"/>' if style else ""
        grid = "".join(f'<{w}:gridCol {w}:w="{cw}"/>' for _ in range(n))
        trs = "".join(f"<{w}:tr>" + "".join(
            f'<{w}:tc><{w}:tcPr><{w}:tcW {w}:w="{cw}" {w}:type="dxa"/></{w}:tcPr>'
            f"<{w}:p>{self.runs(r[c] if c < len(r) else '')}</{w}:p></{w}:tc>" for c in range(n))
            + f"</{w}:tr>" for r in rows)
        return (f"<{w}:tbl><{w}:tblPr>{tstyle}<{w}:tblW {w}:w=\"0\" {w}:type=\"auto\"/>"
                f'<{w}:tblDescription {w}:val="{AI_TAG}"/></{w}:tblPr>'
                f"<{w}:tblGrid>{grid}</{w}:tblGrid>{trs}</{w}:tbl>")


def render(doc, sec, items):
    """New XML for a section body; fixed content is placed at {{keep:N}} or appended."""
    gen = Gen(doc)
    fixed = [k for k in sec["body"] if is_fixed(k)]
    plain = [k for k in sec["body"] if not is_fixed(k) and k.tag == "p"]
    first = plain[0].find("pPr", "pStyle") if plain else None
    body_style = first.wattr("val") if first is not None else doc.style_id.get("Normal")
    bullet_style = doc.style_id.get("List Bullet")
    out, used = [], set()
    for kind, value in items:
        if kind == "p":
            out.append(gen.p(value, body_style))
        elif kind == "bullet":
            out.append(gen.p(value, bullet_style) if bullet_style else gen.p("• " + value, body_style))
        elif kind == "table" and value:
            out.append(gen.table(value))
        elif kind == "keep" and 1 <= value <= len(fixed) and value not in used:
            k = fixed[value - 1]
            out.append(doc.xml[k.start:k.end].decode("utf-8"))
            used.add(value)
    out += [doc.xml[k.start:k.end].decode("utf-8") for n, k in enumerate(fixed, 1) if n not in used]
    return "".join(out)


def splice(xml, edits):
    """Apply (start, end, replacement bytes) edits, last first so offsets stay valid."""
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        xml = xml[:start] + new + xml[end:]
    return xml


def fill_fields(doc, xml, fields):
    """Set the cell right of a matching label cell on the cover (before the first heading),
    keeping paragraph and run formatting. Cells with comments, tracked changes, fields,
    content controls or images are protected and left alone."""
    want, done, edits = {norm(k): str(v) for k, v in fields.items()}, set(), []
    limit = doc.sections[0]["head"].start if doc.sections else len(xml)  # sections are spliced after this point
    for tr in (n for n in scan(xml).iter() if n.tag == "tr" and n.start < limit):
        cells = [c for c in tr.kids if c.tag == "tc"]
        for label, value in zip(cells, cells[1:]):
            key = norm(label.plain())
            if key not in want or key in done:
                continue
            if {n.tag for n in value.iter()} & (COMMENT | TRACKED | FIXED):
                continue
            paras = [k for k in value.kids if k.tag == "p"]
            if not paras:
                continue
            ppr, run = paras[0].find("pPr"), paras[0].find("r")
            rpr = run.find("rPr") if run is not None else None
            w = doc.w
            new = (f"<{w}:p>{xml[ppr.start:ppr.end].decode() if ppr is not None else ''}<{w}:r>"
                   f"{xml[rpr.start:rpr.end].decode() if rpr is not None else ''}"
                   f'<{w}:t xml:space="preserve">{escape(ILLEGAL.sub("", want[key]))}</{w}:t></{w}:r></{w}:p>')
            edits.append((paras[0].start, paras[-1].end, new.encode("utf-8")))
            done.add(key)
    return splice(xml, edits), sorted(k for k in fields if norm(k) not in done)


def write_docx(doc, xml, out):
    """Validate the new document.xml, write the zip to a temp file, re-read it, then rename."""
    new_root = scan(xml)
    if new_root.find("body") is None:
        raise Refuse("generated document has no body")
    out = Path(out)
    fd, tmp = tempfile.mkstemp(dir=out.parent, suffix=".docx.tmp")
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w") as z:
            for info in doc.infos:
                z.writestr(info, xml if info.filename == "word/document.xml" else doc.parts[info.filename])
        check_doc = Doc(tmp)
        if [s["id"] for s in check_doc.sections] != [s["id"] for s in doc.sections]:
            raise Refuse("headings changed during the build; nothing written")
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def build(base, content, out, first=False, fields=None):
    out = Path(out)
    if out.exists():
        raise Refuse(f"{out.name} already exists; choose a new version name")
    doc = Doc(base)
    baseline = {} if first else load_sidecar(base)["sections"]
    wanted = parse_content(Path(content).read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in doc.sections}
    base_sig = {sid: signature(sec) for sid, sec in by_id.items()}
    edits, written, frozen, unmatched = [], [], {}, []
    for sid, item in wanted.items():
        sec = by_id.get(sid)
        if sec is None:
            unmatched.append(sid)
            continue
        f = flags(sec)
        if f["has_comments"] or f["has_tracked_changes"]:
            frozen[sid] = "has comments or tracked changes"
            continue
        if not first:
            b = baseline.get(sid, {})
            if b.get("owner") != "ai":
                frozen[sid] = "not written by the assistant in the base version"
                continue
            if b.get("signature") != signature(sec):
                frozen[sid] = "edited since the assistant wrote it"
                continue
        if sec["body"]:
            start, end = sec["body"][0].start, sec["body"][-1].end
        else:
            start = end = sec["head"].end
        edits.append((start, end, render(doc, sec, item["blocks"]).encode("utf-8")))
        written.append(sid)
    xml = splice(doc.xml, edits)
    missing_fields = []
    if fields:
        if not first:
            raise Refuse("--fields is only allowed with --first; later rounds keep the officer's cover page")
        xml, missing_fields = fill_fields(doc, xml, fields)
    write_docx(doc, xml, out)
    new = Doc(out)
    sections = {}
    for sec in new.sections:
        sid = sec["id"]
        old = baseline.get(sid, {})
        # Stays assistant-owned only if nobody changed it since the assistant wrote it.
        untouched_ai = (not first and old.get("owner") == "ai" and sid not in frozen and sid not in written
                        and old.get("signature") == base_sig.get(sid))
        sections[sid] = {"owner": "ai" if sid in written or untouched_ai else "other",
                         "signature": signature(sec),
                         "ids": wanted[sid]["ids"] if sid in written else old.get("ids", [])}
    sidecar_path(out).write_text(json.dumps(
        {"base": Path(base).name, "docx_sha256": file_sha256(out), "sections": sections}, indent=1),
        encoding="utf-8")
    proposals = None
    if frozen or unmatched:
        proposals = out.with_suffix(".proposals.md")
        lines = [f"# Proposed text not applied to {out.name}", "",
                 "These sections were left exactly as they are. Copy what you want into Word.", ""]
        for sid in list(frozen) + unmatched:
            reason = frozen.get(sid, "no section with this heading in the document")
            lines += [f"## {sid}", f"_Not applied: {reason}._", "", wanted[sid]["raw"], ""]
        proposals.write_text("\n".join(lines), encoding="utf-8")
    return {"out": str(out), "written": written, "frozen": frozen, "unmatched": unmatched,
            "missing_fields": missing_fields, "proposals": str(proposals) if proposals else None,
            "sha256": file_sha256(out)}


# ---------- inspect and check ----------

def inspect(path):
    doc = Doc(path)
    baseline = load_sidecar(path)["sections"]
    comments = doc.comments()
    sections = []
    for sec in doc.sections:
        b = baseline.get(sec["id"], {})
        info = {"id": sec["id"], "heading": sec["heading"], "level": sec["level"],
                "owner": b.get("owner", "unknown"),
                "changed_since_build": bool(b) and b.get("signature") != signature(sec),
                **flags(sec)}
        sections.append(info)
    where = {cid: s["id"] for s in doc.sections for cid in section_comment_ids(s)}
    return {"file": str(path), "sha256": file_sha256(path), "sections": sections,
            "comments": [{"id": cid, "section": where.get(cid), **c} for cid, c in comments.items()]}


def to_markdown(path):
    doc = Doc(path)
    lines = []
    for sec in doc.sections:
        lines += [f"## {sec['id']}", ""]
        fixed_no = 0
        for k in sec["body"]:
            if is_fixed(k):
                fixed_no += 1
                lines.append(f"{{{{keep:{fixed_no}}}}}")
                if k.tag == "tbl":  # readable for reviewers; build ignores <!-- --> notes
                    lines.append("<!-- kept table, read-only:")
                    lines += ["| " + " | ".join(c.plain() for c in tr.kids if c.tag == "tc") + " |"
                              for tr in k.kids if tr.tag == "tr"]
                    lines.append("-->")
                elif k.plain().strip():
                    lines.append(f"<!-- kept, read-only: {k.plain().strip()} -->")
                lines.append("")
            elif k.tag == "tbl":
                for tr in (r for r in k.kids if r.tag == "tr"):
                    lines.append("| " + " | ".join(c.plain() for c in tr.kids if c.tag == "tc") + " |")
                lines.append("")
            elif k.plain().strip():
                ps = k.find("pPr", "pStyle")
                name = doc.styles.get(ps.wattr("val"), ("",))[0] if ps is not None else ""
                prefix = "- " if "list" in name.lower() else ""
                lines += [prefix + k.plain().strip(), ""]
    comments = inspect(path)["comments"]
    if comments:
        lines += ["## comments (not part of the FP)", ""]
        lines += [f"- [{c['section']}] {c['author']}: {c['text']}" for c in comments]
    return "\n".join(lines).rstrip() + "\n"


def check(path, template=None):
    problems = []
    doc = Doc(path)
    text = "\n".join(k.plain() for k in doc.body.kids)
    if TAG.search(text):
        problems.append("source tags left in the text")
    if "{{keep:" in text:
        problems.append("unplaced {{keep:N}} markers left in the text")
    if template:
        tpl = Doc(template)
        ids = [s["id"] for s in doc.sections]
        missing = [s["id"] for s in tpl.sections if s["id"] not in ids]
        if missing:
            problems.append(f"template sections missing or renamed: {', '.join(missing)}")
        by_id = {s["id"]: s for s in doc.sections}
        for s in tpl.sections:
            guidance = " ".join(k.plain() for k in s["body"]).strip()
            mine = by_id.get(s["id"])
            if guidance and mine and " ".join(k.plain() for k in mine["body"]).strip() == guidance:
                problems.append(f"{s['id']}: still contains the template's guidance text")
    info = inspect(path)
    return {"file": str(path), "problems": problems,
            "sections_with_comments": [s["id"] for s in info["sections"] if s["has_comments"]],
            "sections_with_tracked_changes": [s["id"] for s in info["sections"] if s["has_tracked_changes"]]}


# ---------- self-test (also used by the unit tests) ----------

def make_template(path, comment_on=None):
    """A small but realistic FP template: cover table, headings, guidance, a fixed table."""
    w = f'xmlns:w="{W}"'
    style = lambda sid, name, lvl=None: (  # noqa: E731
        f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/>'
        + (f'<w:pPr><w:outlineLvl w:val="{lvl}"/></w:pPr>' if lvl is not None else "") + "</w:style>")
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {w}>'
              + style("Normal", "Normal") + style("Heading1", "heading 1", 0) + style("Heading2", "heading 2", 1)
              + style("ListBullet", "List Bullet")
              + '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/></w:style></w:styles>')
    p = lambda text, sid="Normal": (  # noqa: E731
        f'<w:p><w:pPr><w:pStyle w:val="{sid}"/></w:pPr><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')
    cell = lambda text: f"<w:tc><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"  # noqa: E731
    cover = ("<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr><w:tblGrid><w:gridCol w:w=\"3000\"/>"
             "<w:gridCol w:w=\"6000\"/></w:tblGrid>"
             f"<w:tr>{cell('Borrower:')}{cell('[name]')}</w:tr><w:tr>{cell('Amount:')}{cell('[amount]')}</w:tr></w:tbl>")
    fin = ("<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr><w:tblGrid><w:gridCol w:w=\"4500\"/>"
           f"<w:gridCol w:w=\"4500\"/></w:tblGrid><w:tr>{cell('EUR m')}{cell('FY2025 (template)')}</w:tr></w:tbl>")
    risk_guidance = p("[Describe market risks]")
    if comment_on == "market-risk":
        risk_guidance = ('<w:p><w:commentRangeStart w:id="1"/><w:r><w:t>[Describe market risks]</w:t></w:r>'
                         '<w:commentRangeEnd w:id="1"/><w:r><w:commentReference w:id="1"/></w:r></w:p>')
    body = (cover + p("1. Summary", "Heading1") + p("[Summarise the proposal]")
            + p("2. Financial analysis", "Heading1") + p("[Explain the figures]") + fin
            + p("2.1 Market risk", "Heading2") + risk_guidance
            + p("3. Recommendation", "Heading1") + p("[State the recommendation]")
            + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>')
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {w}>'
                f"<w:body>{body}</w:body></w:document>")
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            + ('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
               'relationships/comments" Target="comments.xml"/>' if comment_on else "") + "</Relationships>")
    types = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/'
             '2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
             'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
             'wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/'
             'vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
             + ('<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.comments+xml"/>' if comment_on else "") + "</Types>")
    root_rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
                 'package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                 'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", rels)
        if comment_on:
            z.writestr("word/comments.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:comments {w}>'
                       '<w:comment w:id="1" w:author="Officer" w:date="2026-10-01T09:00:00Z"><w:p><w:r>'
                       "<w:t>Check the FX exposure</w:t></w:r></w:p></w:comment></w:comments>")


def edit_text(path, old, new):
    """Simulate an officer editing text in Word (test helper)."""
    with zipfile.ZipFile(path) as z:
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    assert old.encode() in parts["word/document.xml"], old
    parts["word/document.xml"] = parts["word/document.xml"].replace(old.encode(), new.encode(), 1)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)


def selftest():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        make_template(d / "template.docx")
        (d / "v1.md").write_text(
            "## summary\nCedar Foods seeks EUR 12m. [S-001 p.2]\n\n## financial-analysis\n"
            "Revenue rose 20% on a restated basis. [S-002 p.20]\n\n{{keep:1}}\n\n## market-risk\n"
            "- Milk prices rose. [S-003]\n\n## recommendation\nApprove, subject to conditions.\n", encoding="utf-8")
        r1 = build(d / "template.docx", d / "v1.md", d / "FP-v01.docx", first=True,
                   fields={"Borrower": "Cedar Foods", "Amount": "EUR 12m"})
        assert r1["written"] == ["summary", "financial-analysis", "market-risk", "recommendation"], r1
        assert not check(d / "FP-v01.docx", d / "template.docx")["problems"]
        edit_text(d / "FP-v01.docx", "Approve, subject to conditions.", "Approve, subject to two conditions.")
        (d / "v2.md").write_text("## summary\nCedar Foods seeks EUR 12m of working capital.\n\n"
                                 "## recommendation\nApprove.\n", encoding="utf-8")
        r2 = build(d / "FP-v01.docx", d / "v2.md", d / "FP-v02.docx")
        assert r2["written"] == ["summary"] and "recommendation" in r2["frozen"], r2
        assert "two conditions" in to_markdown(d / "FP-v02.docx")
        assert "EUR 12m of working capital" in to_markdown(d / "FP-v02.docx")
    return f"PASS fp_docx selftest (Python {sys.version.split()[0]})"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("inspect")
    a.add_argument("docx")
    a.add_argument("--markdown", action="store_true")
    b = sub.add_parser("build")
    b.add_argument("--base", required=True)
    b.add_argument("--content", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--first", action="store_true")
    b.add_argument("--fields")
    c = sub.add_parser("check")
    c.add_argument("docx")
    c.add_argument("--template")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "inspect":
            print(to_markdown(args.docx) if args.markdown else json.dumps(inspect(args.docx), indent=1))
        elif args.cmd == "build":
            fields = json.loads(Path(args.fields).read_text(encoding="utf-8")) if args.fields else None
            print(json.dumps(build(args.base, args.content, args.out, args.first, fields), indent=1))
        elif args.cmd == "check":
            result = check(args.docx, args.template)
            print(json.dumps(result, indent=1))
            return 1 if result["problems"] else 0
        else:
            print(selftest())
    except (Refuse, KeyError, zipfile.BadZipFile, expat.ExpatError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [ ] **Step 4: Run the tests, then the self-test on Python 3.9 without extra libraries**

Run: `uv run pytest tests/test_fp_docx.py -q`
Expected: `12 passed`

Run: `uv run --no-project --python 3.9 python tools/fp_docx.py selftest`
Expected: `PASS fp_docx selftest (Python 3.9.x)`

- [ ] **Step 5: Commit**

```bash
git add tools/fp_docx.py tests/test_fp_docx.py
git commit -m "Add standard-library Word tool that never overwrites the officer's sections"
```

---

### Task 3: Register tool (`tools/register.py`)

**Files:**
- Create: `tools/register.py`
- Test: `tests/test_register.py`

**Interfaces:**
- Produces: `new_register(deal) -> dict`, `load(folder)`, `save(folder, reg)`, `apply(folder, changes) -> dict` (keys `status, revision, ids, warnings`; status `applied` or `already-applied`), `problems(reg, today=None) -> list[tuple]`, `gates(reg) -> list[str]`, `open_checks(reg, word=None) -> list[str]`, `summary(reg, word=None) -> str`, `show(reg, ids) -> str`, `lists(reg) -> str`, `write_views(folder, reg)`, `write_xlsx(path, sheets)` (also used by `fin_table.selftest`), `sha256(path)`, `ChangeError`, `selftest() -> str`.
- Files in FOLDER: `register.json` (record), `register.xlsx` and `Analysis.md` (views).
- Change set: `{"base_revision": N, "op_id": str, "actor": str, "summary": str, "next_step": str, "changes": [{"sheet": ..., "add": {...}} | {"sheet": ..., "update": ID, "set": {...}} | {"sheet": "control", "set": {...}}]}`.
- Open-item statuses: `open` → `promised` → `answered` → `closed`. Only `closed` finishes an item. New sources default to `impact: pending`, `coverage: unread`.
- Readiness: setting control `status` to `ready` records `ready_for` (Word file and revision) and `ready_by`. It is refused while `open_checks` is non-empty, and withdrawn automatically when new open work arrives. Output wording: "Register checks: passed / not passed".
- Command line: `init FOLDER --deal KEY`, `summary FOLDER [--word]`, `show FOLDER IDS...`, `apply FOLDER CHANGES.json`, `lists FOLDER`, `check FOLDER [--word]`, `selftest`. Exit codes: 0 ok, 1 rule errors (`check`), 3 refused.

- [ ] **Step 1: Write the failing tests** — `tests/test_register.py`

````python
import datetime
import json

import openpyxl  # dev-only independent reader; the tool itself uses the standard library
import pytest

import register as reg_tool


@pytest.fixture
def folder(tmp_path):
    reg_tool.save(tmp_path, reg_tool.new_register("Cedar"))
    return tmp_path


def change(base, op, *changes, **extra):
    return {"base_revision": base, "op_id": op, "actor": "test", "summary": op, "changes": list(changes), **extra}


RISK = {"sheet": "risks", "add": {"title": "FX mismatch", "raised_by": "E&S specialist", "rating": "high",
                                  "destination": "main", "reason": "affects repayment", "status": "open"}}


def test_ids_are_assigned_and_revision_advances(folder):
    r = reg_tool.apply(folder, change(0, "a", RISK, {"sheet": "risks", "add": dict(RISK["add"], title="Customer")}))
    assert r == {"status": "applied", "revision": 1, "ids": ["R-001", "R-002"], "warnings": []}
    assert reg_tool.load(folder)["log"][-1]["op_id"] == "a"


def test_stale_and_duplicate_change_sets(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    with pytest.raises(reg_tool.ChangeError, match="stale"):
        reg_tool.apply(folder, change(0, "b", RISK))
    assert reg_tool.apply(folder, change(0, "a", RISK))["status"] == "already-applied"
    assert len(reg_tool.load(folder)["risks"]) == 1


@pytest.mark.parametrize("bad, message", [
    ({"sheet": "mitigants", "add": {"risk": "R-009", "raised_by": "x"}}, "unknown risk"),
    ({"sheet": "mitigants", "add": {"risk": "R-001", "raised_by": "x", "verified": "yes"}}, "needs a source"),
    ({"sheet": "open_items", "add": {"text": "q", "raised_by": "x", "status": "answered"}}, "answer source"),
    ({"sheet": "risks", "add": {"title": "t", "rating": "high"}}, "who raised"),
    ({"sheet": "risks", "add": {"title": "t", "raised_by": "x", "rating": "huge"}}, "rating"),
    ({"sheet": "risks", "update": "R-001", "set": {"destination": "background"}}, "officer's decision"),
    ({"sheet": "open_items", "add": {"text": "q", "raised_by": "x", "link": "R-001", "criticality": "later"}},
     "officer_ok"),
    ({"sheet": "nonsense", "add": {}}, "unknown sheet"),
    ({"sheet": "risks", "add": {"colour": "red"}}, "no field"),
])
def test_rule_violations_reject_the_whole_change_set(folder, bad, message):
    reg_tool.apply(folder, change(0, "a", RISK))
    with pytest.raises(reg_tool.ChangeError, match=message):
        reg_tool.apply(folder, change(1, "b", {"sheet": "sources", "add": {"title": "kept?"}}, bad))
    assert reg_tool.load(folder)["sources"] == []   # nothing from the rejected set was saved


def test_downgrade_needs_officer_decision(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    with pytest.raises(reg_tool.ChangeError, match="downgrading high to medium"):
        reg_tool.apply(folder, change(1, "b", {"sheet": "risks", "update": "R-001", "set": {"rating": "medium"}}))
    ok = {"sheet": "risks", "update": "R-001",
          "set": {"rating": "medium", "officer_decision": "Officer, 2 Oct: hedge confirmed"}}
    assert reg_tool.apply(folder, change(1, "c", ok))["status"] == "applied"


def test_officer_ok_allows_later_diligence(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    item = {"text": "Check FX hedging policy", "raised_by": "credit", "link": "R-001", "criticality": "later",
            "officer_ok": "yes", "status": "open"}
    assert reg_tool.apply(folder, change(1, "b", {"sheet": "open_items", "add": item}))["status"] == "applied"


def test_ready_gate_blocks_and_word_change_invalidates(folder, tmp_path):
    word = tmp_path / "FP-v01.docx"
    word.write_bytes(b"v1")
    reg_tool.apply(folder, change(0, "a", RISK, {"sheet": "open_items", "add": {
        "text": "Borrower cash flow", "raised_by": "officer", "criticality": "blocker", "status": "open",
        "addressee": "client"}}, {"sheet": "control", "set": {"word": word.name, "word_sha256": reg_tool.sha256(word)}}))
    with pytest.raises(reg_tool.ChangeError, match="cannot record ready"):
        reg_tool.apply(folder, change(1, "b", {"sheet": "control", "set": {"status": "ready"}}))
    reg_tool.apply(folder, change(1, "c", {"sheet": "open_items", "update": "O-001",
                                           "set": {"status": "closed", "answer_source": "S-004 p.2"}}))
    reg = reg_tool.load(folder)
    assert reg_tool.open_checks(reg, word) == []
    word.write_bytes(b"v1 edited by officer")
    assert reg_tool.open_checks(reg, word) == ["the Word file changed since it was last recorded"]


def test_new_source_with_pending_impact_blocks_ready(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "sources", "add": {"title": "Lender email: covenant breach",
                                                                       "impact": "pending", "tier": "A"}}))
    reasons = reg_tool.open_checks(reg_tool.load(folder))
    assert reasons == ["source impact not assessed: S-001"]


def test_stale_sources_warning(folder):
    old = (datetime.date.today() - datetime.timedelta(days=500)).isoformat()
    reg_tool.apply(folder, change(0, "a", {"sheet": "sources", "add": {"title": "AR 2023", "event_date": old}},
                                  {"sheet": "fp_map", "add": {"version": "v01", "section": "summary", "ids": "S-001"}}))
    assert any(p[1] == "stale-sources" for p in reg_tool.problems(reg_tool.load(folder)))


def test_analysis_upsert_and_markdown_view(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "analysis", "update": "timeline",
                                           "set": {"title": "Last two years", "text": "2025: new plant."}}))
    reg_tool.apply(folder, change(1, "b", {"sheet": "analysis", "update": "timeline", "set": {"text": "2026: CFO left."}}))
    md = (folder / "Analysis.md").read_text()
    assert "2026: CFO left." in md and "2025: new plant." not in md and "revision 2" in md


def test_excel_view_opens_in_an_independent_reader(folder):
    reg_tool.apply(folder, change(0, "a", RISK))
    wb = openpyxl.load_workbook(folder / "register.xlsx")
    assert wb.sheetnames[:3] == ["Control", "Sources", "Risks"]
    assert wb["Risks"]["A2"].value == "R-001" and wb["Risks"]["B2"].value == "FX mismatch"
    assert wb["Control"]["B2"].value == "Cedar"


def test_summary_lists_show_and_cli(folder, tmp_path, capsys):
    reg_tool.apply(folder, change(0, "a", RISK, {"sheet": "open_items", "add": {
        "text": "Revenue split by currency", "raised_by": "officer", "link": "R-001", "criticality": "blocker",
        "status": "open", "addressee": "client", "due": "2026-10-10"}},
        {"sheet": "mitigants", "add": {"risk": "R-001", "text": "Hedging covenant", "type": "proposed-condition",
                                       "raised_by": "credit"}}, next_step="Grill v01 in a new task"))
    reg = reg_tool.load(folder)
    text = reg_tool.summary(reg)
    assert "Next: Grill v01 in a new task" in text and "O-001 [blocker] client" in text
    assert len(text.splitlines()) <= 40
    assert "Revenue split by currency" in reg_tool.lists(reg) and "M-001 (R-001)" in reg_tool.lists(reg)
    assert "mitigant M-001" in reg_tool.show(reg, ["R-001"])
    changes = tmp_path / "c.json"
    changes.write_text(json.dumps(change(1, "cli", {"sheet": "control", "set": {"officer": "Rik"}})))
    assert reg_tool.main(["apply", str(folder), str(changes)]) == 0
    assert reg_tool.main(["apply", str(folder), str(changes)]) == 0   # retry is a no-op
    assert reg_tool.load(folder)["revision"] == 2
    assert reg_tool.main(["selftest"]) == 0


def test_new_questions_default_open_and_new_sources_pending(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "open_items", "add": {"text": "Borrower forecast", "raised_by": "officer"}},
                                  {"sheet": "sources", "add": {"title": "Email from CFO"}}))
    reg = reg_tool.load(folder)
    assert reg["open_items"][0]["status"] == "open" and reg["sources"][0]["impact"] == "pending"
    assert "O-001" in reg_tool.lists(reg)


def test_promised_and_answered_items_stay_visible_until_closed(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "open_items", "add": {
        "text": "Monthly borrower forecast", "raised_by": "officer", "criticality": "blocker", "addressee": "client"}}))
    # "We will send the forecast on Friday" is a promise, not the forecast.
    reg_tool.apply(folder, change(1, "b", {"sheet": "open_items", "update": "O-001", "set": {
        "status": "promised", "answer": "CFO: will send Friday", "due": "2026-10-09"}}))
    reg = reg_tool.load(folder)
    assert "O-001" in reg_tool.lists(reg) and any("O-001" in r for r in reg_tool.gates(reg))
    reg_tool.apply(folder, change(2, "c", {"sheet": "open_items", "update": "O-001", "set": {
        "status": "answered", "answer_source": "S-001 forecast file"}}))
    reg = reg_tool.load(folder)
    assert "awaiting assessment" in reg_tool.lists(reg) and any("O-001" in r for r in reg_tool.gates(reg))
    reg_tool.apply(folder, change(3, "d", {"sheet": "open_items", "update": "O-001", "set": {"status": "closed"}}))
    reg = reg_tool.load(folder)
    assert "O-001" not in reg_tool.lists(reg) and reg_tool.gates(reg) == []


def test_tool_reports_checks_and_readiness_is_recorded_for_a_version(folder, tmp_path):
    word = tmp_path / "FP-v05.docx"
    word.write_bytes(b"v5")
    reg_tool.apply(folder, change(0, "a", {"sheet": "control", "set": {"word": word.name, "word_sha256": reg_tool.sha256(word)}}))
    assert "Register checks: passed" in reg_tool.summary(reg_tool.load(folder), word)
    reg_tool.apply(folder, change(1, "b", {"sheet": "control", "set": {"status": "ready", "ready_by": "Officer"}}))
    reg = reg_tool.load(folder)
    assert reg["control"]["ready_for"] == f"{word.name} at register revision 2"
    assert "Status: ready (FP-v05.docx at register revision 2, recorded by Officer)" in reg_tool.summary(reg, word)
    word.write_bytes(b"v5 edited")
    assert "changed since readiness was recorded" in reg_tool.summary(reg, word)


def test_retry_repairs_views_left_stale_by_an_interrupted_run(folder, monkeypatch):
    real = reg_tool.write_views
    monkeypatch.setattr(reg_tool, "write_views", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        reg_tool.apply(folder, change(0, "a", RISK))
    monkeypatch.setattr(reg_tool, "write_views", real)
    assert "revision 0" in (folder / "Analysis.md").read_text()      # views are stale, the record is not
    assert reg_tool.apply(folder, change(0, "a", RISK))["status"] == "already-applied"
    assert "revision 1" in (folder / "Analysis.md").read_text()


def test_new_evidence_after_ready_withdraws_readiness_instead_of_blocking(folder):
    reg_tool.apply(folder, change(0, "a", {"sheet": "control", "set": {"status": "ready", "ready_by": "FP Lead"}}))
    r = reg_tool.apply(folder, change(1, "b", {"sheet": "sources", "add": {"title": "Lender email: covenant breach"}}))
    assert r["status"] == "applied" and r["warnings"][0].startswith("readiness withdrawn")
    assert reg_tool.load(folder)["control"]["status"] == "draft"
````

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_register.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'register'`

- [ ] **Step 3: Create `tools/register.py`**

````python
#!/usr/bin/env python3
"""The FP deal register: one JSON file of record plus generated Excel and Markdown views.

  register.py init FOLDER --deal KEY
  register.py summary FOLDER [--word DOCX]
  register.py show FOLDER ID [ID ...]
  register.py apply FOLDER CHANGES.json
  register.py lists FOLDER
  register.py check FOLDER [--word DOCX]
  register.py selftest

FOLDER is a local copy of the deal's "FP assistant" folder. register.json is the record.
register.xlsx and Analysis.md are rewritten from it after every change; they are read-only views.
Standard library only.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

TABLES = {  # name: (id prefix, columns)
    "sources": ("S", ["id", "title", "link", "type", "entity", "period", "event_date", "tier",
                      "coverage", "impact", "notes"]),
    "risks": ("R", ["id", "title", "topic", "raised_by", "rating", "residual", "destination",
                    "reason", "status", "officer_decision"]),
    "mitigants": ("M", ["id", "risk", "text", "type", "verified", "source", "raised_by", "status"]),
    "open_items": ("O", ["id", "kind", "text", "link", "addressee", "raised_by", "owner",
                         "criticality", "status", "answer", "answer_source", "due", "officer_ok"]),
    "findings": ("", ["id", "by", "version", "section", "issue", "priority", "status", "resolution"]),
    "analysis": ("", ["id", "title", "text", "sources", "updated"]),
    "fp_map": ("", ["id", "version", "section", "owner", "ids"]),
}
CONTROL = ["deal", "officer", "decision_sought", "recommendation", "audience", "annexes", "deadline",
           "template", "word", "word_sha256", "status", "ready_for", "ready_by", "updated"]
ALLOWED = {
    ("sources", "tier"): {"A", "B", "C"},
    ("sources", "coverage"): {"unread", "partial", "read", "unreadable"},
    ("sources", "impact"): {"pending", "assessed", "no-impact"},
    ("risks", "rating"): {"high", "medium", "low"},
    ("risks", "residual"): {"high", "medium", "low", "unclear"},
    ("risks", "destination"): {"main", "annex", "background", "unresolved"},
    ("risks", "status"): {"open", "assessed", "recheck", "closed"},
    ("mitigants", "type"): {"existing", "proposed-condition", "assumption"},
    ("mitigants", "verified"): {"yes", "no"},
    ("open_items", "kind"): {"question", "action", "credit-question", "prior-issue"},
    ("open_items", "criticality"): {"blocker", "material", "later"},
    ("open_items", "status"): {"open", "promised", "answered", "closed"},  # only closed is finished
    ("open_items", "officer_ok"): {"yes", "no"},
    ("findings", "by"): {"grill", "style"},
    ("findings", "priority"): {"blocker", "material", "minor"},
    ("findings", "status"): {"open", "resolved", "officer-judgment"},
    ("control", "status"): {"draft", "ready", "submitted"},
}
ID_RE = re.compile(r"\b[SRMOGT]-\d+\b")
ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
CLIENT = ("client", "borrower", "sponsor", "company")
DEFAULTS = {"open_items": {"status": "open"}, "sources": {"impact": "pending", "coverage": "unread"},
            "risks": {"status": "open"}}  # unfinished work stays visible until someone closes it


class ChangeError(Exception):
    """A change set was rejected; the register is unchanged."""


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- storage ----------

def new_register(deal):
    reg = {"revision": 0, "control": {k: "" for k in CONTROL}, "log": []}
    reg["control"].update(deal=deal, status="draft", updated=now())
    reg.update({name: [] for name in TABLES})
    return reg


def load(folder):
    path = Path(folder) / "register.json"
    if not path.exists():
        raise ChangeError(f"no register.json in {folder}; run init first")
    return json.loads(path.read_text(encoding="utf-8"))


def save(folder, reg):
    """Write register.json atomically, then regenerate the views."""
    folder = Path(folder)
    data = json.dumps(reg, indent=1, ensure_ascii=False)
    json.loads(data)
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".json.tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp, folder / "register.json")
    write_views(folder, reg)


def write_views(folder, reg):
    folder = Path(folder)
    sheets = [("Control", ["field", "value"], [[k, reg["control"].get(k, "")] for k in CONTROL])]
    for name, (_, cols) in TABLES.items():
        sheets.append((name.replace("_", " ").capitalize(), cols, [[r.get(c, "") for c in cols] for r in reg[name]]))
    sheets.append(("Check", ["severity", "rule", "item", "detail"], [list(p) for p in problems(reg)]))
    sheets.append(("Log", ["at", "revision", "actor", "op_id", "summary", "next_step"],
                   [[e.get(c, "") for c in ("at", "revision", "actor", "op_id", "summary", "next_step")]
                    for e in reg["log"]]))
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".xlsx.tmp")
    os.close(fd)
    write_xlsx(tmp, sheets)
    with zipfile.ZipFile(tmp) as z:
        if z.testzip() is not None:
            raise ChangeError("generated register.xlsx failed its integrity check")
    os.replace(tmp, folder / "register.xlsx")
    (folder / "Analysis.md").write_text(analysis_md(reg), encoding="utf-8")


def write_xlsx(path, sheets):
    """Minimal valid workbook: inline strings, bold header, wrapped text, frozen first row."""
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    pkg = "http://schemas.openxmlformats.org/package/2006/relationships"

    def col(i):
        s, i = "", i + 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s

    def cell(ref, value, style):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
        text = escape(ILLEGAL.sub("", str(value))[:32000])
        return f'<c r="{ref}" t="inlineStr" s="{style}"><is><t xml:space="preserve">{text}</t></is></c>'

    files = {}
    for n, (_, header, rows) in enumerate(sheets, 1):
        widths = [min(60, max([len(str(h)) + 2] + [len(str(r[i])) + 2 for r in rows[:200]]))
                  for i, h in enumerate(header)]
        cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths))
        data = [f'<row r="1">' + "".join(cell(f"{col(i)}1", h, 1) for i, h in enumerate(header)) + "</row>"]
        for r, row in enumerate(rows, 2):
            data.append(f'<row r="{r}">' + "".join(cell(f"{col(i)}{r}", v, 2)
                                                   for i, v in enumerate(row) if v not in ("", None)) + "</row>")
        files[f"xl/worksheets/sheet{n}.xml"] = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{main}">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
            f'state="frozen"/></sheetView></sheetViews><cols>{cols}</cols><sheetData>{"".join(data)}</sheetData>'
            "</worksheet>")
    names = "".join(f'<sheet name="{escape(name[:31])}" sheetId="{n}" r:id="rId{n}"/>'
                    for n, (name, _, _) in enumerate(sheets, 1))
    files["xl/workbook.xml"] = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                                f'<workbook xmlns="{main}" xmlns:r="{rel}"><sheets>{names}</sheets></workbook>')
    links = "".join(f'<Relationship Id="rId{n}" Type="{rel}/worksheet" Target="worksheets/sheet{n}.xml"/>'
                    for n in range(1, len(sheets) + 1))
    files["xl/_rels/workbook.xml.rels"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{pkg}">{links}'
        f'<Relationship Id="rId{len(sheets) + 1}" Type="{rel}/styles" Target="styles.xml"/></Relationships>')
    files["xl/styles.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{main}">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/>'
        '<name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/>'
        '<top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" '
        'fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" '
        'borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment '
        'wrapText="1" vertical="top"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" '
        'builtinId="0"/></cellStyles></styleSheet>')
    files["_rels/.rels"] = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships '
                            f'xmlns="{pkg}"><Relationship Id="rId1" Type="{rel}/officeDocument" '
                            'Target="xl/workbook.xml"/></Relationships>')
    sheet_types = "".join(f'<Override PartName="/xl/worksheets/sheet{n}.xml" ContentType="application/'
                          'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                          for n in range(1, len(sheets) + 1))
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/'
        'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-'
        'package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override '
        'PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.'
        'sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-'
        f'officedocument.spreadsheetml.styles+xml"/>{sheet_types}</Types>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ["[Content_Types].xml", "_rels/.rels"] + sorted(n for n in files if n.startswith("xl/")):
            z.writestr(name, files[name])


def analysis_md(reg):
    first = ["strategy", "timeline", "key-figures"]
    rows = sorted(reg["analysis"], key=lambda r: (first.index(r["id"]) if r["id"] in first else len(first), r["id"]))
    out = [f"# {reg['control']['deal']} — analysis", "",
           f"_Generated from register revision {reg['revision']}. Do not edit this file; changes go through the register._", ""]
    for r in rows:
        out += [f"## {r['title'] or r['id']} ({r['id']})", "", r["text"].strip(), ""]
    return "\n".join(out)


# ---------- changes ----------

def next_id(rows, prefix):
    nums = [int(r["id"].split("-")[1]) for r in rows if re.fullmatch(rf"{prefix}-\d+", r["id"])]
    return f"{prefix}-{max(nums, default=0) + 1:03d}"


def apply_change(reg, ch):
    sheet = ch.get("sheet")
    if sheet == "control":
        for k, v in ch.get("set", {}).items():
            if k not in CONTROL:
                raise ChangeError(f"control has no field {k!r}")
            reg["control"][k] = str(v)
        return None
    if sheet not in TABLES:
        raise ChangeError(f"unknown sheet {sheet!r}; use one of {['control'] + list(TABLES)}")
    prefix, cols = TABLES[sheet]
    rows = reg[sheet]
    fields = ch.get("add", ch.get("set", {}))
    unknown = set(fields) - set(cols)
    if unknown:
        raise ChangeError(f"{sheet} has no field(s) {sorted(unknown)}")
    if "add" in ch:
        row = {c: "" for c in cols}
        row.update(DEFAULTS.get(sheet, {}))
        row.update({k: str(v) for k, v in fields.items() if str(v) != ""})
        if sheet == "findings":
            row["id"] = next_id(rows, "T" if row["by"] == "style" else "G")
        elif sheet == "fp_map":
            row["id"] = f"{row['version']}/{row['section']}"
        elif sheet == "analysis":
            if not row["id"]:
                raise ChangeError("analysis rows need an id such as timeline, key-figures, strategy or R-001")
        elif row["id"]:
            raise ChangeError("ids are assigned by the register; leave id empty when adding")
        else:
            row["id"] = next_id(rows, prefix)
        rows[:] = [r for r in rows if r["id"] != row["id"]] + [row]
        return row["id"]
    if "update" in ch:
        target = ch["update"]
        for r in rows:
            if r["id"] == target:
                r.update({k: str(v) for k, v in fields.items() if k != "id"})
                return target
        if sheet == "analysis":
            row = {c: "" for c in cols}
            row.update({k: str(v) for k, v in fields.items()}, id=target)
            rows.append(row)
            return target
        raise ChangeError(f"{target} not found in {sheet}")
    raise ChangeError("each change needs 'add', 'update' (with 'set') or, for control, 'set'")


def apply(folder, changes):
    reg = load(folder)
    if any(e.get("op_id") == changes.get("op_id") for e in reg["log"]):
        write_views(folder, reg)  # repairs views an interrupted run may have left stale
        return {"status": "already-applied", "revision": reg["revision"]}
    if changes.get("base_revision") != reg["revision"]:
        raise ChangeError(f"stale: change set is based on revision {changes.get('base_revision')}, "
                          f"the register is at {reg['revision']}; re-read with summary and retry")
    if not changes.get("op_id"):
        raise ChangeError("op_id is required so that a retry cannot apply the same change twice")
    before = {(p[1], p[2]) for p in problems(reg) if p[0] == "error"}
    new = copy.deepcopy(reg)
    touched = [apply_change(new, ch) for ch in changes.get("changes", [])]
    introduced = [p for p in problems(new) if p[0] == "error" and (p[1], p[2]) not in before]
    rank = {"low": 0, "medium": 1, "high": 2}
    old = {r["id"]: r for r in reg["risks"]}
    for r in new["risks"]:
        o = old.get(r["id"])
        if (o and rank.get(r["rating"], -1) < rank.get(o["rating"], -1)
                and r["officer_decision"] == o["officer_decision"]):
            introduced.append(("error", "officer-decision", r["id"],
                               f"downgrading {o['rating']} to {r['rating'] or 'unrated'} needs the officer's "
                               "decision in officer_decision"))
    if introduced:
        raise ChangeError("rejected, nothing saved:\n" + "\n".join(f"  {p[2]}: {p[3]}" for p in introduced))
    notes = []
    c = new["control"]
    if c["status"] == "ready" and reg["control"]["status"] != "ready":
        if open_checks(new):
            raise ChangeError("cannot record ready, nothing saved: " + "; ".join(open_checks(new)))
        c["ready_for"] = f"{c['word']} at register revision {new['revision'] + 1}"
        c["ready_by"] = c["ready_by"] or changes.get("actor", "")
    elif c["status"] == "ready" and open_checks(new):
        c.update(status="draft", ready_for="", ready_by="")
        notes.append("readiness withdrawn: " + "; ".join(open_checks(new)))
    new["revision"] += 1
    new["control"]["updated"] = now()
    new["log"].append({"at": now(), "revision": new["revision"], "actor": changes.get("actor", ""),
                       "op_id": changes["op_id"], "summary": changes.get("summary", ""),
                       "next_step": changes.get("next_step", "")})
    save(folder, new)
    return {"status": "applied", "revision": new["revision"], "ids": [t for t in touched if t],
            "warnings": notes + [f"{p[2]}: {p[3]}" for p in problems(new) if p[0] == "warning"]}


# ---------- rules ----------

def gates(reg):
    """Reasons the FP cannot be called Ready, apart from rule errors and the Word check."""
    out = []
    blockers = [o["id"] for o in reg["open_items"] if o["criticality"] == "blocker" and o["status"] != "closed"]
    blockers += [f["id"] for f in reg["findings"] if f["priority"] == "blocker" and f["status"] == "open"]
    if blockers:
        out.append("open blockers: " + ", ".join(blockers))
    pending = [s["id"] for s in reg["sources"] if s["impact"] == "pending"]
    if pending:
        out.append("source impact not assessed: " + ", ".join(pending))
    recheck = [r["id"] for r in reg["risks"] if r["status"] == "recheck"]
    if recheck:
        out.append("risks to recheck: " + ", ".join(recheck))
    return out


def problems(reg, today=None):
    """(severity, rule, item, detail) tuples; errors block a change, warnings do not."""
    out = []
    err = lambda rule, item, detail: out.append(("error", rule, item, detail))  # noqa: E731
    warn = lambda rule, item, detail: out.append(("warning", rule, item, detail))  # noqa: E731
    for name in TABLES:
        seen = set()
        for r in reg[name]:
            if r["id"] in seen:
                err("unique-id", r["id"], f"duplicate id in {name}")
            seen.add(r["id"])
            for (table, column), allowed in ALLOWED.items():
                if table == name and r.get(column) and r[column] not in allowed:
                    err("allowed-value", r["id"], f"{column}={r[column]!r}; use one of {sorted(allowed)}")
    status = reg["control"].get("status")
    if status and status not in ALLOWED[("control", "status")]:
        err("allowed-value", "control", f"status={status!r}")
    risks = {r["id"]: r for r in reg["risks"]}
    verified = {m["risk"] for m in reg["mitigants"] if m["verified"] == "yes"}
    for r in reg["risks"]:
        if not r["raised_by"]:
            err("raised-by", r["id"], "record who raised this risk")
        if r["rating"] == "high" and r["destination"] == "background" and not r["officer_decision"]:
            err("officer-decision", r["id"], "a high-rated risk moves to background only with the officer's decision")
        if r["destination"] and not r["reason"]:
            warn("destination-reason", r["id"], "give a reason for the destination")
    for m in reg["mitigants"]:
        if m["risk"] not in risks:
            err("link", m["id"], f"mitigant points to unknown risk {m['risk']!r}")
        if not m["raised_by"]:
            err("raised-by", m["id"], "record who raised this mitigant")
        if m["verified"] == "yes" and not m["source"]:
            err("evidence", m["id"], "a verified mitigant needs a source")
    for o in reg["open_items"]:
        if o["link"].startswith("R-") and o["link"] not in risks:
            err("link", o["id"], f"open item points to unknown risk {o['link']!r}")
        if not o["raised_by"]:
            err("raised-by", o["id"], "record who raised this item")
        if o["status"] in ("answered", "closed") and not o["answer_source"]:
            err("evidence", o["id"], "an answered or closed item needs an answer source")
        r = risks.get(o["link"])
        if (o["criticality"] == "later" and r and r["destination"] == "main" and r["id"] not in verified
                and o["officer_ok"] != "yes"):
            err("later-diligence", o["id"], f"{r['id']} is in the main FP without a verified mitigant; "
                                            "'later' needs officer_ok=yes")
    for s in reg["sources"]:
        if s["tier"] == "A" and s["coverage"] != "read":
            warn("tier-a-read", s["id"], f"tier A source is {s['coverage'] or 'unread'}")
        if s["impact"] == "pending":
            warn("impact-pending", s["id"], "assess what this source changes")
    for r in reg["risks"]:
        if r["status"] == "recheck":
            warn("recheck", r["id"], "recheck this risk against the latest evidence")
    known = {r["id"] for name in TABLES for r in reg[name]}
    dates = {s["id"]: s["event_date"] for s in reg["sources"] if s["event_date"]}
    cutoff = ((today or datetime.date.today()) - datetime.timedelta(days=365)).isoformat()
    for f in reg["fp_map"]:
        cited = ID_RE.findall(f["ids"])
        unknown = [i for i in cited if i not in known]
        if unknown:
            warn("fp-map-link", f["id"], "cites unknown ids " + ", ".join(unknown))
        src = [dates[i] for i in cited if i in dates]
        if src and max(src) < cutoff:
            warn("stale-sources", f["id"], "every cited source is more than 12 months old")
    return out


def open_checks(reg, word=None):
    reasons = [f"{n} rule errors" for n in [sum(p[0] == "error" for p in problems(reg))] if n] + gates(reg)
    if word and sha256(word) != reg["control"]["word_sha256"]:
        reasons.append("the Word file changed since it was last recorded")
    return reasons


# ---------- views for the assistant ----------

def short(text, n=90):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1] + "…"


def summary(reg, word=None):
    c = reg["control"]
    changed = bool(word and c["word"] and sha256(word) != c["word_sha256"])
    lines = [f"{c['deal']} · register revision {reg['revision']}"]
    if c["status"] == "ready":
        lines.append(f"Status: ready ({c['ready_for']}, recorded by {c['ready_by'] or 'unknown'})"
                     + (" — the Word file changed since readiness was recorded" if changed else ""))
    else:
        lines.append(f"Status: {c['status'] or 'draft'}")
    if c["word"]:
        lines.append(f"Word: {c['word']}" + (" (changed since recorded — inspect it first)" if changed else ""))
    if reg["log"] and reg["log"][-1]["next_step"]:
        lines.append(f"Next: {reg['log'][-1]['next_step']}")
    src = reg["sources"]
    tier_a = [s for s in src if s["tier"] == "A"]
    lines.append(f"Sources: {len(src)} · tier A read {sum(s['coverage'] == 'read' for s in tier_a)}/{len(tier_a)}"
                 f" · impact pending {sum(s['impact'] == 'pending' for s in src)}")
    dest = Counter(r["destination"] or "unplaced" for r in reg["risks"] if r["status"] != "closed")
    lines.append(f"Risks: {sum(dest.values())} open (" + ", ".join(f"{k} {v}" for k, v in sorted(dest.items()))
                 + f") · recheck {sum(r['status'] == 'recheck' for r in reg['risks'])}")
    opened = [o for o in reg["open_items"] if o["status"] != "closed"]
    state = Counter(o["status"] or "open" for o in opened)
    crit = Counter(o["criticality"] or "unrated" for o in opened)
    lines.append(f"Open items: {len(opened)} not closed (" + ", ".join(f"{k} {v}" for k, v in sorted(state.items()))
                 + "; " + ", ".join(f"{k} {v}" for k, v in sorted(crit.items())) + ")")
    lines.append(f"Findings: {sum(f['status'] == 'open' for f in reg['findings'])} open")
    reasons = open_checks(reg, word)
    lines.append("Register checks: passed" if not reasons else "Register checks: not passed — " + "; ".join(reasons))
    rank = {"blocker": 0, "material": 1}
    top = sorted(opened, key=lambda o: (rank.get(o["criticality"], 2), o["due"] or "9999"))[:5]
    if top:
        lines.append("Top open items:")
        lines += [f"  {o['id']} [{o['criticality'] or '-'}] {o['addressee'] or '-'}: {short(o['text'])}"
                  + (f" ({o['link']})" if o["link"] else "") + (f" due {o['due']}" if o["due"] else "")
                  + (f" — {o['status']}" if o["status"] != "open" else "") for o in top]
    probs = problems(reg)
    lines.append(f"Checks: {sum(p[0] == 'error' for p in probs)} errors, {sum(p[0] == 'warning' for p in probs)} warnings")
    lines += [f"  {p[0].upper()} {p[2]}: {short(p[3])}" for p in probs[:5]]
    if reg["log"]:
        lines.append("Recent:")
        lines += [f"  r{e['revision']} {e['at'][:10]} {e['actor']}: {short(e['summary'])}" for e in reg["log"][-3:]]
    return "\n".join(lines)


def show(reg, ids):
    rows = {r["id"]: (name, r) for name in TABLES for r in reg[name]}
    out = []
    for i in ids:
        if i not in rows:
            out.append(f"{i}: not found")
            continue
        name, r = rows[i]
        out.append(f"{i} ({name})")
        out += [f"  {k}: {v}" for k, v in r.items() if v and k != "id"]
        if name == "risks":
            out += [f"  mitigant {m['id']}: {m['text']} [{m['type']}, verified {m['verified'] or '-'}]"
                    for m in reg["mitigants"] if m["risk"] == i]
            out += [f"  open item {o['id']}: {o['text']} [{o['status']}]" for o in reg["open_items"] if o["link"] == i]
            out += [f"  analysis: {a['text']}" for a in reg["analysis"] if a["id"] == i and name != "analysis"]
    return "\n".join(out)


def lists(reg):
    opened = [o for o in reg["open_items"] if o["status"] != "closed"]
    client = [o for o in opened if any(w in o["addressee"].lower() for w in CLIENT)]
    internal = [o for o in opened if o not in client]
    state = {"promised": " — promised, awaiting evidence", "answered": " — answered, awaiting assessment"}
    item = lambda o: (f"- {o['id']} [{o['criticality'] or '-'}] {o['text']}"  # noqa: E731
                      + (f" ({o['link']})" if o["link"] else "") + state.get(o["status"], "")
                      + (f" — due {o['due']}" if o["due"] else ""))
    conditions = [m for m in reg["mitigants"] if m["type"] == "proposed-condition" and m["status"] != "closed"]
    out = ["## Client requests", ""] + ([item(o) for o in client] or ["- none"])
    out += ["", "## Internal open points", ""] + ([item(o) for o in internal] or ["- none"])
    out += ["", "## Proposed conditions", ""] + ([f"- {m['id']} ({m['risk']}) {m['text']}" for m in conditions]
                                                  or ["- none"])
    return "\n".join(out)


# ---------- self-test ----------

def selftest():
    with tempfile.TemporaryDirectory() as d:
        save(d, new_register("TestDeal"))
        r = apply(d, {"base_revision": 0, "op_id": "t1", "actor": "selftest", "summary": "first", "changes": [
            {"sheet": "sources", "add": {"title": "AR 2025", "tier": "A", "coverage": "read", "impact": "assessed"}},
            {"sheet": "risks", "add": {"title": "FX mismatch", "raised_by": "E&S call", "rating": "high",
                                       "destination": "main", "reason": "decision-relevant", "status": "open"}},
            {"sheet": "open_items", "add": {"text": "Revenue split by currency", "link": "R-001",
                                            "addressee": "client", "raised_by": "officer", "criticality": "blocker",
                                            "status": "open"}}]})
        assert r["status"] == "applied" and r["ids"] == ["S-001", "R-001", "O-001"], r
        assert apply(d, {"base_revision": 0, "op_id": "t1"})["status"] == "already-applied"
        for bad in ({"base_revision": 0, "op_id": "t2", "changes": []},
                    {"base_revision": 1, "op_id": "t3", "changes": [
                        {"sheet": "mitigants", "add": {"risk": "R-001", "verified": "yes", "raised_by": "x"}}]}):
            try:
                apply(d, bad)
                raise AssertionError("change should have been rejected")
            except ChangeError:
                pass
        reg = load(d)
        assert "Register checks: not passed" in summary(reg) and "O-001" in lists(reg)
        with zipfile.ZipFile(Path(d) / "register.xlsx") as z:
            assert z.testzip() is None
    return f"PASS register selftest (Python {sys.version.split()[0]})"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("folder")
    p.add_argument("--deal", required=True)
    for name in ("summary", "check"):
        p = sub.add_parser(name)
        p.add_argument("folder")
        p.add_argument("--word")
    p = sub.add_parser("show")
    p.add_argument("folder")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("apply")
    p.add_argument("folder")
    p.add_argument("changes")
    p = sub.add_parser("lists")
    p.add_argument("folder")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "init":
            if (Path(args.folder) / "register.json").exists():
                raise ChangeError("register.json already exists here")
            Path(args.folder).mkdir(parents=True, exist_ok=True)
            save(args.folder, new_register(args.deal))
            print(f"created register for {args.deal} at revision 0")
        elif args.cmd == "summary":
            print(summary(load(args.folder), args.word))
        elif args.cmd == "show":
            print(show(load(args.folder), args.ids))
        elif args.cmd == "apply":
            result = apply(args.folder, json.loads(Path(args.changes).read_text(encoding="utf-8")))
            print(json.dumps(result, indent=1))
        elif args.cmd == "lists":
            print(lists(load(args.folder)))
        elif args.cmd == "check":
            reg = load(args.folder)
            probs = problems(reg)
            print("\n".join(f"{p[0].upper()} {p[1]} {p[2]}: {p[3]}" for p in probs) or "no problems")
            reasons = open_checks(reg, args.word)
            print("Register checks: passed" if not reasons else "Register checks: not passed — " + "; ".join(reasons))
            return 1 if any(p[0] == "error" for p in probs) else 0
        else:
            print(selftest())
    except (ChangeError, json.JSONDecodeError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [ ] **Step 4: Run the tests and the self-test on Python 3.9**

Run: `uv run pytest tests/test_register.py -q`
Expected: `24 passed`

Run: `uv run --no-project --python 3.9 python tools/register.py selftest`
Expected: `PASS register selftest (Python 3.9.x)`

- [ ] **Step 5: Commit**

```bash
git add tools/register.py tests/test_register.py
git commit -m "Add deal register that keeps unfinished work visible; readiness is a recorded decision"
```

---

### Task 4: Financial table tool (`tools/fin_table.py`)

**Files:**
- Create: `tools/fin_table.py`
- Test: `tests/test_fin_table.py`

**Interfaces:**
- Consumes: `register.write_xlsx` (self-test only; both scripts ship together).
- Produces: `read_sheet(path, name) -> (cells, formula_cells)`, `build_table(spread, mapping) -> dict` (keys `unit, periods, rows`; a row has `label, format, values` and `source` cell references or `formula`), `compute(expr, values)`, `markdown(table) -> str`, `TableError`, `selftest()`.
- Mapping keys: `sheet, label_column, header_row, unit, periods, rows`, optional `expect` (cell → required text, identifying the export) and `trust_formula_values`.
- Command line: `fin_table.py SPREAD.xlsx MAPPING.json [--json OUT]`, `fin_table.py selftest`.

- [ ] **Step 1: Write the failing tests** — `tests/test_fin_table.py`

````python
import json

import openpyxl  # dev-only: writes a realistic export with shared strings, like Excel does
import pytest

import fin_table


@pytest.fixture
def spread(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Spread"
    ws.append(["EUR m", 2023, 2024, 2025])          # numeric year headers, as many exports use
    ws.append(["Total revenue", 90, 100, 120])
    ws.append(["EBITDA", 15, 20, 18])
    ws.append(["Net debt", 40, 45, None])            # missing value
    ws.append(["Comment", "n/a", "x", "y"])          # text in a value row
    path = tmp_path / "spread.xlsx"
    wb.save(path)
    return path


def mapping(**rows):
    base = {"sheet": "Spread", "label_column": "A", "header_row": 1, "unit": "EUR m",
            "periods": ["2024", "2025"], "rows": [
                {"label": "Revenue", "source": "total revenue"},
                {"label": "EBITDA", "source": "EBITDA"},
                {"label": "EBITDA margin", "formula": "{EBITDA} / {Revenue}", "format": "pct"},
                {"label": "Revenue growth", "formula": "growth({Revenue})", "format": "pct"},
                {"label": "Net debt", "source": "Net debt"},
                {"label": "Net debt / EBITDA", "formula": "{Net debt} / {EBITDA}", "format": "x"}]}
    base.update(rows)
    return base


def test_table_values_sources_and_markdown(spread):
    t = fin_table.build_table(spread, mapping())
    rev = t["rows"][0]
    assert rev["values"] == [100.0, 120.0] and rev["source"] == ["Spread!C2", "Spread!D2"]
    md = fin_table.markdown(t)
    assert "| EBITDA margin | 20.0% | 15.0% |" in md
    assert "| Revenue growth | n/a | 20.0% |" in md       # first period has no prior in the table
    assert "| Net debt / EBITDA | 2.2x | n/a |" in md      # missing input stays n/a, never 0


@pytest.mark.parametrize("change, message", [
    ({"periods": ["2024", "2030"]}, "period '2030'"),
    ({"rows": [{"label": "X", "source": "Turnover"}]}, "row 'Turnover'"),
    ({"rows": [{"label": "X", "formula": "{A} * {B}"}]}, "unsupported formula"),
    ({"rows": [{"label": "X", "formula": "{Revenue} / {EBITDA}"}]}, "not an earlier row"),
    ({"rows": [{"label": "X", "source": "Comment"}]}, "not numbers"),
    ({"sheet": "Other"}, "no sheet"),
])
def test_refuses_instead_of_guessing(spread, change, message):
    with pytest.raises(fin_table.TableError, match=message):
        fin_table.build_table(spread, mapping(**change))


def test_growth_on_negative_base_is_not_reported():
    assert fin_table.compute("growth({A})", {"A": [-10.0, 5.0, 10.0]}) == [None, None, 1.0]


def test_cli_writes_json_and_selftest(spread, tmp_path, capsys):
    m = tmp_path / "mapping.json"
    m.write_text(json.dumps(mapping()))
    out = tmp_path / "table.json"
    assert fin_table.main([str(spread), str(m), "--json", str(out)]) == 0
    assert json.loads(out.read_text())["rows"][2]["formula"] == "{EBITDA} / {Revenue}"
    assert fin_table.main(["selftest"]) == 0
    assert "PASS" in capsys.readouterr().out


def test_ambiguous_rows_and_periods_are_refused(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Spread"
    ws.append(["EUR m", 2024, 2025, 2025])
    ws.append(["EBITDA", 20, 18, 17])
    ws.append(["EBITDA", 1, 2, 3])
    path = tmp_path / "dup.xlsx"
    wb.save(path)
    m = {"sheet": "Spread", "label_column": "A", "header_row": 1, "periods": ["2024"],
         "rows": [{"label": "EBITDA", "source": "EBITDA"}]}
    with pytest.raises(fin_table.TableError, match="ambiguous.*row 'EBITDA'"):
        fin_table.build_table(path, m)
    with pytest.raises(fin_table.TableError, match="ambiguous.*period '2025'"):
        fin_table.build_table(path, dict(m, periods=["2025"], rows=[]))


def test_formula_cells_need_an_explicitly_trusted_recalculated_export(tmp_path):
    from register import write_xlsx
    path = tmp_path / "f.xlsx"
    write_xlsx(path, [("Spread", ["Line", "2025"], [["Revenue", 120], ["Gross profit", 30]])])
    fin_table_inject_formula(path, "B3", "B2*0.25")
    m = {"sheet": "Spread", "label_column": "A", "header_row": 1, "periods": ["2025"],
         "rows": [{"label": "Gross profit", "source": "Gross profit"}]}
    with pytest.raises(fin_table.TableError, match="formulas"):
        fin_table.build_table(path, m)
    assert fin_table.build_table(path, dict(m, trust_formula_values=True))["rows"][0]["values"] == [30.0]


def test_expected_cells_identify_the_export(spread):
    m = mapping(expect={"A1": "EUR m", "A2": "Total revenue"})
    assert fin_table.build_table(spread, m)["rows"][0]["values"] == [100.0, 120.0]
    with pytest.raises(fin_table.TableError, match="not the expected export"):
        fin_table.build_table(spread, mapping(expect={"A1": "USD m"}))


def fin_table_inject_formula(path, ref, formula):
    import zipfile
    with zipfile.ZipFile(path) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    sheet = parts["xl/worksheets/sheet1.xml"].decode()
    head = f'<c r="{ref}" s="2">'
    assert head in sheet
    parts["xl/worksheets/sheet1.xml"] = sheet.replace(head, head + f"<f>{formula}</f>").encode()
    with zipfile.ZipFile(path, "w") as z:
        for n, d in parts.items():
            z.writestr(n, d)
````

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_fin_table.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'fin_table'`

- [ ] **Step 3: Create `tools/fin_table.py`**

````python
#!/usr/bin/env python3
"""Turn the spreading export into the FP's financial table, with traceable sources.

  fin_table.py SPREAD.xlsx MAPPING.json [--json OUT.json]
  fin_table.py selftest

Prints a Markdown table for the FP text draft. Every value is either copied from a named
cell or computed by one of four formulas: {A} / {B}, {A} - {B}, {A} + {B}, growth({A}).
Use an identified export of the spreading tool: "expect" names cells that must hold given
text (entity, unit, period headers). Labels or periods that appear twice are refused.
Cells holding formulas are refused unless "trust_formula_values" is true, meaning the
export was recalculated and saved by the spreading tool.
Standard library only. The mapping is set up once per spreading-export layout:

  {"sheet": "Spread", "label_column": "A", "header_row": 1, "unit": "EUR m",
   "expect": {"A1": "EUR m", "B1": "FY2024"},
   "periods": ["FY2024", "FY2025"],
   "rows": [{"label": "Revenue", "source": "Total revenue"},
            {"label": "EBITDA margin", "formula": "{EBITDA} / {Revenue}", "format": "pct"}]}
"""
import argparse
import json
import re
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
FORMULA = re.compile(r"^\s*(?:growth\(\{(?P<g>[^}]+)\}\)|\{(?P<a>[^}]+)\}\s*(?P<op>[-+/])\s*\{(?P<b>[^}]+)\})\s*$")


class TableError(Exception):
    """The table cannot be built as specified; nothing is guessed."""


def norm(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def read_sheet(path, name):
    """({"B7": value}, {cells holding formulas}) for one worksheet; numbers as float, text as str."""
    with zipfile.ZipFile(path) as z:
        sheets = {s.get("name"): s.get(REL + "id") for s in ET.fromstring(z.read("xl/workbook.xml")).iter(MAIN + "sheet")}
        if name not in sheets:
            raise TableError(f"no sheet {name!r}; the workbook has {sorted(sheets)}")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels if r.get("Id") == sheets[name])
        part = target.lstrip("/") if target.startswith("/") else "xl/" + target
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared = ["".join(t.text or "" for t in si.iter(MAIN + "t"))
                      for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(MAIN + "si")]
        cells, formulas = {}, set()
        for c in ET.fromstring(z.read(part)).iter(MAIN + "c"):
            if c.find(MAIN + "f") is not None:
                formulas.add(c.get("r"))
            kind, v = c.get("t"), c.find(MAIN + "v")
            if kind == "s":
                value = shared[int(v.text)]
            elif kind == "inlineStr":
                value = "".join(t.text or "" for t in c.iter(MAIN + "t"))
            elif kind in ("str", "e"):
                value = v.text if v is not None else ""
            elif kind == "b":
                value = v is not None and v.text == "1"
            else:
                value = float(v.text) if v is not None and v.text else None
            cells[c.get("r")] = value
    return cells, formulas


def split_ref(ref):
    m = re.fullmatch(r"([A-Z]+)(\d+)", ref)
    return m.group(1), int(m.group(2))


def compute(expr, values):
    m = FORMULA.match(expr)
    if not m:
        raise TableError(f"unsupported formula {expr!r}; use {{A}} / {{B}}, {{A}} - {{B}}, {{A}} + {{B}} or growth({{A}})")
    for name in filter(None, (m["g"], m["a"], m["b"])):
        if name not in values:
            raise TableError(f"formula {expr!r} uses {name!r}, which is not an earlier row")
    if m["g"]:
        a = values[m["g"]]
        return [None] + [(cur - prev) / prev if prev and prev > 0 and cur is not None else None
                         for prev, cur in zip(a, a[1:])]
    out = []
    for x, y in zip(values[m["a"]], values[m["b"]]):
        if x is None or y is None or (m["op"] == "/" and not y):
            out.append(None)
        else:
            out.append(x / y if m["op"] == "/" else x - y if m["op"] == "-" else x + y)
    return out


def build_table(spread, mapping):
    sheet = mapping["sheet"]
    cells, formulas = read_sheet(spread, sheet)
    wrong = [f"{ref} holds {cells.get(ref)!r}, expected {want!r}" for ref, want in mapping.get("expect", {}).items()
             if norm(cells.get(ref, "")) != norm(want)]
    if wrong:
        raise TableError("this is not the expected export: " + "; ".join(wrong))
    label_col, header_row = mapping["label_column"].upper(), int(mapping["header_row"])
    label_rows, header_cols = {}, {}
    for ref, value in cells.items():
        col, row = split_ref(ref)
        if col == label_col and isinstance(value, str) and value.strip():
            label_rows.setdefault(norm(value), []).append(row)
        if row == header_row and value not in (None, ""):
            header_cols.setdefault(norm(value), []).append(col)
    periods = mapping["periods"]
    sources = [r["source"] for r in mapping["rows"] if "source" in r]
    missing = [f"period {p!r}" for p in periods if norm(p) not in header_cols]
    missing += [f"row {s!r}" for s in sources if norm(s) not in label_rows]
    if missing:
        raise TableError("not found in the spreading export: " + ", ".join(missing))
    twice = [f"period {p!r}" for p in periods if len(header_cols[norm(p)]) > 1]
    twice += [f"row {s!r}" for s in sources if len(label_rows[norm(s)]) > 1]
    if twice:
        raise TableError("ambiguous in the spreading export (appears more than once): " + ", ".join(twice))
    labels = {k: v[0] for k, v in label_rows.items()}
    headers = {k: v[0] for k, v in header_cols.items()}
    values, rows = {}, []
    for spec in mapping["rows"]:
        row = {"label": spec["label"], "format": spec.get("format", "num")}
        if "source" in spec:
            r = labels[norm(spec["source"])]
            refs = [f"{headers[norm(p)]}{r}" for p in periods]
            vals = [cells.get(ref) for ref in refs]
            wrong = [ref for ref, v in zip(refs, vals) if v is not None and not isinstance(v, float)]
            if wrong:
                raise TableError(f"{spec['label']}: cells {wrong} are not numbers")
            calc = [ref for ref in refs if ref in formulas]
            if calc and not mapping.get("trust_formula_values"):
                raise TableError(f"{spec['label']}: cells {calc} hold formulas; use a values-only export, or set "
                                 "trust_formula_values when the spreading tool recalculated and saved this export")
            if any(ref in formulas and v is None for ref, v in zip(refs, vals)):
                raise TableError(f"{spec['label']}: a formula cell has no stored value; recalculate and save the export")
            row.update(values=vals, source=[f"{sheet}!{ref}" for ref in refs])
        else:
            row.update(values=compute(spec["formula"], values), formula=spec["formula"])
        values[spec["label"]] = row["values"]
        rows.append(row)
    return {"unit": mapping.get("unit", ""), "periods": periods, "rows": rows}


def fmt(value, kind):
    if value is None:
        return "n/a"
    if kind == "pct":
        return f"{value * 100:.1f}%"
    if kind == "x":
        return f"{value:.1f}x"
    return f"{value:,.1f}"


def markdown(table):
    lines = ["| " + " | ".join([table["unit"]] + table["periods"]) + " |",
             "|---|" + "---:|" * len(table["periods"])]
    lines += ["| " + " | ".join([r["label"]] + [fmt(v, r["format"]) for v in r["values"]]) + " |"
              for r in table["rows"]]
    return "\n".join(lines)


def selftest():
    from register import write_xlsx  # shipped next to this script in every skill that uses it
    with tempfile.TemporaryDirectory() as d:
        spread = Path(d) / "spread.xlsx"
        write_xlsx(spread, [("Spread", ["Line", "FY2024", "FY2025"],
                             [["Total revenue", 100, 120], ["EBITDA", 20, 18]])])
        table = build_table(spread, {"sheet": "Spread", "label_column": "A", "header_row": 1, "unit": "EUR m",
                                     "periods": ["FY2024", "FY2025"], "rows": [
                                         {"label": "Revenue", "source": "Total revenue"},
                                         {"label": "EBITDA", "source": "EBITDA"},
                                         {"label": "EBITDA margin", "formula": "{EBITDA} / {Revenue}", "format": "pct"},
                                         {"label": "Revenue growth", "formula": "growth({Revenue})", "format": "pct"}]})
        md = markdown(table)
        assert "| EBITDA margin | 20.0% | 15.0% |" in md and "| Revenue growth | n/a | 20.0% |" in md, md
    return f"PASS fin_table selftest (Python {sys.version.split()[0]})"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spread", help="spreading export (.xlsx), or 'selftest'")
    ap.add_argument("mapping", nargs="?")
    ap.add_argument("--json", help="also write the table with its sources to this file")
    args = ap.parse_args(argv)
    try:
        if args.spread == "selftest":
            print(selftest())
            return 0
        if not args.mapping:
            raise TableError("give the mapping file after the spreading export")
        table = build_table(args.spread, json.loads(Path(args.mapping).read_text(encoding="utf-8")))
        if args.json:
            Path(args.json).write_text(json.dumps(table, indent=1), encoding="utf-8")
        print(markdown(table))
    except (TableError, KeyError, zipfile.BadZipFile, ET.ParseError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [ ] **Step 4: Run all tests and the self-test on Python 3.9**

Run: `uv run pytest -q`
Expected: `55 passed`

Run: `cd tools && uv run --no-project --python 3.9 python fin_table.py selftest && cd ..`
Expected: `PASS fin_table selftest (Python 3.9.x)`

- [ ] **Step 5: Commit**

```bash
git add tools/fin_table.py tests/test_fin_table.py
git commit -m "Add financial table tool for identified spreading exports"
```

---

### Task 5: Skills — rename, non-overlapping triggers, tool links, new workflow contract, version 0.3.0

**Files:**
- Rename: `skills/meeting-evidence-review/` → `skills/deal-updates/`
- Modify: every `skills/*/SKILL.md` (frontmatter, one `Tools:` line, cross-references)
- Modify (replace): `shared/workflow-contract.md`
- Modify: `.claude-plugin/plugin.json` (version); links in `evaluations/deal-updates-case.md`, `evaluations/transcript-case.md` and `evaluations/transcript-review.md`
- Generated by `package.py`: `skills/*/scripts/*.py` and the skills' copies of `references/workflow-contract.md`

- [ ] **Step 1: Rename the skill folder**

```bash
git mv skills/meeting-evidence-review skills/deal-updates
```

- [ ] **Step 2: Set names, descriptions, cross-references and tool links**

```bash
python3 - <<'EOF'
import re, pathlib
DESC = {
 "deal-analyst": "Build the company, transaction and due-diligence analysis behind a financing proposal (FP). Use to analyse a deal, assess what a new document means for the case, answer \"what's open?\", integrate specialist views, prepare a specified annex or find support for a Credit question. For emails, meeting transcripts or call notes use deal-updates; for reading a full annual report use annual-report-review; for explaining margins or cash use financial-performance-analysis; for repayment and covenants use repayment-and-structure.",
 "annual-report-review": "Read annual accounts and all their notes completely for a financing proposal, keeping page-referenced findings and a record of what was read. Use for a full annual-report or audited-accounts review, note disclosures, reporting-scope checks and unreadable pages. For explaining movements across periods use financial-performance-analysis; for the repayment conclusion use repayment-and-structure.",
 "financial-performance-analysis": "Explain financial movements, earnings quality and cash conversion for a financing proposal. Use for revenue or margin changes, profit versus cash, working capital, adjustments, financial trends and the FP's financial table. For complete report reading use annual-report-review; for debt service and financing terms use repayment-and-structure.",
 "repayment-and-structure": "Assess repayment capacity and financing structure for a corporate financing proposal. Use for debt service, liquidity runway, maturity or refinancing risk, covenant headroom, sources and uses, guarantees, security and proposed conditions. For historical drivers use financial-performance-analysis; regulated financial institutions and other materially different sectors need specialist institutional methods.",
 "fp-lead": "Draft and revise financing proposals (FPs) and Credit replies. Use to start or continue an FP, set the brief, choose the approval case, write or revise sections, build the Word version, integrate review findings and the officer's Word edits, assess readiness or record submission. For detailed analysis use deal-analyst and the finance skills; for challenge use investment-grill; for house style use fp-template-style-reviewer.",
 "investment-grill": "Challenge the evidence and reasoning in a financing proposal or Credit reply. Use to grill an FP, test the financing thesis, interview the officer about the case, recheck findings or arbitrate a disputed finding in a fresh task. For wording and layout use fp-template-style-reviewer.",
 "fp-template-style-reviewer": "Set up template and house-style rules, or polish and check the presentation of a settled financing proposal. Use for template preflight, style editing, template compliance and Word layout checks. Escalates changes in meaning; for substantive challenge use investment-grill, for new content fp-lead.",
 "deal-updates": "Review recent deal emails, meeting transcripts, call notes, Word comments and informal guidance for a financing proposal. Use to check the latest correspondence, process a Teams call or specialist interview, record what someone said, reconcile conflicting updates or interpret tentative feedback. Records who said what and proposes updates to evidence, open items and the deal strategy. For reading documents such as annual reports or contracts use deal-analyst or annual-report-review.",
}
TOOLS = {
 "fp-lead": ["register.py", "fp_docx.py", "fin_table.py"],
 "fp-template-style-reviewer": ["register.py", "fp_docx.py"],
 "investment-grill": ["register.py", "fp_docx.py"],
 "deal-updates": ["register.py", "fp_docx.py"],
 "financial-performance-analysis": ["register.py", "fin_table.py"],
}
for skill, desc in DESC.items():
    p = pathlib.Path("skills", skill, "SKILL.md")
    t = p.read_text()
    t = re.sub(r"^name: .*$", f"name: {skill}", t, count=1, flags=re.M)
    t = re.sub(r"^description: .*$", "description: " + desc.replace("\\", "\\\\"), t, count=1, flags=re.M)
    t = t.replace("`meeting-evidence-review` (Deal Updates and Guidance)", "`deal-updates`")
    t = t.replace("**meeting-evidence-review** (Deal Updates and Guidance)", "**deal-updates**")
    t = t.replace(" The existing skill identifier is retained for continuity.", "")
    tools = TOOLS.get(skill, ["register.py"])
    line = "Tools: " + ", ".join(f"[{x}](scripts/{x})" for x in tools) + ". The workflow contract says how to run them."
    t = re.sub(r"(^Apply \[operating-rules\.md\].*?$)", r"\1\n\n" + line, t, count=1, flags=re.M | re.S)
    p.write_text(t)
    print(skill, len(desc), "chars")
EOF
```

Expected: eight lines `<skill> <n> chars`, every n ≤ 1,024.

Run: `grep -rn "meeting-evidence-review" skills/ || echo "none"`
Expected: `none`

- [ ] **Step 3: Replace `shared/workflow-contract.md`**

````markdown
# FP Assistant workflow contract

Read this contract and the operating rules once per task. Load only what the request needs: a status question does not need the whole report or every skill.

## Files and tools

Each skill carries its scripts in `scripts/`. They need Python 3.9 or later and nothing else. They work on local files:

1. Bring the deal's `FP assistant` folder (OneDrive or SharePoint) into the working folder, plus any other file the step needs.
2. Run the script with `python3` (or `python` if that is the available command).
3. Save every file the script created or changed back to the same deal folder. Do not edit those files in any other way.

| Need | Command |
|---|---|
| Start of every task | `python3 scripts/register.py summary FOLDER --word CURRENT.docx` |
| New deal | `python3 scripts/register.py init FOLDER --deal KEY` |
| Look up items | `python3 scripts/register.py show FOLDER R-002 O-005` |
| Record changes | `python3 scripts/register.py apply FOLDER changes.json` |
| Client requests, internal points, proposed conditions | `python3 scripts/register.py lists FOLDER` |
| Rule check and readiness | `python3 scripts/register.py check FOLDER --word CURRENT.docx` |
| Read a Word version: text, comments, officer edits | `python3 scripts/fp_docx.py inspect FILE.docx --markdown` (or without `--markdown` for section status as JSON) |
| Write a Word version | `python3 scripts/fp_docx.py build --base BASE.docx --content TEXT.md --out NEW.docx` |
| First version from the template | add `--first --fields FIELDS.json` (cover-page labels and values) |
| Check a Word version | `python3 scripts/fp_docx.py check FILE.docx --template TEMPLATE.docx` |
| Financial table from an identified spreading export | `python3 scripts/fin_table.py SPREAD.xlsx MAPPING.json --json TABLE.json` |
| Confirm the scripts run here | `python3 scripts/<tool>.py selftest` |

**Change sets.** `apply` takes JSON: `{"base_revision": N, "op_id": "unique-name", "actor": "skill", "summary": "what changed", "next_step": "one next action, with the skill and whether it needs a new task", "changes": [...]}`. Take `base_revision` from `summary`. A change is `{"sheet": "risks", "add": {...}}`, `{"sheet": "risks", "update": "R-002", "set": {...}}` or `{"sheet": "control", "set": {...}}`. Leave ids empty when adding; the register assigns them. Sheets: control, sources, risks, mitigants, open_items, findings, analysis, fp_map. Analysis rows are narrative sections keyed by id, for example `strategy`, `timeline`, `key-figures`, `R-001` or `annual-accounts-2025`. A rejected change set saves nothing; fix what the message names and apply again. Re-sending the same `op_id` is safe and repairs the Excel and Markdown views if an earlier run was interrupted.

**Unfinished work stays visible.** New open items start as `open` and new sources as `impact: pending`. A promise to send evidence is `promised`; an answer that still needs your assessment is `answered`. Only `closed`, with an answer source, finishes an item, and only then does it leave the lists.

**Financial table.** Set up the mapping once per spreading-export layout. `expect` names cells that identify the export (entity, unit, period headers). Labels or periods that appear twice are refused. Cells that hold formulas are refused unless the export was recalculated and saved by the spreading tool (`trust_formula_values`); a values-only export avoids this. The table keeps the cell reference of every copied figure.

**Text drafts.** `build` reads Markdown: `## section-id` (or the heading text) per section, then paragraphs, `- ` bullets, `|` tables and `**bold**`. Put source tags such as `[S-012 p.45]` after claims; they are removed from Word and recorded per section. `{{keep:N}}` places the section's N-th fixed object (a template table, image or field) at that point; fixed objects are never deleted. `inspect --markdown` shows the content of kept tables inside read-only `<!-- -->` notes, which `build` ignores, so the same text can be edited and sent back.

**When a tool fails.** Stop that change, report the exact message and offer the unapplied work as a labelled proposal. Never edit Word or Excel files another way. If Python is unavailable, say so and work in proposal mode: analysis and draft text in the chat or a Markdown file, with no claim that records or Word files were updated.

## Word rounds

One officer task writes at a time. Before revising, run `inspect` on the current Word file. Sections the officer edited, commented on or tracked-changed stay exactly as they are; `build` refuses to replace them and writes your text to `NEW.proposals.md` for the officer to copy. Only untouched sections that the assistant wrote are replaced. Every round is a new file (`DEAL-FP-v04.docx`); Word's Review → Compare shows what changed. Preserving officer text does not exempt it from factual review. After `build`, record the new file and its hash in control (`word`, `word_sha256`) and its sections in `fp_map`.

## Evidence and decisions

For a material assertion retain: source identity and version; page, passage or cell; entity and reporting boundary; period or event date; currency and unit where relevant; the assertion and its support status. Distinguish reported fact, management assertion, analyst inference and calculation. A citation alone does not establish support. Calculations keep formula, inputs and their references.

Keep supporting and contrary evidence. Mitigants are existing protection, proposed condition or assumption; record evidence of implementation, applicability and timing. An answer need not resolve the issue it addresses. Only evidence or an explicit, recorded officer decision closes an issue; an officer decision does not make an unverified assertion verified.

Every new or changed source gets an impact assessment (`impact` = assessed or no-impact), even when nothing links to it yet. Pending assessments prevent Ready. Material edits and revised calculations reopen affected findings and conclusions (`status` = recheck). A newer date alone does not supersede an executed agreement or change the period of a fact.

## Completion and handoff

Return the requested result first, with evidence and only decision-relevant open points. Record what was checked, changed and left open, and one next action, through `apply`. Ask only for genuinely missing input or material judgment; routine repairs need no approval. One challenge round plus a recheck per material checkpoint is the default. FP Lead and Investment Grill use the review protocol; a skill instruction does not prove that an independent task ran.

The tools report checks; people decide readiness. `summary` and `check` say "Register checks: passed" or list what is still open. When the template, style and layout checks have also passed for the current Word file, FP Lead records readiness with the officer: set control `status` to `ready` and `ready_by` to the person deciding. The register records which Word file and revision this applies to, and refuses while checks are open. New open work withdraws it automatically, and `summary` warns when the Word file changed since. The officer can submit with recorded exceptions: record that as `submitted`, with the exceptions in the summary, never as a clean Ready result or a credit approval.
````

- [ ] **Step 4: Fix evaluation links and bump the version**

```bash
sed -i '' 's#skills/meeting-evidence-review/SKILL.md#skills/deal-updates/SKILL.md#' evaluations/deal-updates-case.md evaluations/transcript-review.md
sed -i '' 's#applicable meeting-evidence-review skill#applicable deal-updates skill#' evaluations/transcript-case.md
sed -i '' 's/"version": "0.2.0"/"version": "0.3.0"/' .claude-plugin/plugin.json
```

- [ ] **Step 5: Sync, check and build; confirm each skill has the scripts it links to**

Run: `python3 scripts/package.py && for s in skills/*/; do echo "$(basename $s): $(ls $s/scripts | tr '\n' ' ')"; done`
Expected:
- `fp-assistant-0.3.0.zip: 44 files OK` and `fp-assistant-individual-skills-0.3.0.zip: 9 files OK`;
- every skill lists `register.py`;
- fp-lead also lists `fp_docx.py` and `fin_table.py`;
- fp-template-style-reviewer, investment-grill and deal-updates also list `fp_docx.py`;
- financial-performance-analysis also lists `fin_table.py`.

- [ ] **Step 6: Run the self-tests from inside the built plugin, as Cowork will**

```bash
rm -rf /tmp/fpa-zip && mkdir /tmp/fpa-zip && unzip -q dist/fp-assistant-0.3.0.zip -d /tmp/fpa-zip
cd /tmp/fpa-zip/skills/fp-lead && for t in register fp_docx fin_table; do uv run --no-project --python 3.9 python scripts/$t.py selftest; done; cd -
```

Expected: three `PASS ... (Python 3.9.x)` lines.

- [ ] **Step 7: Run all tests, then commit**

Run: `uv run pytest -q`
Expected: `55 passed`

```bash
git add -A skills shared .claude-plugin evaluations
git commit -m "Rename deal-updates, separate skill triggers, ship tools with the skills, v0.3.0"
```

---

### Task 6: One current design

**Files:**
- Move: `docs/design-v3.md`, `docs/handover-v3.md`, `docs/research-assessment.md`, `docs/skill-review.md`, `docs/transcripts-and-strategy.md`, `docs/adversarial-review.md` → `docs/archive/`
- Create: `docs/design.md`, `docs/archive/README.md`, `evaluations/README.md`, `evaluations/results.md`
- Modify (replace): `README.md`, `INSTALL.md`, `AGENTS.md`

- [ ] **Step 1: Archive the superseded documents and repair their relative links**

```bash
mkdir -p docs/archive
for f in design-v3 handover-v3 research-assessment skill-review transcripts-and-strategy adversarial-review; do git mv docs/$f.md docs/archive/; done
sed -i '' 's#](\.\./#](../../#g' docs/archive/*.md
sed -i '' 's#\.\./\.\./skills/meeting-evidence-review/SKILL.md#../../skills/deal-updates/SKILL.md#' docs/archive/transcripts-and-strategy.md
```

- [ ] **Step 2: Create `docs/archive/README.md`**

````markdown
# Archive

Superseded documents, kept for history: design v3, the seven-skill handover, the research assessment, the skill review, the deal-updates extension and the adversarial-review note. They describe version 0.2.0, before the scripts existed and before `meeting-evidence-review` was renamed `deal-updates`.

The current design is [../design.md](../design.md).
````

- [ ] **Step 3: Create `docs/design.md`**

````markdown
# FP Assistant — design

The current design, 2 October 2026. Earlier designs and reviews are kept in [archive/](archive/) for history only.

## Purpose

Help an investment officer prepare a financing proposal (FP) that is well evidenced, tells the company's recent story, explains its figures and states the remaining critical questions. It should be faster and more consistent than a prompt alone, and every step should be traceable. The officer keeps every judgment: the recommendation, where risks go, conditions and submission.

It runs as a plugin in Microsoft Copilot Cowork on the work laptop. It works with whichever model Cowork offers, and nothing is hosted.

## Principles

- The officer's writing principle, approval-case guidance and five operating rules ([shared/operating-rules.md](../shared/operating-rules.md)) govern every skill.
- Depth over volume. The latest audited accounts are read in full, every note included. Key figures are explained with their sources: notes, management commentary, call transcripts. The last two years' developments are told, not only the risks.
- Scripts do the exact work, the model does the judgment, and the officer makes the decisions.
- The scripts use the Python standard library only, because Microsoft does not document which libraries Cowork's script environment has.

## Skills

| Skill | Owns | Hands over to |
|---|---|---|
| fp-lead | Brief, approval case, drafting and revisions, Word versions, readiness, Credit replies | Analysis to deal-analyst and the finance skills; challenge to investment-grill; polish to the style reviewer |
| deal-analyst | Company and transaction account, specialist views, risks, open items, annexes, "what's open?" | Emails, calls and notes to deal-updates |
| deal-updates | Emails, meeting transcripts, call notes, Word comments, informal guidance; who said what; the deal strategy | Documents to deal-analyst or annual-report-review |
| annual-report-review | Complete reading of annual accounts and notes, with a coverage record | Explanations to financial-performance-analysis |
| financial-performance-analysis | Movements, earnings quality, cash conversion, the FP financial table | Debt service to repayment-and-structure |
| repayment-and-structure | Borrower liquidity, debt service, covenants, protections and conditions | The case to fp-lead |
| investment-grill | Evidence-based challenge, rechecks, optional arbitration in a fresh task | Findings to fp-lead |
| fp-template-style-reviewer | Style preflight, house style, template compliance, layout | Changes in meaning to fp-lead |

Skills are methods that Cowork picks from what you say. They are not agents that run on their own. A review is independent only when it runs in a fresh task.

## The deal folder

The deal's folder, in OneDrive or SharePoint, gets an `FP assistant` subfolder:

| File | Role |
|---|---|
| `register.json` | The record: control (brief, current Word file, status), sources, risks, mitigants, open items, findings, analysis texts and the FP map. Written only by `register.py`. |
| `register.xlsx` | Read-only Excel view of the record, plus a Check sheet and the log. Regenerated after every change. |
| `Analysis.md` | Read-only view of the narrative: strategy, timeline, key figures, risk analyses, annual-accounts notes and annexes. |
| `DEAL-FP-vNN.docx` | The FP. A new file each round. You edit it in Word. |
| `DEAL-FP-vNN.sections.json` | What the assistant wrote in that version, used to detect your edits next round. |
| `DEAL-FP-vNN.proposals.md` | Text the assistant was not allowed to put into Word because you had edited or commented on that section. |

Every task starts with `register.py summary`, a single screen showing the status, next step, blockers and checks. Details come from `show` and the `Analysis.md` sections the task needs, not from re-reading everything.

## Rules the scripts enforce

`apply` rejects a whole change set, saving nothing, when it would:

- leave a risk, mitigant or open item without who raised it;
- link a mitigant or question to a risk that does not exist;
- mark a mitigant verified without a source, or an item answered without an answer source;
- move a high-rated risk to background, or lower a risk's rating, without your recorded decision;
- mark an item "later diligence" while its risk is in the main FP with no verified mitigant, unless you agreed;
- record Ready while there are open blockers (until closed), unassessed sources or risks to recheck;
- use an old revision (stale) or a value outside the allowed list.

Unfinished work stays visible: new questions start open and new sources start as "impact pending". A promise of evidence is "promised" and an answer awaiting assessment is "answered". Only "closed", with an answer source, removes an item from the lists.

Warnings, which do not block: Tier A documents not fully read, sources whose impact is not yet assessed, risks to recheck, FP paragraphs that cite only sources older than twelve months, and destinations without a reason. They appear in `summary` and on the Check sheet.

## Word rounds

- The first version is built from the template. Guidance text is replaced and fixed objects (template tables, images, fields) stay in place. Cover-page fields are filled from their labels, but only on the cover and only in cells without comments, tracked changes, fields or content controls.
- Later versions start from the newest Word file. A section the assistant wrote and nobody has touched since is replaced. A section you edited, commented on or tracked-changed is left exactly as it is in every later round, and the proposed text goes to `proposals.md`.
- The reading view (`inspect --markdown`) shows the content of kept tables, so reviewers see what the reader will see.
- Every version is a new file, so Word's Review → Compare shows what changed. `check` confirms that every template section is present and that no guidance text, source tags or markers are left.

## Reading the evidence

| Tier | Documents | Reading |
|---|---|---|
| A | Latest audited accounts (all of it), latest interim or management accounts, proposal or term sheet, prior FP and Credit decision, and any document critical to this decision | In full, part by part, with a page record and the annual-accounts checklist |
| B | Older accounts, historical correspondence, specialist material | Changes, restatements and relevant passages |
| C | Everything else | Searched only |

Unreadable pages stay "unreadable", never "not disclosed". Each checklist topic ends as found, not applicable, not disclosed or unresolved.

## Deal updates and strategy

Emails, transcripts, notes and Word comments are recorded with who said what and when. Statements, explanations, suggestions, commitments and decisions are kept apart: a promise to send a document is not the document. The current strategy (what must be true, the main evidence for and against, the next questions and whom to ask) is the `strategy` text in the register, owned by fp-lead.

## Review and readiness

One challenge round plus a recheck at each material checkpoint: the case plan, important sections, the whole draft and material revisions. A third, fresh task can arbitrate a disputed material finding when you ask for it.

The tools report "Register checks: passed" or what is still open. Readiness is a decision FP Lead records with you, for a named Word file and register revision. The register refuses it while checks are open and withdraws it when new open work arrives; `summary` warns when the Word file changed since. Submitting with exceptions is recorded as your decision.

## Evaluation

1. **Scripts:** unit tests, plus a self-test (`selftest`) that also runs inside Cowork.
2. **Early Cowork check:** as soon as the tools are packaged, on the work laptop: self-tests, file access, save and reopen, and the Word round trip on the real template ([INSTALL.md](../INSTALL.md)).
3. **One complete workflow:** a historical deal from evidence to full FP, then officer edits and a new email or transcript, then a fresh task. Judged by how much correction you needed.
4. **Model qualification:** the critical skill cases ([evaluations/](../evaluations/README.md)) on the model you use in Cowork. Rerun affected cases after a change; test another model before switching to it.

## Known limits

- Microsoft does not document how Cowork's scripts receive and save files. The early Cowork check tests this before live use.
- The financial table needs an identified export of the spreading tool. Duplicated labels or periods, and formulas without a trusted recalculation, are refused.
- Headings inside content controls are not found as sections. Content controls bound to data are left alone. Numbered lists in drafts become plain paragraphs. Predefined template tables are kept but not filled; only label/value cells on the cover are.
- One officer task writes at a time. The revision check catches stale writes; it is not a lock.
````

- [ ] **Step 4: Replace `README.md`**

````markdown
# FP Assistant

A plugin for Microsoft Copilot Cowork that helps an investment officer prepare a financing proposal (FP). It reads the deal's documents and correspondence, keeps a traceable record of sources, risks, mitigants and open items, drafts the FP in the institution's Word template, and lists the remaining critical questions. It works with whichever model Cowork offers. Nothing is hosted.

## What you say, and which skill answers

| You say | Skill |
|---|---|
| "Start an FP for <deal>; the folder is <link>" · "Draft / update the FP" · "Credit asked…" · "Is it ready?" | fp-lead |
| "Analyse the deal" · "What does this document change?" · "What's open?" | deal-analyst |
| "Check the latest emails" · "Here are my notes from the E&S call" · "Process the comments on v03" | deal-updates |
| "Read the annual report in full" | annual-report-review |
| "Explain the margin and cash movements" · "Build the financial table" | financial-performance-analysis |
| "Test repayment, covenants and conditions" | repayment-and-structure |
| "Grill this FP" · "Challenge the case" | investment-grill |
| "Run the style preflight" · "Polish v05" | fp-template-style-reviewer |

## How it works

- The deal folder (OneDrive or SharePoint) gets an `FP assistant` subfolder. It holds `register.json` (the record), the read-only views `register.xlsx` and `Analysis.md`, and the Word versions.
- Three scripts do the exact work using only Python's standard library: `register.py` (records, rules, one-screen summary), `fp_docx.py` (read, build and check Word files) and `fin_table.py` (spreading export → FP table). The AI never edits Word or Excel files itself.
- Sections you edit or comment on in Word are never overwritten. Proposed text for them goes to a separate file.

Design: [docs/design.md](docs/design.md). Install and acceptance steps: [INSTALL.md](INSTALL.md).

## Develop

    uv run pytest -q                  # tests; python-docx and openpyxl are test-only readers
    python3 scripts/package.py        # sync shared files into skills, check, build dist/*.zip

`shared/` and `tools/` hold the originals. `package.py` copies them into every skill that links to them and checks Microsoft's upload rules. Keep deal data out of this repository; everything in `evaluations/` is synthetic.

## Status

- **Scripts:** unit-tested, and self-tested on Python 3.9 and 3.12 with no third-party libraries.
- **Skills:** synthetic cases in [evaluations/](evaluations/README.md).
- **Cowork:** use on the work laptop starts with the acceptance steps in INSTALL.md.
````

- [ ] **Step 5: Replace `INSTALL.md`**

````markdown
# FP Assistant 0.3.0 — install and acceptance

## Upload to Copilot Cowork (work laptop)

1. Copy `fp-assistant-0.3.0.zip` to the work laptop.
2. In Cowork, open **Customize → Plugins → Upload plugin** and choose the zip without extracting it. Share it with **Only you** for the pilot.
3. Check that eight skills appear: fp-lead, deal-analyst, deal-updates, annual-report-review, financial-performance-analysis, repayment-and-structure, investment-grill and fp-template-style-reviewer.

If plugin upload is not available, extract `fp-assistant-individual-skills-0.3.0.zip` and upload each inner zip under **Customize → Skills → Add → Upload skill**. Remove older copies of these skills first; Cowork keeps duplicates under a numbered name rather than replacing them.

## First check (5 minutes, no deal data)

Start a new task and ask: *"Using fp-lead, run the self-tests of register.py, fp_docx.py and fin_table.py and show me the output."*

You should see three lines starting with `PASS`. If Cowork reports that Python is not available, the skills still work in proposal mode (analysis and draft text, without updating files). Note that result before going further.

## Acceptance with a test folder (no confidential data)

1. Create a OneDrive folder called `FP test deal`. Put in a blank copy of the FP template and a public annual report.
2. Ask: *"Start an FP for TestDeal; the folder is <link>."* Check that `FP assistant/register.xlsx` and `Analysis.md` appear in that folder and that the Excel file opens.
3. Ask for a first draft of one section. Check that `TestDeal-FP-v01.docx` opens in Word with no repair message.
4. In Word, change a paragraph in one section, add a comment in a second, make a tracked change in a third, and bold a phrase in a fourth. Ask: *"Update TestDeal from my edits"* and have it revise a fifth section. Then ask for a second update that touches the first four sections. In v03, check:
   - all four of your changes are unchanged;
   - the proposed text for those sections is in the `.proposals.md` files;
   - the fifth section was updated.
5. Ask the grill to review v03. Check that it quotes the content of the template's kept tables; it should not only report that a table is there.
6. Check that the cover fields were filled, and that a cover cell containing a comment or tracked change was left alone.
7. Repeat steps 1–4 with a SharePoint folder.

Write down pass or fail for each step before using the assistant on a live deal.

## What is included

- Eight skills, with shared rules and the scripts each skill uses.
- The scripts need Python 3.9 or later and nothing else.
- No connectors, no hosted services and no automatic sending: emails and replies are always drafts for you.
````

- [ ] **Step 6: Replace `AGENTS.md`**

````markdown
# Working on FP Assistant

- `skills/` holds the eight skills. `shared/` (rules) and `tools/` (scripts) hold the originals. Never edit the copies inside a skill: run `python3 scripts/package.py`, which copies each original into every skill that links to it and checks Microsoft's upload rules.
- Scripts use the Python standard library only and must run on Python 3.9, because Cowork's script environment is undocumented. Test-only libraries belong in the `dev` group of `pyproject.toml`.
- Scripts never overwrite their inputs, write atomically, and refuse rather than guess. Add a test for every new rule, and keep `selftest` passing.
- Keep skills model-neutral: no instructions written for one particular model.
- There is one current design, [docs/design.md](docs/design.md). `docs/archive/` is history only.
- Never commit confidential deal documents, real transcripts, private audience notes, credentials or institutional templates.
- Before committing, run `uv run pytest -q` and `python3 scripts/package.py --check`.
````

- [ ] **Step 7: Create `evaluations/README.md` and `evaluations/results.md`**

````markdown
# Evaluations

Everything here is synthetic. There are two kinds of checks.

1. **Scripts:** `uv run pytest -q` and `python3 tools/<tool>.py selftest`.
2. **Skills:** the cases in [scenarios.md](scenarios.md), [transcript-case.md](transcript-case.md) and [deal-updates-case.md](deal-updates-case.md), graded with [reviewer-guide.md](reviewer-guide.md) and the review records.

## Running a skill case

1. Start a fresh session with the model you use. Give it only the case text, the named skill folder(s) and their references. Never give it the reviewer guide.
2. Save its full answer as `runs/<date>-<model>/<case>.md`, with the model name, version and effort setting at the top.
3. In a separate fresh session, give a grader the case, the answer and the matching reviewer-guide criteria. Save its verdict next to the answer.
4. Add one line to [results.md](results.md): date, model, case, pass or fail, one-line reason.

## How much to run

- **Qualify the model you use in Cowork** on the critical cases: scenarios 1, 2, 3 and 5, and deal-updates-case.
- **After changing a skill,** rerun the cases that skill is involved in.
- **Before switching to another model,** run the critical cases on it first.

A case passes only if all its essential checks pass; writing quality is scored separately. The complete-workflow replay of a historical deal is the main quality test; these cases catch specific failures quickly.
````

````markdown
# Evaluation results

| Date | Model (version, effort) | Case | Result | Reason |
|---|---|---|---|---|
| 2026-10-01 | session model of the authoring agent | transcript-case | pass | graded independently; one wording error recorded in transcript-review.md |
| 2026-10-02 | session model of the authoring agent | deal-updates-case | pass | author-graded; see deal-updates-review.md |
````

- [ ] **Step 8: Check every relative link, rebuild, test**

```bash
python3 - <<'EOF'
import re, pathlib
bad = []
for p in pathlib.Path(".").rglob("*.md"):
    if any(x in p.parts for x in ("dist", ".venv", ".git")):
        continue
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", p.read_text()):
        if not target.startswith(("http", "mailto")) and not (p.parent / target).exists():
            bad.append(f"{p}: {target}")
print("\n".join(bad) or "all relative links resolve")
EOF
```

Expected: `all relative links resolve`

Run: `python3 scripts/package.py && uv run pytest -q`
Expected: two `OK` zip lines, then `55 passed`.

- [ ] **Step 9: Commit**

```bash
git add -A docs README.md INSTALL.md AGENTS.md evaluations
git commit -m "Replace layered documents with one current design; archive history"
```

---

### Task 7: Early Cowork check on the work laptop (no deal data)

Run this as soon as Tasks 5 and 6 are done (both are local). It answers the open question: how do Cowork's scripts receive and save files?

**Files:**
- Modify: `evaluations/results.md` (record the outcome)

- [ ] **Step 1:** Copy `dist/fp-assistant-0.3.0.zip` to the work laptop. Upload it in Cowork (Customize → Plugins → Upload plugin, **Only you**) and confirm the eight skills appear.
- [ ] **Step 2:** In a new task, ask fp-lead to run the three self-tests. Expected: three `PASS` lines. If Python is unavailable, record that and stop; the skills still work in proposal mode while a decision is made.
- [ ] **Step 3:** Run "Acceptance with a test folder" in `INSTALL.md` (written in Task 6, Step 5), steps 1–6, with the **real FP template** in a OneDrive folder and no deal data. Record pass or fail for each:
  - the register files appear and the Excel file opens;
  - v01 opens in Word without repair;
  - your edit, comment, tracked change and bold text all survive two later rounds;
  - the proposals files hold the refused text;
  - the grill can read the kept tables;
  - cover fields are filled and protected cover cells are untouched.
- [ ] **Step 4:** Repeat on a SharePoint folder.
- [ ] **Step 5:** Add the rows `cowork-check-onedrive` and `cowork-check-sharepoint` to `evaluations/results.md`, including the exact Cowork message for any failure. Commit:

```bash
git add evaluations/results.md
git commit -m "Record early Cowork check"
```

If a step fails, try the fallback that matches it and add a regression test before retrying:
- attach the `FP assistant` folder to the task explicitly;
- save outputs to the Cowork output folder and move them;
- for a template feature the Word tool does not support, keep that section in proposal mode.

---

### Task 8: One complete workflow on a historical deal (in the work tenant)

This is the main quality test: does the assistant produce a useful full FP, and does it hold up through edits and new information? The deal data stays in the tenant; only the outcome is recorded here.

**Setup (officer):**
- Pick a past deal with an approved FP.
- Copy its evidence as it stood before that FP into a OneDrive test folder.
- Add the template, approved style examples (not the target FP itself), the spreading export and its mapping. Add `expect` cells for entity, unit and period headers.

- [ ] **Step 1: Draft the complete FP.** In a new task: "Start an FP for <deal>; the folder is <link>." Confirm the brief, let the analyst read Tier A in full, then ask for the complete FP. A representative section first is optional, for troubleshooting only.
- [ ] **Step 2: Judge the draft.** Does it explain the business and the numbers logically (drivers, cash, repayment)? Does it include the relevant detail, and does it read naturally in house style? Note the material errors and omissions, and how long your corrections take.
- [ ] **Step 3: Edit and add news.**
  - Make your usual edits in Word: wording, a comment, a tracked change.
  - Add one later email or call transcript to the folder that changes something, for example a covenant waiver or a revised forecast.
  - Leave at least one question unanswered.
- [ ] **Step 4: Resume in a fresh task.** Ask fp-lead to continue. Verify:
  - your edits and comments are unchanged, with proposals for those sections in `proposals.md`;
  - the unanswered question is still in `lists` and in `summary`, including any `promised` or `answered` ones;
  - the new email or transcript is a source with an impact assessment;
  - its information reaches `Analysis.md` and the right FP passages (updated sections or proposals);
  - `summary` reports the register checks honestly.
- [ ] **Step 5: Record and fix.** Add a `replay-<deal-code>` row to `evaluations/results.md` with the correction time, the number of material corrections and the main failures (no confidential detail). For each failure, change the skill or tool, add a test or evaluation case, and rerun the affected step. Commit:

```bash
git add evaluations/results.md skills shared tools tests
git commit -m "Historical replay: record results and fixes"
```

---

### Task 9: Qualify the model you use in Cowork

- [ ] **Step 1:** Run the critical cases (scenarios 1, 2, 3 and 5, and `deal-updates-case`) on the model selected in Cowork, following `evaluations/README.md`. Save the runs and add the rows to `evaluations/results.md`.
- [ ] **Step 2:** Fix the skill text for any failed essential check, rerun only the affected cases, and commit:

```bash
git add evaluations skills shared
git commit -m "Qualify the Cowork model on the critical cases"
```

Later: rerun affected cases after a skill change, and run the critical cases before switching to another model. There is no blanket two-model requirement.

## Deferred, with the trigger to add them

- **Filling predefined template tables:** add if the real template keeps an empty financial table that `{{keep:N}}` preserves but leaves empty.
- **Numbered lists in drafts:** add if review keeps flagging plain-paragraph numbering.
- **Headings inside content controls, or cover fields in content controls:** add if Task 6 shows the real template uses them.

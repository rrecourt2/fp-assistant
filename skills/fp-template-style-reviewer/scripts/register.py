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
            "risks": {"status": "open"}, "findings": {"status": "open"}}


class ChangeError(Exception):
    """A change set was rejected; the register is unchanged."""


class ViewsIncompleteError(OSError):
    """The JSON record is saved, but its generated views need a retry."""


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
    atomic_text(folder / "register.json", data)
    refresh_views(folder, reg)


def atomic_text(path, text):
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def refresh_views(folder, reg):
    try:
        write_views(folder, reg)
    except (OSError, ChangeError, zipfile.BadZipFile) as e:
        raise ViewsIncompleteError(f"register revision {reg['revision']} saved; views incomplete: {e}. "
                                   "Retry the same change set to regenerate the views.") from e


def write_views(folder, reg):
    folder = Path(folder)
    sheets = [("Control", ["field", "value"], [[k, reg["control"].get(k, "")] for k in CONTROL]
               + [["register_revision", reg["revision"]]])]
    for name, (_, cols) in TABLES.items():
        sheets.append((name.replace("_", " ").capitalize(), cols, [[r.get(c, "") for c in cols] for r in reg[name]]))
    sheets.append(("Check", ["severity", "rule", "item", "detail"], [list(p) for p in problems(reg)]))
    sheets.append(("Log", ["at", "revision", "actor", "op_id", "summary", "next_step"],
                   [[e.get(c, "") for c in ("at", "revision", "actor", "op_id", "summary", "next_step")]
                    for e in reg["log"]]))
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".xlsx.tmp")
    os.close(fd)
    try:
        write_xlsx(tmp, sheets)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() is not None:
                raise ChangeError("generated register.xlsx failed its integrity check")
        os.replace(tmp, folder / "register.xlsx")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    atomic_text(folder / "Analysis.md", analysis_md(reg))


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
    if not isinstance(ch, dict):
        raise ChangeError("each change must be an object")
    sheet = ch.get("sheet")
    fields = ch.get("add", ch.get("set", {}))
    if not isinstance(fields, dict) or any(not isinstance(v, str) for v in fields.values()):
        raise ChangeError("add/set fields must be an object of strings; omit unavailable fields")
    if sheet == "control":
        for k, v in fields.items():
            if k not in CONTROL:
                raise ChangeError(f"control has no field {k!r}")
            if k == "ready_for":
                raise ChangeError("ready_for is assigned when recording readiness")
            if k == "status" and not str(v).strip():
                raise ChangeError("control status cannot be blank")
            reg["control"][k] = str(v)
        return None
    if sheet not in TABLES:
        raise ChangeError(f"unknown sheet {sheet!r}; use one of {['control'] + list(TABLES)}")
    prefix, cols = TABLES[sheet]
    rows = reg[sheet]
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
                for k, v in fields.items():
                    if (sheet, k) in ALLOWED and r.get(k) and not str(v).strip():
                        raise ChangeError(f"{target}: {k} cannot be blank; choose an explicit state")
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
    if not isinstance(changes, dict) or not isinstance(changes.get("changes", []), list):
        raise ChangeError("a change set must be an object with a changes list")
    reg = load(folder)
    if any(e.get("op_id") == changes.get("op_id") for e in reg["log"]):
        refresh_views(folder, reg)  # repairs views an interrupted run may have left stale
        return {"status": "already-applied", "revision": reg["revision"]}
    if changes.get("base_revision") != reg["revision"]:
        raise ChangeError(f"stale: change set is based on revision {changes.get('base_revision')}, "
                          f"the register is at {reg['revision']}; re-read with summary and retry")
    if not isinstance(changes.get("op_id"), str) or not changes["op_id"].strip():
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
                and (not r["officer_decision"].strip()
                     or r["officer_decision"] == o["officer_decision"])):
            introduced.append(("error", "officer-decision", r["id"],
                               f"downgrading {o['rating']} to {r['rating'] or 'unrated'} needs the officer's "
                               "decision in officer_decision"))
    if introduced:
        raise ChangeError("rejected, nothing saved:\n" + "\n".join(f"  {p[2]}: {p[3]}" for p in introduced))
    notes = []
    c = new["control"]
    control_changes = {k: v for ch in changes.get("changes", []) if ch.get("sheet") == "control"
                       for k, v in ch.get("set", {}).items()}
    requested_ready = control_changes.get("status") == "ready"
    word = recorded_word(folder, new)
    if requested_ready:
        reasons = open_checks(new, word)
        if not str(control_changes.get("ready_by", "")).strip():
            reasons.append("explicit officer ready_by is required")
        if not c["word"].strip() or not c["word_sha256"].strip():
            reasons.append("a current Word file and word_sha256 are required")
        if reasons:
            raise ChangeError("cannot record ready, nothing saved: " + "; ".join(reasons))
        c["ready_for"] = f"{c['word']} at register revision {new['revision'] + 1}"
    elif reg["control"]["status"] == "ready":
        reasons = open_checks(new, word)
        if any(new[name] != reg[name] for name in TABLES):
            reasons.append("evidence or analysis changed since readiness was recorded")
        if any(c[k] != reg["control"][k] for k in CONTROL if k != "updated"):
            reasons.append("the Word record or control details changed since readiness was recorded")
        if reasons:
            if c["status"] == "ready":
                c["status"] = "draft"
            c.update(ready_for="", ready_by="")
            notes.append("readiness withdrawn: " + "; ".join(reasons))
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
    blockers += [f["id"] for f in reg["findings"] if f["priority"] == "blocker" and f["status"] != "resolved"]
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
                required = column in DEFAULTS.get(name, {})
                if table == name and (r.get(column) or required) and r.get(column) not in allowed:
                    err("allowed-value", r["id"], f"{column}={r[column]!r}; use one of {sorted(allowed)}")
    status = reg["control"].get("status")
    if status not in ALLOWED[("control", "status")]:
        err("allowed-value", "control", f"status={status!r}")
    risks = {r["id"]: r for r in reg["risks"]}
    verified = {m["risk"] for m in reg["mitigants"] if m["verified"] == "yes"}
    for r in reg["risks"]:
        if not r["raised_by"].strip():
            err("raised-by", r["id"], "record who raised this risk")
        if r["rating"] == "high" and r["destination"] == "background" and not r["officer_decision"].strip():
            err("officer-decision", r["id"], "a high-rated risk moves to background only with the officer's decision")
        if r["destination"] and not r["reason"].strip():
            warn("destination-reason", r["id"], "give a reason for the destination")
    for m in reg["mitigants"]:
        if m["risk"] not in risks:
            err("link", m["id"], f"mitigant points to unknown risk {m['risk']!r}")
        if not m["raised_by"].strip():
            err("raised-by", m["id"], "record who raised this mitigant")
        if m["verified"] == "yes" and not m["source"].strip():
            err("evidence", m["id"], "a verified mitigant needs a source")
    for o in reg["open_items"]:
        if o["link"].startswith("R-") and o["link"] not in risks:
            err("link", o["id"], f"open item points to unknown risk {o['link']!r}")
        if not o["raised_by"].strip():
            err("raised-by", o["id"], "record who raised this item")
        if o["status"] in ("answered", "closed") and not o["answer_source"].strip():
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


def recorded_word(folder, reg):
    name = reg["control"]["word"].strip()
    return Path(folder) / name if name else None


def word_problem(reg, word):
    if word is None:
        return None
    try:
        if sha256(word) != reg["control"]["word_sha256"]:
            return "the Word file changed since it was last recorded"
    except OSError:
        return "the recorded Word file is unavailable; its hash could not be checked"
    return None


def open_checks(reg, word=None):
    reasons = [f"{n} rule errors" for n in [sum(p[0] == "error" for p in problems(reg))] if n] + gates(reg)
    problem = word_problem(reg, word)
    if problem:
        reasons.append(problem)
    return reasons


# ---------- views for the assistant ----------

def short(text, n=90):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1] + "…"


def summary(reg, word=None):
    c = reg["control"]
    changed = bool(word_problem(reg, word))
    lines = [f"{c['deal']} · register revision {reg['revision']}"]
    if c["status"] == "ready" and changed:
        lines.append("Status: draft — the Word file changed since readiness was recorded or is unavailable")
    elif c["status"] == "ready":
        lines.append(f"Status: ready ({c['ready_for']}, recorded by {c['ready_by'] or 'unknown'})"
                     + (" — current Word hash not checked" if word is None else ""))
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
    lines.append(f"Findings: {sum(f['status'] != 'resolved' for f in reg['findings'])} unresolved")
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
    rows = {r["id"]: (name, r) for name in TABLES if name != "analysis" for r in reg[name]}
    for r in reg["analysis"]:
        rows.setdefault(r["id"], ("analysis", r))
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
    client = [o for o in opened if o["status"] != "answered"
              and any(w in o["addressee"].lower() for w in CLIENT)]
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
            reg = load(args.folder)
            print(summary(reg, args.word or recorded_word(args.folder, reg)))
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
            reasons = open_checks(reg, args.word or recorded_word(args.folder, reg))
            print("Register checks: passed" if not reasons else "Register checks: not passed — " + "; ".join(reasons))
            return 1 if reasons else 0
        else:
            print(selftest())
    except ViewsIncompleteError as e:
        print(f"SAVED: {e}", file=sys.stderr)
        return 4
    except (ChangeError, json.JSONDecodeError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

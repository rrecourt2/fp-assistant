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
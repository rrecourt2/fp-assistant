#!/usr/bin/env python3
"""Read, build and check FP Word files with the Python standard library only.

document.xml is changed by splicing byte ranges; XML this tool did not generate is
never re-serialised, and every other file inside the .docx is copied unchanged (only a
.dotx template's main content type becomes a document's). Macro-enabled files are refused.
A section is the body between one heading and the next heading of any level.

  fp_docx.py inspect DOCX [--markdown]
  fp_docx.py build --base BASE.docx --content CONTENT.md --out OUT.docx [--first | --existing]
                   [--template BLANK.docx] [--fields FIELDS.json] [--protect ID,ID]
  fp_docx.py check DOCX [--template TEMPLATE.docx]
  fp_docx.py selftest

Build modes (a section with comments or tracked changes is never rewritten in any mode):
  --first     a new FP from the blank template; BASE must be byte-identical to --template.
  --existing  an officer's draft without an assistant record, checked against --template; every
              section named in the draft is rewritten except those listed in --protect and those
              holding a missing template heading as plain text.
  (neither)   a later round; needs BASE.sections.json and rewrites only sections the assistant
              wrote that nobody has changed since.
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
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
XML_SPACE = "http://www.w3.org/XML/1998/namespace space"
AI_TAG = "fp-assistant"
ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
TAG = re.compile(r"\s*\[[SRMOGT]-\d+[^\]]*\]")
TAG_ID = re.compile(r"\b[SRMOGT]-\d+\b")
TRACKED = {"ins", "del", "moveFrom", "moveTo", "pPrChange", "rPrChange", "tblPrChange",
           "trPrChange", "tcPrChange", "sectPrChange", "cellIns", "cellDel"}
COMMENT = {"commentRangeStart", "commentRangeEnd", "commentReference"}
FIXED = {"drawing", "pict", "object", "fldChar", "fldSimple", "instrText", "sectPr", "sdt",
         "AlternateContent", "oMath", "footnoteReference", "endnoteReference"}
NOISE = {"proofErr", "lastRenderedPageBreak"}
LAYOUT = {"tblPr", "tblGrid", "trPr", "tcPr", "tblPrEx"}  # table layout Word rewrites when it saves
TEMPLATE_MAIN, DOCUMENT_MAIN = b"wordprocessingml.template.main+xml", b"wordprocessingml.document.main+xml"


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
        """Text as if tracked changes were accepted, with tabs and line breaks."""
        out = []
        for n in self.iter():
            s = ("".join(n.text) if n.tag == "t" else "\t" if n.tag == "tab" and n.parent.tag == "r"
                 else "\n" if n.tag == "br" and n.wattr("type") not in ("page", "column") else "")
            if s and n.uri == W and not n.deleted():
                out.append(s)
        return "".join(out)


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
    """styleId -> (name, heading level or None), levels following basedOn chains; the id of the
    default paragraph style; and the list styles (named "List ..." or carrying numbering)."""
    if not styles_xml:
        return {}, "Normal", set()
    w = "{%s}" % W
    raw, default, lists = {}, "Normal", set()
    for s in ET.fromstring(styles_xml).iter(w + "style"):
        sid = s.get(w + "styleId")
        if s.get(w + "type") == "paragraph" and s.get(w + "default") in ("1", "true", "on"):
            default = sid
        name = s.find(w + "name")
        lvl = s.find(f"{w}pPr/{w}outlineLvl")
        base = s.find(w + "basedOn")
        raw[sid] = (name.get(w + "val") if name is not None else sid,
                    int(lvl.get(w + "val")) if lvl is not None else None,
                    base.get(w + "val") if base is not None else None)
        if "list" in (raw[sid][0] or "").lower() or s.find(f"{w}pPr/{w}numPr") is not None:
            lists.add(sid)

    def level(sid, seen=()):
        if sid not in raw or sid in seen:
            return None
        _, lvl, base = raw[sid]
        if lvl is not None:
            return lvl + 1 if lvl < 9 else None
        return level(base, seen + (sid,)) if base else None

    return {sid: (v[0], level(sid)) for sid, v in raw.items()}, default, lists


class Doc:
    """A .docx opened for reading: zip entries, document.xml bytes, tree, styles, sections."""

    def __init__(self, path):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as z:
            self.infos = z.infolist()
            self.parts = {i.filename: z.read(i.filename) for i in self.infos}
        self.xml = self.parts["word/document.xml"]
        types = self.parts.get("[Content_Types].xml", b"")
        self.template, self.macro = TEMPLATE_MAIN in types, b"macroEnabled" in types
        self.root = scan(self.xml)
        head = self.xml[self.root.start:tag_end(self.xml, self.root.start)]
        m = re.search(rb'xmlns:(\w+)="' + re.escape(W.encode()) + b'"', head)
        if not m:
            raise Refuse("the Word main namespace has no prefix; refusing to guess")
        self.w = m.group(1).decode()
        self.styles, self.default_style, self.list_styles = style_info(self.parts.get("word/styles.xml"))
        self.style_id = {name: sid for sid, (name, _) in self.styles.items()}
        self.body = self.root.find("body")
        if self.body is None:
            raise Refuse(f"{self.path.name} has no document body")
        self.goback = {n.wattr("id") for n in self.root.iter()  # Word's "last edit" bookmark is save noise
                       if n.tag == "bookmarkStart" and n.wattr("name") == "_GoBack"}
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
                        "head": kids[i], "body": body, "doc": self})
        return out

    def comments(self):
        """Comment id -> {author, date, text}."""
        xml = self.parts.get("word/comments.xml")
        if not xml:
            return {}
        return {c.wattr("id"): {"author": c.wattr("author") or "", "date": c.wattr("date") or "",
                                "text": c.plain().strip()}
                for c in scan(xml).kids if c.tag == "comment"}


def canon(n, doc, masked=()):
    """n as nested lists [tag, attributes, text, children] without the noise of a Word save: w14 and
    rsid attributes, xml:space (the exact text is kept), proofing marks, _GoBack, run languages,
    paragraph-mark properties, the default paragraph style and table layout. Adjacent runs with equal
    properties are merged. A cell in `masked` (filled through --fields) counts by its formatting and
    protected marks only."""
    if id(n) in masked:
        p = n.find("p")
        r = p.find("r") if p is not None else None
        keep = [x for x in (p and p.find("pPr"), r and r.find("rPr")) if x is not None]
        return ["filled cell", [], "", [canon(x, doc) for x in keep + [
            x for x in n.iter() if x.tag in COMMENT | TRACKED | {"hyperlink"}]]]
    attrs = sorted([k, v] for k, v in n.attrs.items() if k != XML_SPACE and not k.startswith(W14 + " ")
                   and not k.rpartition(" ")[2].startswith("rsid"))
    if n.tag == "tbl":
        attrs.append(["assistant table", str(not is_fixed(n))])
    text = "".join(n.text)
    out = [n.tag if n.uri == W else f"{n.uri} {n.tag}", attrs,
           text if n.tag in ("t", "delText", "instrText") else text.strip(), []]
    for k in n.kids:
        default_style = k.tag == "pStyle" and k.wattr("val") == doc.default_style
        if (k.tag in NOISE or k.tag in LAYOUT or (n.tag == "rPr" and k.tag in ("lang", "noProof"))
                or (k.tag in ("bookmarkStart", "bookmarkEnd") and k.wattr("id") in doc.goback)
                or (n.tag == "pPr" and (k.tag == "rPr" or default_style))):
            continue
        c = canon(k, doc, masked)
        if not (k.tag in ("pPr", "rPr") and not c[1] and not c[3]):  # properties that became empty
            merge(out[3], c)
    return out


def merge(kids, c):
    """Append canonical node c, joining adjacent text, and adjacent runs with equal properties."""
    last, props = kids[-1] if kids else None, lambda r: [x for x in r[3] if x[0] == "rPr"]
    if last and last[0] == c[0] == "t":
        last[2] += c[2]
    elif last and last[0] == c[0] == "r" and props(last) == props(c):
        for x in c[3]:
            if x[0] != "rPr":
                merge(last[3], x)
    else:
        kids.append(c)


def signature(sec):
    data = json.dumps([canon(k, sec["doc"]) for k in [sec["head"]] + sec["body"]])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def fixed_node(n, goback):
    """An object, field, control, section break, note reference, bookmark or page/column break."""
    return (n.tag in FIXED or (n.tag in ("bookmarkStart", "bookmarkEnd") and n.wattr("id") not in goback)
            or (n.tag == "br" and n.wattr("type") in ("page", "column")))


def is_fixed(k):
    """Content this tool must keep in place: template tables, captions and paragraphs with fixed nodes."""
    if k.tag == "tbl":
        d = k.find("tblPr", "tblDescription")
        return not (d is not None and d.wattr("val") == AI_TAG)
    if k.tag != "p":
        return True
    goback = {n.wattr("id") for n in k.iter() if n.tag == "bookmarkStart" and n.wattr("name") == "_GoBack"}
    if any(fixed_node(n, goback) for n in k.iter()):
        return True
    style = k.find("pPr", "pStyle")
    return style is not None and "caption" in (style.wattr("val") or "").lower()


def inventory(doc, filled=()):
    """The fixed objects of the whole body as a sorted list (a multiset). Cover cells filled through
    --fields (indexes among all w:tc) count by their formatting only."""
    tcs = [n for n in doc.body.iter() if n.tag == "tc"]
    masked, out = {id(tcs[i]) for i in filled}, []
    for n in doc.body.iter():
        if n.tag == "bookmarkStart" and n.wattr("name") != "_GoBack":
            out.append(f"bookmark {n.wattr('name')}")
        elif n.tag in ("instrText", "fldSimple"):
            out.append("field " + (n.wattr("instr") or "".join(n.text)))
        elif n.tag in ("drawing", "pict", "object"):
            out.append("object")
        elif n.tag == "tbl" and is_fixed(n):
            out.append("table " + json.dumps(canon(n, doc, masked)))
        elif n.tag in ("sdt", "sectPr", "footnoteReference", "endnoteReference"):
            out.append(f"{n.tag} {n.wattr('id') or ''}")
        elif n.tag == "br" and n.wattr("type") in ("page", "column"):
            out.append(f"break {n.wattr('type')}")
    return sorted(out)


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
    data = read_json(p) if p.exists() else {"sections": {}}
    if not (isinstance(data, dict) and isinstance(data.get("sections"), dict)
            and all(isinstance(v, dict) for v in data["sections"].values())):
        raise Refuse(f"{p.name} is not an assistant record")
    return data


def read_text(path):
    """UTF-8 text without a byte order mark; anything else is refused."""
    try:
        return Path(path).read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Refuse(f"{Path(path).name} is not UTF-8 text") from None


def read_json(path):
    try:
        return json.loads(read_text(path))
    except ValueError as e:
        raise Refuse(f"{Path(path).name} is not valid JSON ({e})") from None


def publish(path, write):
    """Call write(temp path) for a temp file next to path, then rename it into place with mode 0644."""
    fd, tmp = tempfile.mkstemp(dir=Path(path).parent, suffix=".tmp")
    os.close(fd)
    try:
        write(tmp)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def write_text_file(path, text):
    publish(path, lambda tmp: Path(tmp).write_text(text, encoding="utf-8"))


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- content markdown ----------

def parse_content(text):
    """'## section' blocks -> ({section_id: {"blocks": [...], "raw": str, "ids": [...]}}, warnings)."""
    raw, cur, stray = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\S.*?)\s*$", line)
        if m and not line.startswith("###"):
            cur = slug(m.group(1))
            if cur in raw:
                raise Refuse(f"the draft has more than one '## {cur}' section")
            raw[cur] = []
        else:
            (stray if cur is None else raw[cur]).append(line)
    stray = "\n".join(stray).strip()
    warnings = [f"text before the first '## section' heading was not used: {stray}"] if stray else []
    return {k: {"blocks": blocks(v), "raw": "\n".join(v).strip(),
                "ids": sorted(set(TAG_ID.findall("\n".join(v))))} for k, v in raw.items()}, warnings


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
        self.w, self.ids, self.default = doc.w, doc.style_id, doc.default_style

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
        explicit = style_id not in (None, self.default)  # the default style is never written out
        ppr = f'<{w}:pPr><{w}:pStyle {w}:val="{style_id}"/></{w}:pPr>' if explicit else ""
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
    """New XML for a section body; fixed content is placed at {{keep:N}} or appended. Prose takes the
    style of the section's first plain paragraph that is not a list."""
    gen = Gen(doc)
    fixed = [k for k in sec["body"] if is_fixed(k)]
    styles = [k.find("pPr", "pStyle") for k in sec["body"] if not is_fixed(k) and k.tag == "p"]
    styles = [s.wattr("val") if s is not None else doc.default_style for s in styles]
    body_style = next((s for s in styles if s not in doc.list_styles), doc.default_style)
    bullet_style = doc.style_id.get("List Bullet")
    keep = lambda k: (k if k.tag == "tbl" else None, doc.xml[k.start:k.end].decode("utf-8"))  # noqa: E731
    out, used = [], set()  # (kept table node, "generated" or None; xml)
    for kind, value in items:
        if kind == "p":
            out.append((None, gen.p(value, body_style)))
        elif kind == "bullet":
            out.append((None, gen.p(value, bullet_style) if bullet_style else gen.p("• " + value, body_style)))
        elif kind == "table" and value:
            out.append(("generated", gen.table(value)))
        elif kind == "keep" and 1 <= value <= len(fixed) and value not in used:
            out.append(keep(fixed[value - 1]))
            used.add(value)
    out += [keep(k) for n, k in enumerate(fixed, 1) if n not in used]
    pos = {id(k): i for i, k in enumerate(sec["body"])}
    xml, before = "", None
    for table, x in out:  # Word merges tables that touch; keep them apart unless they touched in the base
        if table is not None and before is not None and not (
                isinstance(table, Node) and isinstance(before, Node) and pos[id(table)] == pos[id(before)] + 1):
            xml += f"<{doc.w}:p/>"
        xml, before = xml + x, table
    return xml


def splice(xml, edits):
    """Apply (start, end, replacement bytes) edits, last first so offsets stay valid."""
    for start, end, new in sorted(edits, key=lambda e: e[0], reverse=True):
        xml = xml[:start] + new + xml[end:]
    return xml


def fill_fields(doc, xml, fields):
    """Set the cell right of a matching label cell on the cover (before the first heading), keeping
    the first paragraph's pPr and first run's rPr. A cell with comments, tracked changes, fixed
    objects, bookmarks, hyperlinks or nested tables is protected and left alone.
    Returns the new xml, the filled cells (indexes among all w:tc), missing and protected labels."""
    want, done, protected, edits, filled = {norm(k): str(v) for k, v in fields.items()}, set(), set(), [], []
    limit = doc.sections[0]["head"].start if doc.sections else len(xml)  # sections are spliced after this point
    tcs = [n for n in doc.body.iter() if n.tag == "tc"]
    for tr in (n for n in doc.body.iter() if n.tag == "tr" and n.start < limit):
        cells = [c for c in tr.kids if c.tag == "tc"]
        for label, value in zip(cells, cells[1:]):
            key, paras = norm(label.plain()), [k for k in value.kids if k.tag == "p"]
            if key not in want or key in done or not paras:
                continue
            if any(fixed_node(n, doc.goback) or n.tag in COMMENT | TRACKED | {"hyperlink", "tbl"}
                   for n in value.iter()) or any(map(is_fixed, paras)):
                protected.add(key)
                continue
            ppr, run = paras[0].find("pPr"), paras[0].find("r")
            rpr = run.find("rPr") if run is not None else None
            w = doc.w
            new = (f"<{w}:p>{xml[ppr.start:ppr.end].decode() if ppr is not None else ''}<{w}:r>"
                   f"{xml[rpr.start:rpr.end].decode() if rpr is not None else ''}"
                   f'<{w}:t xml:space="preserve">{escape(ILLEGAL.sub("", want[key]))}</{w}:t></{w}:r></{w}:p>')
            edits.append((paras[0].start, paras[-1].end, new.encode("utf-8")))
            filled.append(tcs.index(value))
            done.add(key)
    missing = sorted(k for k in fields if norm(k) not in done)
    return splice(xml, edits), filled, missing, [k for k in missing if norm(k) in protected]


def verify(base, new, written, filled):
    """The preservation check: refuse unless everything this build did not write is unchanged."""
    if [s["id"] for s in new.sections] != [s["id"] for s in base.sections]:
        raise Refuse("headings changed during the build; nothing written")
    changed = [a["id"] for a, b in zip(base.sections, new.sections)
               if a["id"] not in written and signature(a) != signature(b)]
    if changed:
        raise Refuse(f"sections not written in this build changed ({', '.join(changed)}); nothing written")
    if inventory(base, filled) != inventory(new, filled):
        raise Refuse("fixed objects (bookmarks, fields, objects, tables, content controls, breaks or notes) "
                     "changed; nothing written")


def write_docx(doc, xml, out, written, filled):
    """Write the zip to a temp file, run the preservation check on it, then rename it into place."""
    parts = {**doc.parts, "word/document.xml": xml}
    if doc.template:  # a .dotx base gives a document
        parts["[Content_Types].xml"] = parts["[Content_Types].xml"].replace(TEMPLATE_MAIN, DOCUMENT_MAIN)

    def write(tmp):
        with zipfile.ZipFile(tmp, "w") as z:
            for info in doc.infos:
                z.writestr(info, parts[info.filename])
        verify(doc, Doc(tmp), written, filled)

    publish(out, write)


def check_mode(doc, base, mode, template):
    """Refuse a build mode that does not fit the base (see the module docstring)."""
    record = sidecar_path(base).exists()
    if mode not in ("first", "existing", "normal"):
        raise Refuse(f"unknown build mode {mode!r}")
    if doc.macro:
        raise Refuse("macro-enabled Word files (.docm, .dotm) are not supported")
    if doc.template and mode != "first":
        raise Refuse("a Word template (.dotx) can only be the base of --first")
    if mode == "first":
        if not template:
            raise Refuse("--first needs --template: the configured blank FP template")
        if file_sha256(base) != file_sha256(template):
            raise Refuse("--first builds only from the blank template: the base is not identical to it; "
                         "for an officer's draft use --existing")
        if record:
            raise Refuse(f"{sidecar_path(base).name} exists, so the base is an FP with an assistant record; "
                         "use a normal round")
    elif mode == "existing":
        if record:
            raise Refuse(f"{sidecar_path(base).name} exists; use a normal round instead of --existing")
        if not template:
            raise Refuse("--existing needs --template: the blank FP template is used to check the draft's "
                         "headings")
    elif not record:
        raise Refuse(f"no assistant record ({sidecar_path(base).name}) next to the base; use --existing for "
                     "an officer's draft or --first for the blank template")


def build(base, content, out, mode="normal", template=None, fields=None, protect=()):
    out = Path(out)
    record, proposals = sidecar_path(out), out.with_suffix(".proposals.md")
    for p in (out, record, proposals):
        if p.exists():
            raise Refuse(f"{p.name} already exists; choose a new version name")
    if fields is not None and not isinstance(fields, dict):
        raise Refuse("--fields must be a JSON object of cover label: value")
    doc = Doc(base)
    check_mode(doc, base, mode, template)
    baseline = load_sidecar(base)["sections"] if mode == "normal" else {}
    wanted, warnings = parse_content(read_text(content))
    by_id = {s["id"]: s for s in doc.sections}
    unknown = sorted(set(protect) - set(by_id))
    if unknown:
        raise Refuse(f"--protect names no section of the document: {', '.join(unknown)}")
    # The writer cannot insert headings, so template sections absent from the base stay absent.
    tpl = Doc(template) if template else None
    missing_sections = [s["id"] for s in tpl.sections if s["id"] not in by_id] if tpl else None
    if missing_sections is None:
        warnings.append("missing template sections were not checked: no --template was given")
    if fields and not doc.sections:
        raise Refuse("--fields refused: the document has no recognised headings, so its cover cannot be told "
                     "from its body")
    if fields and tpl and tpl.sections and doc.sections[0]["id"] != tpl.sections[0]["id"]:
        raise Refuse(f"--fields refused: the first recognised heading is {doc.sections[0]['id']!r}, not the "
                     f"template's first section {tpl.sections[0]['id']!r}, so tables before it may not be the "
                     "cover; give the earlier headings their Heading style in Word")
    base_sig = {sid: signature(sec) for sid, sec in by_id.items()}
    edits, written, frozen, unmatched = [], [], {}, []
    for sid, item in wanted.items():
        sec = by_id.get(sid)
        if sec is None:
            unmatched.append(sid)
            continue
        f, b = flags(sec), baseline.get(sid, {})
        # A missing template heading typed as plain text: rewriting would delete the text under it.
        lost = sorted(set(missing_sections or ()) & {slug(k.plain()) for k in sec["body"] if k.tag == "p"})
        if f["has_comments"] or f["has_tracked_changes"]:
            frozen[sid] = "has comments or tracked changes"
        elif sid in protect:
            frozen[sid] = "protected at the officer's request"
        elif lost:
            frozen[sid] = (f"contains the missing template heading {', '.join(lost)} as plain text; "
                           "give it a Heading style in Word")
        elif mode == "normal" and b.get("owner") != "ai":
            frozen[sid] = "not written by the assistant in the base version"
        elif mode == "normal" and b.get("signature") != base_sig[sid]:
            frozen[sid] = "edited since the assistant wrote it"
        else:
            start, end = (sec["body"][0].start, sec["body"][-1].end) if sec["body"] else (sec["head"].end,) * 2
            edits.append((start, end, render(doc, sec, item["blocks"]).encode("utf-8")))
            written.append(sid)
    xml = splice(doc.xml, edits)
    filled, missing_fields, protected_fields = [], [], []
    if fields:
        xml, filled, missing_fields, protected_fields = fill_fields(doc, xml, fields)
    write_docx(doc, xml, out, written, filled)
    new = Doc(out)
    sections = {}
    for sec in new.sections:
        sid = sec["id"]
        old = baseline.get(sid, {})
        # Stays assistant-owned only if nobody changed it since the assistant wrote it.
        untouched_ai = (old.get("owner") == "ai" and sid not in frozen and sid not in written
                        and sid not in protect and old.get("signature") == base_sig.get(sid))
        sections[sid] = {"owner": "ai" if sid in written or untouched_ai else "other",
                         "signature": signature(sec),
                         "ids": wanted[sid]["ids"] if sid in written else old.get("ids", [])}
    write_text_file(record, json.dumps(
        {"base": Path(base).name, "docx_sha256": file_sha256(out), "sections": sections}, indent=1))
    if frozen or unmatched:
        lines = [f"# Proposed text not applied to {out.name}", "",
                 "These sections were left exactly as they are. Copy what you want into Word.", ""]
        for sid in list(frozen) + unmatched:
            reason = frozen.get(sid, "no section with this heading in the document")
            lines += [f"## {sid}", f"_Not applied: {reason}._", "", wanted[sid]["raw"], ""]
        write_text_file(proposals, "\n".join(lines))
    return {"out": str(out), "written": written, "frozen": frozen, "unmatched": unmatched,
            "missing_sections": missing_sections, "missing_fields": missing_fields,
            "protected_fields": protected_fields, "proposals": str(proposals) if frozen or unmatched else None,
            "warnings": warnings,
            "complete": missing_sections == [] and not (unmatched or frozen or missing_fields or protected_fields),
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
    if comments:  # a read-only note, so feeding this text back to build adds no section
        lines.append("<!-- comments, read-only (not part of the FP):")
        lines += [f"- [{c['section']}] {c['author']}: {c['text']}".replace("-->", "- ->") for c in comments]
        lines.append("-->")
    return "\n".join(lines).rstrip() + "\n"


def check(path, template=None):
    problems = []
    doc = Doc(path)
    text = "\n".join(k.plain() for k in doc.body.kids)
    if TAG.search(text):
        problems.append("source tags left in the text")
    if "{{keep:" in text:
        problems.append("unplaced {{keep:N}} markers left in the text")
    missing = None  # not checked without a template
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
    return {"file": str(path), "problems": problems, "missing_sections": missing,
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
    if old.encode() not in parts["word/document.xml"]:
        raise ValueError(f"not in word/document.xml: {old}")
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
        r1 = build(d / "template.docx", d / "v1.md", d / "FP-v01.docx", mode="first", template=d / "template.docx",
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
    m = b.add_mutually_exclusive_group()
    m.add_argument("--first", action="store_true")
    m.add_argument("--existing", action="store_true")
    b.add_argument("--template")
    b.add_argument("--fields")
    b.add_argument("--protect", default="", help="comma-separated section ids to keep as they are")
    c = sub.add_parser("check")
    c.add_argument("docx")
    c.add_argument("--template")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "inspect":
            print(to_markdown(args.docx) if args.markdown else json.dumps(inspect(args.docx), indent=1))
        elif args.cmd == "build":
            fields = read_json(args.fields) if args.fields else None
            mode = "first" if args.first else "existing" if args.existing else "normal"
            protect = [s.strip() for s in args.protect.split(",") if s.strip()]
            result = build(args.base, args.content, args.out, mode, args.template, fields, protect)
            print(json.dumps(result, indent=1))
        elif args.cmd == "check":
            result = check(args.docx, args.template)
            print(json.dumps(result, indent=1))
            return 1 if result["problems"] else 0
        else:
            print(selftest())
    except (Refuse, KeyError, ValueError, zipfile.BadZipFile, expat.ExpatError, ET.ParseError, OSError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
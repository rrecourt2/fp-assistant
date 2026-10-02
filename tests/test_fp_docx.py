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
    r = fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), out, mode="first", template=tpl,
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
    fp_docx.build(tpl, write(tmp_path / "c1.md", FIRST), v1, mode="first", template=tpl)
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
    r = fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), tmp_path / "out.docx", mode="first", template=tpl)
    assert "market-risk" in r["frozen"]
    info = fp_docx.inspect(tmp_path / "out.docx")
    assert info["comments"][0]["section"] == "market-risk"
    assert info["comments"][0]["text"] == "Check the FX exposure"


def test_unknown_section_goes_to_proposals(tpl, tmp_path):
    r = fp_docx.build(tpl, write(tmp_path / "c.md", "## annex-9\nText\n"), tmp_path / "o.docx",
                      mode="first", template=tpl)
    assert r["unmatched"] == ["annex-9"] and r["proposals"]


def test_refuses_to_overwrite(tpl, tmp_path):
    out = tmp_path / "o.docx"
    out.write_bytes(b"x")
    with pytest.raises(fp_docx.Refuse):
        fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), out, mode="first", template=tpl)
    assert out.read_bytes() == b"x"


def test_fields_in_a_later_round_change_only_the_requested_cover_value(tpl, tmp_path):
    v1, v2 = tmp_path / "v1.docx", tmp_path / "v2.docx"
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, mode="first", template=tpl,
                  fields={"Borrower": "Cedar Foods", "Amount": "EUR 12m"})
    fp_docx.edit_text(v1, "Cedar Foods</w:t>", "Cedar Foods B.V.</w:t>")   # the officer's edit in Word
    r = fp_docx.build(v1, write(tmp_path / "c2.md", "## summary\nNew summary.\n"), v2, fields={"Amount": "EUR 15m"})
    cells = [c.text for t in docx.Document(v2).tables for row in t.rows for c in row.cells]
    assert "EUR 15m" in cells and "EUR 12m" not in cells
    assert "Cedar Foods B.V." in cells
    assert r["missing_fields"] == []


def test_signature_ignores_word_save_noise(tpl, tmp_path):
    v1 = tmp_path / "v1.docx"
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, mode="first", template=tpl)
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
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, mode="first", template=tpl)
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
    fp_docx.build(tpl, write(tmp_path / "c1.md", FIRST), v1, mode="first", template=tpl)
    fp_docx.edit_text(v1, "Approve.", "Approve, in the officer's words.")
    fp_docx.build(v1, write(tmp_path / "c2.md", "## summary\nNew summary.\n"), v2)
    r = fp_docx.build(v2, write(tmp_path / "c3.md", "## recommendation\nDecline.\n"), v3)
    assert "recommendation" in r["frozen"]
    assert "officer's words" in fp_docx.to_markdown(v3)


def test_reviewer_can_read_kept_tables_and_reusing_the_text_does_not_duplicate_them(tpl, tmp_path):
    v1, v2 = tmp_path / "v1.docx", tmp_path / "v2.docx"
    fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), v1, mode="first", template=tpl)
    md = fp_docx.to_markdown(v1)
    assert "FY2025 (template)" in md                     # the template's kept table is readable
    fp_docx.build(v1, write(tmp_path / "again.md", md), v2)
    assert len(docx.Document(v2).tables) == len(docx.Document(v1).tables)


def test_cover_fields_fill_only_unprotected_cover_cells(tpl, tmp_path):
    fp_docx.edit_text(tpl, "<w:r><w:t>[amount]</w:t></w:r>",
                      '<w:ins w:id="9" w:author="Officer" w:date="2026-10-01T09:00:00Z"><w:r><w:t>[amount]</w:t></w:r></w:ins>')
    r = fp_docx.build(tpl, write(tmp_path / "c.md", FIRST), tmp_path / "v1.docx", mode="first", template=tpl,
                      fields={"Borrower": "Cedar Foods", "Amount": "EUR 12m", "EUR m": "overwritten?"})
    cells = [c.text for t in docx.Document(tmp_path / "v1.docx").tables for row in t.rows for c in row.cells]
    assert "Cedar Foods" in cells                        # ordinary cover cell is filled
    assert "EUR 12m" not in cells                        # a cell with tracked changes is protected
    assert "FY2025 (template)" in cells and "overwritten?" not in cells   # tables inside sections are not cover fields
    assert sorted(r["missing_fields"]) == ["Amount", "EUR m"]


# ---------- build modes ----------

def test_first_build_needs_the_blank_template_itself(tpl, tmp_path):
    c = write(tmp_path / "c.md", FIRST)
    with pytest.raises(fp_docx.Refuse, match="--template"):
        fp_docx.build(tpl, c, tmp_path / "a.docx", mode="first")
    other = tmp_path / "other.docx"
    fp_docx.make_template(other, comment_on="market-risk")
    with pytest.raises(fp_docx.Refuse, match="identical"):
        fp_docx.build(other, c, tmp_path / "b.docx", mode="first", template=tpl)
    write(tmp_path / "template.sections.json", '{"sections": {}}')
    with pytest.raises(fp_docx.Refuse, match="assistant record"):
        fp_docx.build(tpl, c, tmp_path / "c.docx", mode="first", template=tpl)
    assert not any((tmp_path / f"{n}.docx").exists() for n in "abc")


def test_existing_refuses_a_record_and_a_normal_round_needs_one(tpl, tmp_path):
    c = write(tmp_path / "c.md", FIRST)
    v1 = tmp_path / "v1.docx"
    fp_docx.build(tpl, c, v1, mode="first", template=tpl)
    with pytest.raises(fp_docx.Refuse, match="normal round"):
        fp_docx.build(v1, c, tmp_path / "v2.docx", mode="existing")
    with pytest.raises(fp_docx.Refuse, match="--existing"):
        fp_docx.build(tpl, c, tmp_path / "v3.docx")


def test_existing_draft_rewrites_unprotected_sections_then_normal_rounds_follow_ownership(tmp_path):
    draft = tmp_path / "Officer-draft.docx"
    fp_docx.make_template(draft, comment_on="market-risk")
    fp_docx.edit_text(draft, '<w:r><w:t xml:space="preserve">[Summarise the proposal]</w:t></w:r>',
                      '<w:ins w:id="7" w:author="Officer" w:date="2026-10-01T09:00:00Z">'
                      "<w:r><w:t>Officer summary.</w:t></w:r></w:ins>")
    fp_docx.edit_text(draft, "[State the recommendation]", "Approve, in the officer's words.")
    before = draft.read_bytes()
    v1 = tmp_path / "FP-v01.docx"
    r = fp_docx.build(draft, write(tmp_path / "c.md", FIRST), v1, mode="existing", protect=["recommendation"])
    assert r["written"] == ["financial-analysis"]
    assert r["frozen"] == {"summary": "has comments or tracked changes",
                           "market-risk": "has comments or tracked changes",
                           "recommendation": "protected at the officer's request"}
    md = fp_docx.to_markdown(v1)
    assert "Revenue rose 20%." in md and "FY2025 (template)" in md        # rewritten; fixed table kept
    assert "Officer summary." in md and "officer's words" in md and "[Describe market risks]" in md
    proposals = (tmp_path / "FP-v01.proposals.md").read_text()
    assert "Approve." in proposals and "Milk prices rose." in proposals
    side = json.loads((tmp_path / "FP-v01.sections.json").read_text())["sections"]
    assert {k: v["owner"] for k, v in side.items()} == {
        "summary": "other", "financial-analysis": "ai", "market-risk": "other", "recommendation": "other"}
    assert draft.read_bytes() == before                                    # the officer's file is untouched
    r2 = fp_docx.build(v1, write(tmp_path / "c2.md", "## financial-analysis\nRevenue rose 25%.\n\n{{keep:1}}\n\n"
                                 "## recommendation\nDecline.\n"), tmp_path / "FP-v02.docx")
    assert r2["written"] == ["financial-analysis"]
    assert r2["frozen"] == {"recommendation": "not written by the assistant in the base version"}
    assert "Decline." in (tmp_path / "FP-v02.proposals.md").read_text()

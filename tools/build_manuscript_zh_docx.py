#!/usr/bin/env python3
"""Build Chinese manuscript Word (.docx) with TOC from docs/manuscript_zh_final.md."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, Cm, RGBColor

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "manuscript_zh_final.md"
OUT_DOCS = ROOT / "docs" / "manuscript_zh_final.docx"
DESKTOP = Path(r"C:\Users\Administrator\Desktop\FMR_IMA_Layer1_manuscript_zh_final.docx")
FIGS = {
    1: ROOT / "results/output/paper_figures/fig1_ima_ap_nonmonotonic_exploratory_planning_range.png",
    2: ROOT / "results/output/paper_figures/fig2_suture_vs_ap_reduction.png",
    3: ROOT / "results/output/paper_figures/fig3_jet_location.png",
    4: ROOT / "results/output/paper_figures/fig4_pareto_lcx_strain.png",
    5: ROOT / "results/output/paper_figures/fig5_dual_vs_single_suture.png",
}
EA_FONT = "宋体"
LATIN_FONT = "Times New Roman"


def set_run_font(run, size=11, bold=False, italic=False, east_asia=EA_FONT):
    run.bold = bold
    run.italic = italic
    run.font.name = LATIN_FONT
    run.font.size = Pt(size)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), LATIN_FONT)
    rFonts.set(qn("w:hAnsi"), LATIN_FONT)
    rFonts.set(qn("w:eastAsia"), east_asia)
    rFonts.set(qn("w:cs"), LATIN_FONT)


def configure_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = LATIN_FONT
    normal.font.size = Pt(11)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), LATIN_FONT)
    rFonts.set(qn("w:hAnsi"), LATIN_FONT)
    rFonts.set(qn("w:eastAsia"), EA_FONT)

    for style_name, size, space_before, space_after in (
        ("Heading 1", 14, 16, 8),
        ("Heading 2", 12, 12, 6),
        ("Heading 3", 11, 10, 4),
    ):
        style = doc.styles[style_name]
        style.font.name = LATIN_FONT
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(space_before)
        style.paragraph_format.space_after = Pt(space_after)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        style.paragraph_format.first_line_indent = Cm(0)
        rPr = style.element.get_or_add_rPr()
        rFonts = rPr.get_or_add_rFonts()
        rFonts.set(qn("w:ascii"), LATIN_FONT)
        rFonts.set(qn("w:hAnsi"), LATIN_FONT)
        rFonts.set(qn("w:eastAsia"), "黑体")


def add_para(
    doc,
    text,
    *,
    size=11,
    bold=False,
    italic=False,
    space_after=8,
    align=None,
    first_line=True,
    style=None,
):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if first_line and align is None and style is None:
        pf.first_line_indent = Cm(0.74)
    else:
        pf.first_line_indent = Cm(0)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def add_heading(doc, text, level=1):
    style = f"Heading {level}"
    p = doc.add_paragraph(text, style=style)
    # Re-apply east-asia font on runs
    for run in p.runs:
        set_run_font(run, size=14 if level == 1 else 12, bold=True, east_asia="黑体")
    return p


def add_toc_field(doc) -> None:
    """Insert a Word TOC field that updates on open / F9."""
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(8)
    run = title.add_run("目录")
    set_run_font(run, size=16, bold=True, east_asia="黑体")

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run()

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'

    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")

    # Visible placeholder until Word updates fields
    placeholder = OxmlElement("w:t")
    placeholder.text = "（请在 Microsoft Word 中右键目录并选择“更新域”以生成完整页码目录）"

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    r = run._r
    r.append(fld_begin)
    r.append(instr)
    r.append(fld_sep)
    r.append(placeholder)
    r.append(fld_end)

    # Also emit a static outline so the file is useful before Update Field
    add_para(doc, "静态大纲（与标题样式同步，供未更新域时阅读）", size=10, italic=True, first_line=False, space_after=4)


def add_static_toc_from_headings(doc, headings: list[tuple[int, str]]) -> None:
    for level, text in headings:
        indent = "　　" * (level - 1)
        add_para(doc, f"{indent}{text}", size=10 if level > 1 else 11, first_line=False, space_after=2)
    # page break after TOC
    p = doc.add_paragraph()
    run = p.add_run()
    run.add_break(WD_BREAK.PAGE)


def add_table_from_md(doc, header, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(header))
    table.style = "Table Grid"
    for j, h in enumerate(header):
        cell = table.rows[0].cells[j]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h.strip())
        set_run_font(run, size=9, bold=True)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            if j >= len(header):
                break
            cell = table.rows[i + 1].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(val.strip())
            set_run_font(run, size=9)
    doc.add_paragraph()


def parse_table(lines, start_idx):
    header = [c.strip() for c in lines[start_idx].strip("|").split("|")]
    rows = []
    i = start_idx + 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append([c.strip() for c in lines[i].strip("|").split("|")])
        i += 1
    return header, rows, i


def insert_figure(doc, fig_num, caption):
    path = FIGS.get(fig_num)
    if path and path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run()
        run.add_picture(str(path), width=Inches(5.8))
    add_para(doc, caption, size=10, italic=True, first_line=False, space_after=10)


def clean_inline(s: str) -> str:
    body = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
    body = re.sub(r"`([^`]*)`", r"\1", body)
    body = re.sub(r"\$([^$]+)\$", r"\1", body)
    body = body.replace("\\mathrm{", "").replace("\\text{", "").replace("}", "")
    return body


def collect_headings(lines: list[str]) -> list[tuple[int, str]]:
    out = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("### "):
            out.append((3, s[4:].strip()))
        elif s.startswith("## "):
            out.append((2, s[3:].strip()))
    return out


def build():
    text = MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    headings = collect_headings(lines)

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    configure_styles(doc)

    pending_fig_caption = {}
    for ln in lines:
        m = re.match(r"\*\*图 (\d+)\.\*\*\s*(.*)", ln.strip())
        if m:
            pending_fig_caption[int(m.group(1))] = f"图 {m.group(1)}. {m.group(2)}"

    # Title + meta before TOC
    i = 0
    title_done = False
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("# ") and not title_done:
            add_para(
                doc,
                s[2:].strip(),
                size=16,
                bold=True,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                first_line=False,
                space_after=8,
            )
            title_done = True
            i += 1
            continue
        if s.startswith("**短标题：**") or s.startswith("**文章类型：**") or s.startswith("**一句话主张：**") or s.startswith("**复现命令：**") or s.startswith("**验证层级：**"):
            add_para(doc, s.replace("**", ""), size=10, italic=True, first_line=False, space_after=4)
            i += 1
            continue
        if s == "---":
            i += 1
            break
        i += 1

    add_toc_field(doc)
    add_static_toc_from_headings(doc, headings)

    inserted_figs: set[int] = set()
    skip_fig_section = False

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if not s:
            i += 1
            continue

        if s == "---":
            i += 1
            continue

        if s.startswith("## 图注"):
            skip_fig_section = True
            i += 1
            continue

        if skip_fig_section and s.startswith("## "):
            skip_fig_section = False
            # fall through to process this heading
        elif skip_fig_section:
            i += 1
            continue

        if s.startswith("## "):
            add_heading(doc, s[3:].strip(), level=1)
            i += 1
            continue

        if s.startswith("### "):
            add_heading(doc, s[4:].strip(), level=2)
            i += 1
            continue

        if s.startswith("**关键词：**") or s.startswith("**关键词.**"):
            add_para(doc, s.replace("**", ""), size=11, italic=True, first_line=False)
            i += 1
            continue

        if s.startswith("**表 ") and ("**" in s[3:]):
            add_para(doc, s.replace("**", ""), size=10, bold=True, italic=True, first_line=False, space_after=4)
            i += 1
            continue

        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*-+", lines[i + 1].strip() or ""):
            header, rows, ni = parse_table(lines, i)
            add_table_from_md(doc, header, rows)
            i = ni
            continue

        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            add_para(doc, "\n".join(buf), size=9, first_line=False, space_after=8)
            continue

        if s.startswith("$$"):
            if s == "$$":
                i += 1
                buf = []
                while i < len(lines) and lines[i].strip() != "$$":
                    buf.append(lines[i].strip())
                    i += 1
                i += 1
                eq = clean_inline(" ".join(buf))
            else:
                eq = clean_inline(s.strip("$").strip())
                i += 1
            add_para(doc, eq, size=11, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=False)
            continue

        if s.startswith("**图 "):
            i += 1
            continue

        body = clean_inline(s)
        add_para(doc, body, size=11)

        for n in range(1, 6):
            if n in inserted_figs:
                continue
            if f"图 {n}" in body or f"图{n}" in body:
                cap = pending_fig_caption.get(n, f"图 {n}.")
                insert_figure(doc, n, cap)
                inserted_figs.add(n)

        i += 1

    for n in range(1, 6):
        if n not in inserted_figs and n in pending_fig_caption:
            insert_figure(doc, n, pending_fig_caption[n])
            inserted_figs.add(n)

    # Primary write to Desktop (C:), then copy into docs/ if space allows
    DESKTOP.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(DESKTOP))
    desktop_ok = DESKTOP.exists()
    docs_ok = False
    try:
        OUT_DOCS.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DESKTOP, OUT_DOCS)
        docs_ok = OUT_DOCS.exists()
    except OSError as exc:
        print("docs copy failed:", exc)

    print("Desktop:", DESKTOP, DESKTOP.stat().st_size if desktop_ok else 0)
    print("Docs:", OUT_DOCS, OUT_DOCS.stat().st_size if docs_ok else 0)
    print("Figures embedded:", sorted(inserted_figs))
    print("Headings for TOC:", len(headings))


if __name__ == "__main__":
    build()

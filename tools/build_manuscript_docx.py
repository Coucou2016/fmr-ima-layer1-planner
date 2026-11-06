#!/usr/bin/env python3
"""Build docs/manuscript_final.docx from manuscript_final.md + SciencePlots figures."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, Cm

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "manuscript_final.md"
OUT = ROOT / "docs" / "manuscript_final.docx"
DESKTOP = Path(r"C:\Users\Administrator\Desktop\FMR_IMA_Layer1_manuscript_final.docx")
FIGS = {
    1: ROOT / "results/output/paper_figures/fig1_ima_ap_nonmonotonic_exploratory_planning_range.png",
    2: ROOT / "results/output/paper_figures/fig2_suture_vs_ap_reduction.png",
    3: ROOT / "results/output/paper_figures/fig3_jet_location.png",
    4: ROOT / "results/output/paper_figures/fig4_pareto_lcx_strain.png",
    5: ROOT / "results/output/paper_figures/fig5_dual_vs_single_suture.png",
}


def set_run_font(run, size=11, bold=False, italic=False):
    run.bold = bold
    run.italic = italic
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:eastAsia"), "Times New Roman")


def add_para(doc, text, *, size=11, bold=False, italic=False, space_after=8, align=None, first_line=True):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if first_line and align is None:
        pf.first_line_indent = Cm(0.74)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def add_heading_custom(doc, text, level=1):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(14 if level == 1 else 10)
    pf.space_after = Pt(8)
    pf.first_line_indent = Cm(0)
    run = p.add_run(text)
    set_run_font(run, size=14 if level == 1 else 12, bold=True)
    return p


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
        run = p.add_run()
        run.add_picture(str(path), width=Inches(5.8))
    add_para(doc, caption, size=10, italic=True, first_line=False, space_after=12)


def build():
    text = MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    i = 0
    title_done = False
    pending_fig_caption = {}
    # Collect figure captions from later section
    for ln in lines:
        m = re.match(r"\*\*Figure (\d+)\.\*\*\s*(.*)", ln.strip())
        if m:
            pending_fig_caption[int(m.group(1))] = f"Figure {m.group(1)}. {m.group(2)}"

    inserted_figs = set()

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if not s:
            i += 1
            continue

        if s.startswith("# ") and not title_done:
            add_para(doc, s[2:].strip(), size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=False, space_after=6)
            title_done = True
            i += 1
            continue

        if s.startswith("**Short title.**") or s.startswith("**Article type.**") or s.startswith("**One-sentence argument.**"):
            add_para(doc, s.replace("**", ""), size=10, italic=True, first_line=False, space_after=4)
            i += 1
            continue

        if s == "---":
            i += 1
            continue

        if s.startswith("## "):
            add_heading_custom(doc, s[3:].strip(), level=1)
            i += 1
            continue

        if s.startswith("### "):
            add_heading_custom(doc, s[4:].strip(), level=2)
            i += 1
            continue

        if s.startswith("**Keywords.**"):
            add_para(doc, s.replace("**", ""), size=11, italic=True, first_line=False)
            i += 1
            continue

        if s.startswith("**Table ") and s.endswith("**"):
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

        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            add_para(doc, s.strip("$").strip(), size=11, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=False)
            i += 1
            continue

        if s == "$$":
            i += 1
            buf = []
            while i < len(lines) and lines[i].strip() != "$$":
                buf.append(lines[i].strip())
                i += 1
            i += 1
            add_para(doc, " ".join(buf), size=11, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_line=False)
            continue

        if s.startswith("**Figure "):
            # captions collected; skip duplicate at end if already inserted earlier via marker
            i += 1
            continue

        if s.startswith("## Table note") or s.startswith("## Figure captions"):
            # skip trailing meta sections already used
            break

        # Inline figure insertion after key result paragraphs
        body = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
        body = re.sub(r"`([^`]*)`", r"\1", body)
        body = re.sub(r"\$([^$]+)\$", r"\1", body)
        add_para(doc, body, size=11)

        # Insert figures after the sentences that first mention them
        for n in range(1, 6):
            if n in inserted_figs:
                continue
            if f"Figure {n}" in body or f"Fig. {n}" in body:
                cap = pending_fig_caption.get(n, f"Figure {n}.")
                insert_figure(doc, n, cap)
                inserted_figs.add(n)

        i += 1

    # Ensure remaining figures appear before references if not inserted
    for n in range(1, 6):
        if n not in inserted_figs and n in pending_fig_caption:
            insert_figure(doc, n, pending_fig_caption[n])
            inserted_figs.add(n)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    try:
        shutil.copy2(OUT, DESKTOP)
        desktop_ok = True
    except Exception as exc:  # noqa: BLE001
        desktop_ok = False
        print("Desktop copy failed:", exc)
    print("Wrote", OUT)
    print("Desktop copy:", desktop_ok, DESKTOP if desktop_ok else "")
    print("Figures embedded:", sorted(inserted_figs))


if __name__ == "__main__":
    build()

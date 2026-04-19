"""
Day 9: PDF report generator using ReportLab.

Generates a 3-page PDF from the final report dict produced by report_builder.py:
  Page 1 — Executive Summary (triage, stats, brief, documents)
  Page 2 — Conflicts & Action Plan
  Page 3 — Full Rule Results (grouped by category, FAIL first)
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── brand colours ──────────────────────────────────────────────────────────────
_BG          = colors.HexColor("#ffffff")
_BG_SEC      = colors.HexColor("#f7f7f5")
_BG_TER      = colors.HexColor("#f0efe9")
_TEXT_PRI    = colors.HexColor("#1a1a18")
_TEXT_SEC    = colors.HexColor("#5f5e5a")
_TEXT_TER    = colors.HexColor("#888780")
_FAIL_BG     = colors.HexColor("#FCEBEB")
_FAIL_TXT    = colors.HexColor("#A32D2D")
_WARN_BG     = colors.HexColor("#FAEEDA")
_WARN_TXT    = colors.HexColor("#854F0B")
_PASS_BG     = colors.HexColor("#EAF3DE")
_PASS_TXT    = colors.HexColor("#3B6D11")
_BORDER      = colors.HexColor("#e0e0db")

_PAGE_W, _PAGE_H = letter
_MARGIN = 0.65 * inch


def _triage_colors(overall: str) -> tuple[colors.HexColor, colors.HexColor]:
    """Return (bg, text) colours for a triage badge."""
    return {
        "FAIL":    (_FAIL_BG, _FAIL_TXT),
        "WARNING": (_WARN_BG, _WARN_TXT),
        "PASS":    (_PASS_BG, _PASS_TXT),
    }.get(overall.upper(), (_BG_SEC, _TEXT_PRI))


def _status_colors(status: str) -> tuple[colors.HexColor, colors.HexColor]:
    return {
        "FAIL":    (_FAIL_BG, _FAIL_TXT),
        "WARNING": (_WARN_BG, _WARN_TXT),
        "PASS":    (_PASS_BG, _PASS_TXT),
        "SKIP":    (_BG_SEC,  _TEXT_TER),
    }.get(status.upper(), (_BG_SEC, _TEXT_TER))


# ── style helpers ──────────────────────────────────────────────────────────────

def _styles():
    base = getSampleStyleSheet()
    return {
        "logo": ParagraphStyle("logo", fontName="Helvetica-Bold", fontSize=13,
                               textColor=_TEXT_PRI, letterSpacing=2, leading=16),
        "meta": ParagraphStyle("meta", fontName="Helvetica", fontSize=8,
                               textColor=_TEXT_TER, leading=10),
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18,
                             textColor=_TEXT_PRI, leading=22, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11,
                             textColor=_TEXT_PRI, leading=14, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9,
                               textColor=_TEXT_SEC, leading=13),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9,
                                 textColor=_TEXT_SEC, leading=13, leftIndent=12,
                                 bulletIndent=0, bulletText="•"),
        "stat_label": ParagraphStyle("stat_label", fontName="Helvetica-Bold", fontSize=8,
                                     textColor=_TEXT_TER, leading=10, alignment=TA_CENTER),
        "stat_val": ParagraphStyle("stat_val", fontName="Helvetica-Bold", fontSize=20,
                                   textColor=_TEXT_PRI, leading=24, alignment=TA_CENTER),
        "stat_val_fail": ParagraphStyle("stat_val_fail", fontName="Helvetica-Bold", fontSize=20,
                                        textColor=_FAIL_TXT, leading=24, alignment=TA_CENTER),
        "stat_val_warn": ParagraphStyle("stat_val_warn", fontName="Helvetica-Bold", fontSize=20,
                                        textColor=_WARN_TXT, leading=24, alignment=TA_CENTER),
        "triage_lbl": ParagraphStyle("triage_lbl", fontName="Helvetica-Bold", fontSize=13,
                                     alignment=TA_CENTER, leading=16),
        "tbl_hdr": ParagraphStyle("tbl_hdr", fontName="Helvetica-Bold", fontSize=8,
                                  textColor=_TEXT_SEC, leading=10),
        "tbl_cell": ParagraphStyle("tbl_cell", fontName="Helvetica", fontSize=8,
                                   textColor=_TEXT_SEC, leading=11, wordWrap="LTR"),
        "tbl_cell_bold": ParagraphStyle("tbl_cell_bold", fontName="Helvetica-Bold", fontSize=8,
                                        textColor=_TEXT_PRI, leading=11),
        "caption": ParagraphStyle("caption", fontName="Helvetica", fontSize=8,
                                  textColor=_TEXT_TER, leading=10),
    }


# ── page header / footer ───────────────────────────────────────────────────────

def _draw_page_frame(canvas, doc):
    canvas.saveState()
    # Top rule
    canvas.setStrokeColor(_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(_MARGIN, _PAGE_H - _MARGIN * 0.7,
                _PAGE_W - _MARGIN, _PAGE_H - _MARGIN * 0.7)
    # Logo
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(_TEXT_PRI)
    canvas.drawString(_MARGIN, _PAGE_H - _MARGIN * 0.55, "CLOSECHECK")
    # Right: page number
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_TEXT_TER)
    canvas.drawRightString(_PAGE_W - _MARGIN, _PAGE_H - _MARGIN * 0.55,
                           f"Page {doc.page}")
    # Bottom rule + footer
    canvas.line(_MARGIN, _MARGIN * 0.8, _PAGE_W - _MARGIN, _MARGIN * 0.8)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_TEXT_TER)
    canvas.drawString(_MARGIN, _MARGIN * 0.5,
                      "CloseCheck — AI Pre-Close File Validator  |  Confidential")
    canvas.drawRightString(_PAGE_W - _MARGIN, _MARGIN * 0.5,
                           datetime.utcnow().strftime("%b %d, %Y"))
    canvas.restoreState()


# ── Page 1: Executive Summary ──────────────────────────────────────────────────

def _page1(report: dict, job_id: str, s: dict) -> list:
    overall  = report.get("overall", "UNKNOWN")
    summary  = report.get("summary", {})
    brief    = report.get("executive_brief", [])
    docs     = report.get("documents", [])

    triage_label = {"FAIL": "Blocked", "WARNING": "Needs Review", "PASS": "Ready to Close"}.get(
        overall.upper(), overall)
    bg_col, txt_col = _triage_colors(overall)

    story = []
    story.append(Spacer(1, 0.15 * inch))

    # Job meta line
    story.append(Paragraph(
        f"Job&nbsp;{job_id[:8].upper()} &nbsp;·&nbsp; "
        f"{datetime.utcnow().strftime('%B %d, %Y')}",
        s["meta"]))
    story.append(Spacer(1, 0.18 * inch))

    # Triage badge (wide table cell)
    badge_style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg_col),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [20, 20, 20, 20]),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ])
    triage_para = Paragraph(triage_label,
                            ParagraphStyle("triage_p", fontName="Helvetica-Bold",
                                           fontSize=14, textColor=txt_col,
                                           alignment=TA_CENTER, leading=18))
    badge_tbl = Table([[triage_para]], colWidths=[2.4 * inch])
    badge_tbl.setStyle(badge_style)
    # Center the badge
    wrapper = Table([[badge_tbl]], colWidths=[_PAGE_W - 2 * _MARGIN])
    wrapper.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(wrapper)
    story.append(Spacer(1, 0.22 * inch))

    # Summary stats grid (4 boxes)
    total  = summary.get("total_rules", 0)
    passed = summary.get("passed", 0)
    warns  = summary.get("warnings", 0)
    failed = summary.get("failed", 0)

    def _stat_cell(label, value, val_style_key):
        return [Paragraph(label.upper(), s["stat_label"]),
                Paragraph(str(value), s[val_style_key])]

    stat_data = [[
        _stat_cell("Total Rules", total,  "stat_val"),
        _stat_cell("Passed",      passed, "stat_val"),
        _stat_cell("Warnings",    warns,  "stat_val_warn" if warns else "stat_val"),
        _stat_cell("Failed",      failed, "stat_val_fail" if failed else "stat_val"),
    ]]
    col_w = (_PAGE_W - 2 * _MARGIN) / 4
    stat_tbl = Table(stat_data, colWidths=[col_w] * 4, rowHeights=[None])
    stat_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _BG_SEC),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEAFTER",     (0, 0), (2, -1), 0.5, _BORDER),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [8, 8, 8, 8]),
    ]))
    story.append(stat_tbl)
    story.append(Spacer(1, 0.22 * inch))

    # Executive brief
    story.append(Paragraph("Executive Brief", s["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=6))
    if brief:
        for bullet in brief:
            story.append(Paragraph(str(bullet), s["bullet"]))
            story.append(Spacer(1, 3))
    else:
        story.append(Paragraph("No issues detected.", s["body"]))
    story.append(Spacer(1, 0.18 * inch))

    # Documents processed
    story.append(Paragraph("Documents Processed", s["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=6))
    if docs:
        hdr = [Paragraph(h, s["tbl_hdr"]) for h in ["Filename", "Document Type", "Confidence", "Status"]]
        rows = [hdr]
        col_w_d = [(_PAGE_W - 2 * _MARGIN) * r for r in [0.38, 0.28, 0.16, 0.18]]
        for d in docs:
            st = d.get("status", "ok").upper()
            st_bg, st_txt = _status_colors("FAIL" if st == "FAIL" else "WARNING" if st in ("WARN", "WARNING") else "PASS")
            rows.append([
                Paragraph(str(d.get("filename", "")), s["tbl_cell"]),
                Paragraph(str(d.get("document_type", "")).replace("_", " ").title(), s["tbl_cell"]),
                Paragraph(f"{float(d.get('confidence', 0)) * 100:.0f}%", s["tbl_cell"]),
                Paragraph(st, ParagraphStyle("st", fontName="Helvetica-Bold", fontSize=8,
                                             textColor=st_txt, leading=11)),
            ])
        doc_tbl = Table(rows, colWidths=col_w_d)
        ts = [
            ("BACKGROUND",    (0, 0), (-1, 0), _BG_SEC),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("GRID",          (0, 0), (-1, -1), 0.5, _BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]
        # Colour status column cells
        for i, d in enumerate(docs, start=1):
            st = d.get("status", "ok").upper()
            bg, _ = _status_colors("FAIL" if st == "FAIL" else "WARNING" if st in ("WARN", "WARNING") else "PASS")
            ts.append(("BACKGROUND", (3, i), (3, i), bg))
        doc_tbl.setStyle(TableStyle(ts))
        story.append(doc_tbl)
    else:
        story.append(Paragraph("No documents found.", s["body"]))

    return story


# ── Page 2: Conflicts & Action Plan ───────────────────────────────────────────

def _page2(report: dict, s: dict) -> list:
    conflicts   = report.get("conflicts", [])
    action_plan = report.get("action_plan", [])
    story = []
    story.append(Spacer(1, 0.15 * inch))

    # Conflicts table
    story.append(Paragraph("Conflicts Detected", s["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=6))

    if conflicts:
        hdr = [Paragraph(h, s["tbl_hdr"]) for h in
               ["Rule ID", "Type", "Sev.", "Doc A / Value A", "Doc B / Value B", "Message"]]
        rows = [hdr]
        cw = [(_PAGE_W - 2 * _MARGIN) * r for r in [0.09, 0.14, 0.07, 0.22, 0.22, 0.26]]
        for c in conflicts:
            sev  = str(c.get("severity", "")).upper()
            _, txt = _triage_colors(sev)
            rows.append([
                Paragraph(str(c.get("rule_id", "")), s["tbl_cell_bold"]),
                Paragraph(str(c.get("type", ""))[:40], s["tbl_cell"]),
                Paragraph(sev, ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=8,
                                              textColor=txt, leading=11)),
                Paragraph(
                    f"<b>{c.get('doc_a') or '—'}</b><br/>{c.get('value_a') or '—'}",
                    s["tbl_cell"]),
                Paragraph(
                    f"<b>{c.get('doc_b') or '—'}</b><br/>{c.get('value_b') or '—'}",
                    s["tbl_cell"]),
                Paragraph(str(c.get("message", ""))[:80], s["tbl_cell"]),
            ])

        ts = [
            ("BACKGROUND",    (0, 0), (-1, 0), _BG_SEC),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("GRID",          (0, 0), (-1, -1), 0.5, _BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]
        for i, c in enumerate(conflicts, start=1):
            sev = str(c.get("severity", "")).upper()
            bg, _ = _status_colors(sev)
            ts.append(("BACKGROUND", (0, i), (-1, i), bg))
        tbl = Table(rows, colWidths=cw)
        tbl.setStyle(TableStyle(ts))
        story.append(tbl)
    else:
        story.append(Paragraph("No conflicts detected.", s["body"]))

    story.append(Spacer(1, 0.22 * inch))

    # Action plan
    story.append(Paragraph("Action Plan", s["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=6))

    if action_plan:
        urgency_label = {"now": "Do now", "today": "Today", "soon": "Soon"}
        urgency_colors = {
            "now":   (_FAIL_BG, _FAIL_TXT),
            "today": (_WARN_BG, _WARN_TXT),
            "soon":  (_BG_SEC,  _TEXT_SEC),
        }
        hdr = [Paragraph(h, s["tbl_hdr"]) for h in
               ["#", "Title", "Description", "Urgency", "Owner", "Blocker"]]
        rows = [hdr]
        cw = [(_PAGE_W - 2 * _MARGIN) * r for r in [0.05, 0.22, 0.38, 0.12, 0.13, 0.10]]
        for i, item in enumerate(action_plan, start=1):
            urg = str(item.get("urgency", "soon")).lower()
            urg_bg, urg_txt = urgency_colors.get(urg, (_BG_SEC, _TEXT_SEC))
            is_blocker = item.get("is_blocker", False)
            rows.append([
                Paragraph(str(i), s["tbl_cell_bold"]),
                Paragraph(str(item.get("title", ""))[:50], s["tbl_cell_bold"]),
                Paragraph(str(item.get("description", ""))[:120], s["tbl_cell"]),
                Paragraph(urgency_label.get(urg, urg.title()),
                          ParagraphStyle("ul", fontName="Helvetica-Bold", fontSize=8,
                                         textColor=urg_txt, leading=11)),
                Paragraph(str(item.get("owner", "")).title()[:20], s["tbl_cell"]),
                Paragraph("YES" if is_blocker else "—",
                          ParagraphStyle("bl", fontName="Helvetica-Bold", fontSize=8,
                                         textColor=_FAIL_TXT if is_blocker else _TEXT_TER,
                                         leading=11)),
            ])
        ts = [
            ("BACKGROUND",    (0, 0), (-1, 0), _BG_SEC),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("GRID",          (0, 0), (-1, -1), 0.5, _BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]
        tbl = Table(rows, colWidths=cw)
        tbl.setStyle(TableStyle(ts))
        story.append(tbl)
    else:
        story.append(Paragraph("No action items generated.", s["body"]))

    return story


# ── Page 3: Full Rule Results ──────────────────────────────────────────────────

def _page3(report: dict, s: dict) -> list:
    results = report.get("results", [])
    story = []
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Full Validation Results", s["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=6))

    if not results:
        story.append(Paragraph("No rule results available.", s["body"]))
        return story

    # Group by category, FAIL first within each group
    categories: dict[str, list] = {}
    for r in results:
        cat = str(r.get("category", "other"))
        categories.setdefault(cat, []).append(r)

    # Sort within each category: FAIL → WARNING → PASS → SKIP
    severity_order = {"FAIL": 0, "WARNING": 1, "PASS": 2, "SKIP": 3}
    for cat in categories:
        categories[cat].sort(key=lambda r: severity_order.get(r.get("status", "").upper(), 4))

    cw = [(_PAGE_W - 2 * _MARGIN) * r for r in [0.11, 0.34, 0.11, 0.44]]

    for cat, rules in categories.items():
        story.append(Spacer(1, 6))
        story.append(Paragraph(cat.replace("_", " ").upper(), s["caption"]))
        story.append(Spacer(1, 3))

        hdr = [Paragraph(h, s["tbl_hdr"]) for h in
               ["Rule ID", "Description", "Status", "Detail"]]
        rows = [hdr]
        for r in rules:
            st = str(r.get("status", "")).upper()
            _, txt_col = _status_colors(st)
            rows.append([
                Paragraph(str(r.get("rule_id", "")), s["tbl_cell_bold"]),
                Paragraph(str(r.get("description", ""))[:80], s["tbl_cell"]),
                Paragraph(st, ParagraphStyle("st2", fontName="Helvetica-Bold", fontSize=8,
                                             textColor=txt_col, leading=11)),
                Paragraph(str(r.get("detail") or "—")[:120], s["tbl_cell"]),
            ])
        ts = [
            ("BACKGROUND",    (0, 0), (-1, 0), _BG_SEC),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("GRID",          (0, 0), (-1, -1), 0.5, _BORDER),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]
        for i, r in enumerate(rules, start=1):
            bg, _ = _status_colors(str(r.get("status", "")).upper())
            ts.append(("BACKGROUND", (2, i), (2, i), bg))
        tbl = Table(rows, colWidths=cw)
        tbl.setStyle(TableStyle(ts))
        story.append(tbl)

    return story


# ── public API ─────────────────────────────────────────────────────────────────

def generate_pdf(report: dict, output_path: str, job_id: Optional[str] = None) -> str:
    """
    Render *report* dict as a multi-page PDF and write it to *output_path*.
    Returns the resolved absolute path string.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    s = _styles()

    doc = BaseDocTemplate(
        str(out),
        pagesize=letter,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_MARGIN * 1.4,
        bottomMargin=_MARGIN * 1.2,
        title="CloseCheck Validation Report",
        author="CloseCheck",
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="main",
    )
    template = PageTemplate(id="main", frames=[frame], onPage=_draw_page_frame)
    doc.addPageTemplates([template])

    job_id = job_id or out.stem
    story = (
        _page1(report, job_id, s)
        + [PageBreak()]
        + _page2(report, s)
        + [PageBreak()]
        + _page3(report, s)
    )

    doc.build(story)
    logger.info("PDF written to %s", out)
    return str(out)

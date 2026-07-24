"""ReportLab PDF rendering for AI Shield security reports.

Consumes the dictionary produced by :func:`app.reports.builder.build_json_report`
— no duplicated scoring or findings extraction.
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.assessment_sdk.severity import Severity
from app.reports.builder import is_architecture_finding
from app.services.findings import FindingView


def _s(value: Any, default: str = "—") -> str:
    if value is None or value == "":
        return default
    return str(value)


def _escape(text: Any) -> str:
    value = _s(text, "")
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _coerce_severity(value: Any) -> Severity:
    try:
        return Severity(str(value or "info").lower())
    except ValueError:
        return Severity.INFO


def _finding_views_from_document(document: dict[str, Any]) -> list[FindingView]:
    """Rehydrate FindingView objects only for classification helpers (no re-scoring)."""
    items = ((document.get("findings") or {}).get("items")) or []
    views: list[FindingView] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        views.append(
            FindingView(
                id=str(item.get("id") or ""),
                title=str(item.get("title") or "Finding"),
                description=str(item.get("description") or ""),
                severity=_coerce_severity(item.get("severity")),
                category=item.get("category"),
                confidence=item.get("confidence"),
                recommendation=item.get("recommendation"),
                evidence=dict(item.get("evidence") or {})
                if isinstance(item.get("evidence"), dict)
                else {},
                tags=list(item.get("tags") or []),
                assessment_id=item.get("assessment_id"),
                assessment_key=item.get("assessment_key"),
                assessment_name=item.get("assessment_name"),
                scan_id=item.get("scan_id"),
                project_id=item.get("project_id"),
            )
        )
    return views


def render_report_pdf(document: dict[str, Any]) -> bytes:
    """Render a PDF from an existing JSON report document."""
    buffer = BytesIO()
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=_s((document.get("report") or {}).get("title"), "AI Shield Security Report"),
        author="AI Shield",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor("#0f172a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHead",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#0f172a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyMuted",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetaLabel",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="FindingTitle",
            parent=styles["BodyText"],
            fontSize=10,
            leading=13,
            spaceBefore=4,
            textColor=colors.HexColor("#0f172a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallCenter",
            parent=styles["Normal"],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontSize=8,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#64748b"),
        )
    )

    story: list[Any] = []
    report_meta = document.get("report") or {}
    executive = document.get("executive_summary") or {}
    project = document.get("project") or {}
    scan = document.get("scan") or {}
    architecture = document.get("architecture") or {}
    findings_block = document.get("findings") or {}
    recommendations = document.get("recommendations") or []
    evidence_rows = document.get("evidence") or []

    # --- Cover / branding ---
    story.append(Paragraph("AI SHIELD", styles["CoverTitle"]))
    story.append(Paragraph("[Logo Placeholder]", styles["SmallCenter"]))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            _escape(report_meta.get("title") or "Security Assessment Report"),
            styles["SmallCenter"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12)
    )

    # --- Executive summary ---
    story.append(Paragraph("Executive Summary", styles["SectionHead"]))
    summary_text = report_meta.get("summary_text") or (
        f"Security posture {_escape(executive.get('overall_security_posture'))} "
        f"(score {_escape(executive.get('overall_security_score'))}/100). "
        f"Risk {_escape(executive.get('risk_level'))} "
        f"({_escape(executive.get('overall_risk_score'))}/100). "
        f"{_escape(executive.get('total_findings'))} finding(s)."
    )
    story.append(Paragraph(_escape(summary_text), styles["BodyMuted"]))

    # --- Scan metadata ---
    story.append(Paragraph("Scan Metadata", styles["SectionHead"]))
    arch_list = architecture.get("affected_architectures") or []
    architecture_label = ", ".join(str(a) for a in arch_list) if arch_list else _s(
        project.get("application_type"), "universal"
    )
    timestamp = (
        scan.get("completed_at")
        or scan.get("started_at")
        or report_meta.get("created_at")
        or generated_at
    )
    meta_table = Table(
        [
            [
                Paragraph("<b>Project</b>", styles["MetaLabel"]),
                Paragraph(_escape(project.get("name")), styles["BodyMuted"]),
                Paragraph("<b>Architecture</b>", styles["MetaLabel"]),
                Paragraph(_escape(architecture_label), styles["BodyMuted"]),
            ],
            [
                Paragraph("<b>Scan ID</b>", styles["MetaLabel"]),
                Paragraph(_escape(scan.get("id")), styles["BodyMuted"]),
                Paragraph("<b>Timestamp</b>", styles["MetaLabel"]),
                Paragraph(_escape(timestamp), styles["BodyMuted"]),
            ],
            [
                Paragraph("<b>Profile</b>", styles["MetaLabel"]),
                Paragraph(_escape(scan.get("profile")), styles["BodyMuted"]),
                Paragraph("<b>Status</b>", styles["MetaLabel"]),
                Paragraph(_escape(scan.get("status")), styles["BodyMuted"]),
            ],
        ],
        colWidths=[1.1 * inch, 2.2 * inch, 1.2 * inch, 2.2 * inch],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta_table)

    # --- Risk / severity ---
    story.append(Paragraph("Overall Risk Score and Severity", styles["SectionHead"]))
    risk_table = Table(
        [
            ["Overall Risk Score", _s(executive.get("overall_risk_score"))],
            ["Security Score", _s(executive.get("overall_security_score"))],
            ["Overall Severity", _s(executive.get("overall_severity")).upper()],
            ["Risk Level", _s(executive.get("risk_level"))],
            ["Critical Findings", _s(executive.get("critical_findings"), "0")],
            ["High Findings", _s(executive.get("high_findings"), "0")],
            ["Medium Findings", _s(executive.get("medium_findings"), "0")],
            ["Low Findings", _s(executive.get("low_findings"), "0")],
        ],
        colWidths=[2.4 * inch, 4.3 * inch],
    )
    risk_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(risk_table)

    # Split findings using existing architecture classifier
    views = _finding_views_from_document(document)
    if views:
        universal = [f for f in views if not is_architecture_finding(f)]
        architecture_findings = [f for f in views if is_architecture_finding(f)]
    else:
        # Fallback to raw items when views cannot be built
        raw_items = findings_block.get("items") or []
        universal = []
        architecture_findings = []
        for item in raw_items:
            tags = {str(t).lower() for t in (item.get("tags") or [])}
            if "architecture" in tags:
                architecture_findings.append(item)
            else:
                universal.append(item)

    def _append_findings(title: str, items: list[Any]) -> None:
        story.append(Paragraph(title, styles["SectionHead"]))
        if not items:
            story.append(Paragraph("No findings in this category.", styles["BodyMuted"]))
            return
        for item in items:
            if isinstance(item, FindingView):
                data = item.to_dict()
            else:
                data = item if isinstance(item, dict) else {}
            block = [
                Paragraph(
                    f"<b>{_escape(data.get('title'))}</b> · "
                    f"{_escape(data.get('severity')).upper()} · "
                    f"{_escape(data.get('category') or data.get('assessment_key'))}",
                    styles["FindingTitle"],
                ),
                Paragraph(
                    _escape(data.get("description") or "No description."),
                    styles["BodyMuted"],
                ),
            ]
            rec = data.get("recommendation")
            if rec:
                block.append(
                    Paragraph(f"<b>Recommendation:</b> {_escape(rec)}", styles["BodyMuted"])
                )
            story.append(KeepTogether(block))
            story.append(Spacer(1, 4))

    _append_findings("Universal Assessment Findings", universal)
    _append_findings("Architecture Assessment Findings", architecture_findings)

    # --- Recommendations ---
    story.append(Paragraph("Recommendations", styles["SectionHead"]))
    if not recommendations:
        story.append(Paragraph("No recommendations recorded.", styles["BodyMuted"]))
    else:
        bullets: list[Any] = []
        for rec in recommendations:
            if not isinstance(rec, dict):
                continue
            text = (
                f"<b>{_escape(rec.get('title') or 'Recommendation')}</b> "
                f"[{_escape(rec.get('priority')).upper()}] — "
                f"{_escape(rec.get('description'))}"
            )
            bullets.append(ListItem(Paragraph(text, styles["BodyMuted"]), leftIndent=8))
        if bullets:
            story.append(ListFlowable(bullets, bulletType="bullet", start="•"))

    # --- Evidence ---
    story.append(Paragraph("Evidence", styles["SectionHead"]))
    if not evidence_rows:
        # Fall back to per-finding evidence embedded in findings items
        embedded = []
        for f in universal + architecture_findings:
            if isinstance(f, FindingView):
                evidence = f.evidence
                finding_id = f.id
                assessment_key = f.assessment_key
            elif isinstance(f, dict):
                evidence = f.get("evidence")
                finding_id = f.get("id")
                assessment_key = f.get("assessment_key")
            else:
                continue
            if not evidence:
                continue
            embedded.append(
                {
                    "finding_id": finding_id,
                    "assessment_key": assessment_key,
                    "evidence": evidence,
                }
            )
        evidence_rows = embedded

    if not evidence_rows:
        story.append(Paragraph("No evidence attached.", styles["BodyMuted"]))
    else:
        for row in evidence_rows:
            if not isinstance(row, dict):
                continue
            ev = row.get("evidence")
            preview = _escape(ev)[:500] if not isinstance(ev, dict) else _escape(
                ev.get("prompt") or ev.get("completion") or ev.get("extra") or ev
            )[:500]
            story.append(
                Paragraph(
                    f"<b>Finding</b> {_escape(row.get('finding_id'))} · "
                    f"<b>Assessment</b> {_escape(row.get('assessment_key'))}",
                    styles["FindingTitle"],
                )
            )
            story.append(Paragraph(preview or "—", styles["BodyMuted"]))
            story.append(Spacer(1, 4))

    def _on_page(canvas: Any, doc_template: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(
            0.75 * inch,
            0.4 * inch,
            f"Generated {generated_at}",
        )
        canvas.drawRightString(
            A4[0] - 0.75 * inch,
            0.4 * inch,
            f"Page {doc_template.page}",
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buffer.getvalue()

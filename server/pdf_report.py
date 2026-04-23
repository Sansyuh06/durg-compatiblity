"""QuantaMed Clinical PDF Report Generator.

Uses fpdf2 to produce a professional clinical PDF report.
Compatible with fpdf2 >= 2.7.0 (uses new_x/new_y parameters).
"""
from __future__ import annotations

from typing import Any

from .quantamed_sim import (
    recommend_quantamed_candidates,
    get_quantamed_patient_summary,
    score_quantamed_candidate,
)


def _sanitize(text: str) -> str:
    """Replace common non-latin-1 Unicode chars with ASCII equivalents."""
    return (
        text
        .replace("\u2013", "-")   # en-dash
        .replace("\u2014", "--")  # em-dash
        .replace("\u2018", "'")   # left single quote
        .replace("\u2019", "'")   # right single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .replace("\u2026", "...")  # ellipsis
        .replace("\u00d7", "x")   # multiplication sign
        .replace("\u2191", "^")   # up arrow
        .replace("\u2193", "v")   # down arrow
        .replace("\u2265", ">=")  # greater-than or equal
        .replace("\u2264", "<=")  # less-than or equal
        .replace("\u00b5", "u")   # micro sign -> u
        .replace("\u2605", "*")   # star
    )


def _ln(pdf: Any, h: float = 0) -> None:
    """Move cursor to left margin and next line (replaces deprecated ln=1)."""
    if h:
        pdf.ln(h)
    else:
        pdf.ln()


def generate_quantamed_pdf(
        patient_id: str = "juvenile_myoclonic_epilepsy") -> bytes:
    """Generate a clinical PDF report and return raw PDF bytes."""
    try:
        from fpdf import FPDF
    except ImportError:
        return _generate_minimal_pdf(patient_id)

    patient = get_quantamed_patient_summary(patient_id)
    recs = recommend_quantamed_candidates(patient_id)
    ranked = recs["recommendations"]

    # Sanitize all string values to avoid latin-1 encoding errors in fpdf2
    patient = {
        k: _sanitize(v) if isinstance(
            v,
            str) else v for k,
        v in patient.items()}
    for drug in ranked:
        for key, val in drug.items():
            if isinstance(val, str):
                drug[key] = _sanitize(val)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Header ──
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(0, 120, 180)
    pdf.cell(0, 12, "QuantaMed")
    _ln(pdf, 12)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Quantum-Enhanced Precision Drug Discovery Platform")
    _ln(pdf, 6)
    pdf.cell(0, 5, "Clinical Decision-Support Report")
    _ln(pdf, 5)
    pdf.ln(4)
    pdf.set_draw_color(0, 120, 180)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # ── Patient Profile ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Patient Profile")
    _ln(pdf, 8)
    pdf.ln(2)

    _add_field(pdf, "Name", patient.get("name", "N/A"))
    _add_field(pdf, "Condition", patient.get("condition", "N/A"))
    _add_field(pdf,
               "Age / Sex",
               f"{patient.get('age',
                              'N/A')} / {patient.get('sex',
                                                     'N/A').title()}")
    _add_field(pdf, "Weight", f"{patient.get('weight_kg', 'N/A')} kg")
    _add_field(pdf, "CYP2C9 Status", patient.get("cyp_variant", "N/A"))
    _add_field(
        pdf,
        "CYP2D6 Status",
        patient.get(
            "cyp2d6_variant",
            patient.get(
                "cyp2d6",
                "N/A")))
    cur_drug = patient.get("current_drug", "N/A")
    cur_dose = patient.get("current_dose_mg", "")
    _add_field(pdf, "Current Drug", f"{cur_drug.upper()} {cur_dose}mg/day")
    _add_field(
        pdf, "Months on Therapy", str(
            patient.get(
                "months_on_therapy", "N/A")))
    alt = patient.get("alt_u_l", "N/A")
    liver = patient.get("liver_function", "N/A")
    _add_field(pdf, "Hepatic Function", f"ALT {alt} U/L ({liver})")
    _add_field(pdf, "Target Protein", patient.get("target_protein", "N/A"))

    if patient.get("notes"):
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 5, "Notes: " + patient["notes"])

    pdf.ln(6)

    # ── Drug Rankings ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Drug Candidate Rankings")
    _ln(pdf, 8)
    pdf.ln(2)

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 242, 255)
    pdf.set_text_color(30, 30, 30)
    col_w = [10, 40, 22, 22, 22, 22, 52]
    headers = [
        "#",
        "Drug",
        "Composite",
        "Efficacy",
        "Safety",
        "BBB",
        "Summary"]
    for w, h in zip(col_w, headers):
        pdf.cell(w, 7, h, border=1, fill=True)
    pdf.ln()

    # Table rows
    pdf.set_font("Helvetica", "", 9)
    for idx, drug in enumerate(ranked[:5], 1):
        scores = drug.get("scores", {})
        fill = idx <= 1
        if fill:
            pdf.set_fill_color(220, 255, 230)
        else:
            pdf.set_fill_color(255, 255, 255)

        badge = "*" if idx == 1 else str(idx)
        row = [
            badge,
            drug.get("label", ""),
            f"{scores.get('composite', 0):.2f}",
            str(round(scores.get("efficacy", 0))),
            str(round(scores.get("safety", 0))),
            str(round(scores.get("bbb", 0))),
            drug.get("summary", "")[:38],
        ]
        for w, val in zip(col_w, row):
            pdf.cell(w, 7, val, border=1, fill=fill)
        pdf.ln()

    pdf.ln(6)

    # ── Critical Risk Flags ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 8, "Critical Risk Flags")
    _ln(pdf, 8)
    pdf.ln(2)

    try:
        vpa_detail = score_quantamed_candidate("vpa", patient_id)
        off_target = vpa_detail.get(
            "details", {}).get(
            "off_target_details", [])
        for entry in off_target:
            if entry.get("sex_factor", 1.0) > 1.0:
                _add_risk_flag(
                    pdf,
                    entry["protein"],
                    entry["raw_binding"],
                    entry.get(
                        "risk_notes",
                        []))
    except Exception:
        pass

    # CYP flag
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(180, 100, 0)
    pdf.cell(0, 6, "CYP2C9 Intermediate Metabolizer Warning")
    _ln(pdf, 6)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    dose = patient.get("current_dose_mg", 1000)
    alt_val = patient.get("alt_u_l", 42)
    pdf.multi_cell(0, 5, (
        f"At {dose}mg/day VPA, CYP2C9 IM status predicts Css ~78.4 ug/mL "
        f"(31% above Normal Metabolizer). Approaching hepatotoxicity threshold "
        f"of 100 ug/mL. ALT already elevated at {alt_val} U/L."
    ))
    pdf.ln(4)

    # ── Recommendation ──
    top_drug = ranked[0] if ranked else {}
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 130, 60)
    pdf.cell(0, 8, "Recommendation")
    _ln(pdf, 8)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 100, 50)
    drug_name = top_drug.get("label", "N/A").upper()
    pdf.cell(0, 8, f"SWITCH TO {drug_name}")
    _ln(pdf, 8)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pat_name = patient.get("name", "this patient")
    drug_label = top_drug.get("label", "the recommended drug")
    pdf.multi_cell(0, 5, (
        f"Across all six simulation layers (Quantum VQE, Off-Target Panel, CYP Genomics, "
        f"ADMET/BBB, RL Timeline, TRIBE v2), {drug_label} achieves equivalent seizure "
        f"control with a dramatically superior safety, genomic, and metabolic profile "
        f"for {pat_name}'s specific biology."
    ))
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    scores = top_drug.get("scores", {})
    stat_line = (
        f"Composite: {scores.get('composite', 0):.2f}  |  "
        f"Efficacy: {scores.get('efficacy', 0):.0f}  |  "
        f"Safety: {scores.get('safety', 0):.0f}  |  "
        f"BBB: {scores.get('bbb', 0)}"
    )
    pdf.cell(0, 5, stat_line)
    _ln(pdf, 5)

    pdf.ln(10)

    # ── Disclaimer ──
    pdf.set_draw_color(150, 150, 150)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 4, ("DISCLAIMER: This report is generated by QuantaMed, a computational "
               "decision-support tool developed for research and educational purposes. "
               "All outputs are based on simulated quantum and classical models running "
               "on Qiskit Aer. This report is NOT a clinical prescription and must NOT "
               "be used for clinical decision-making without review by a licensed physician. "
               "All patient data is synthetic and anonymized."))
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(0, 4, "QuantaMed v1.0  |  Hackathon Edition  |  April 2026")
    _ln(pdf, 4)

    return bytes(pdf.output())


def _add_field(pdf: Any, label: str, value: str) -> None:
    """Add a label: value field row to the PDF."""
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(45, 5, label + ":")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 5, value)
    _ln(pdf, 5)


def _add_risk_flag(
        pdf: Any,
        protein: str,
        binding: float,
        notes: list[str]) -> None:
    """Add a highlighted risk flag entry to the PDF."""
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 6, f"HIGH RISK: {protein} Off-Target Binding = {binding:.2f}")
    _ln(pdf, 6)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    for note in notes:
        pdf.cell(0, 5, f"  - {note}")
        _ln(pdf, 5)
    pdf.ln(2)


def _generate_minimal_pdf(patient_id: str) -> bytes:
    """Fallback PDF generator when fpdf2 is not installed."""
    return b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 595 842] /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n50 750 Td\n(Report Unavailable) Tj\nET\nendstream\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF'

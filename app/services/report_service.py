"""
Medical PDF Report Generation Service using ReportLab.
Produces comprehensive, academic-standard clinical summary reports combining:
1. Patient / User metadata
2. Brain MRI Classification results & confidence metrics
3. Explainable AI (Grad-CAM) visualization
4. Multi-domain Cognitive Assessment scores and breakdown
5. Medical educational disclaimers and researcher signature blocks
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "app" / "static" / "reports"


def generate_pdf_report(
    user_info,
    mri_result=None,
    cognitive_result=None,
    output_filename=None
):
    """
    Generate professional multi-section PDF medical report.
    Args:
        user_info: dict with keys {"user_id", "username", "email"}
        mri_result: dict with keys {"predicted_category", "confidence", "image_path", "gradcam_path", "probabilities"}
        cognitive_result: dict with keys {"total_score", "max_score", "domain_scores", "performance_tier", "clinical_note"}
        output_filename: optional filename
    Returns:
        output_filepath (str)
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if not output_filename:
        report_uid = uuid.uuid4().hex[:8].upper()
        output_filename = f"Alzheimer_Report_{user_info.get('username', 'Patient')}_{report_uid}.pdf"

    output_path = REPORTS_DIR / output_filename
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom Color Palette
    primary_blue = colors.HexColor("#1E3A8A")
    secondary_blue = colors.HexColor("#0284C7")
    light_blue = colors.HexColor("#F0F9FF")
    dark_slate = colors.HexColor("#1E293B")
    border_gray = colors.HexColor("#CBD5E1")
    warning_red = colors.HexColor("#DC2626")

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_blue
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748B")
    )
    h2_style = ParagraphStyle(
        "Heading2Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_blue,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_slate
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#475569")
    )

    # 1. HEADER SECTION
    header_data = [
        [
            Paragraph("<b>NEUROLOGICAL INFORMATICS & COGNITIVE RESEARCH LABORATORY</b><br/>"
                      "<font size=8 color='#64748B'>Automated Neuroimaging & Cognitive Evaluation Protocol</font>", title_style),
            Paragraph(f"<b>REPORT ID:</b> ALZ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}<br/>"
                      f"<b>DATE:</b> {datetime.now().strftime('%B %d, %Y')}<br/>"
                      f"<b>TIME:</b> {datetime.now().strftime('%H:%M:%S')}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[4.2 * inch, 2.8 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=secondary_blue, spaceBefore=4, spaceAfter=12))

    # 2. PATIENT / SUBJECT METADATA
    story.append(Paragraph("1. SUBJECT / PATIENT PROFILE", h2_style))
    patient_data = [
        [
            Paragraph("<b>Subject Name:</b>", body_style),
            Paragraph(str(user_info.get("username", "Anonymous")), body_bold),
            Paragraph("<b>User / Patient ID:</b>", body_style),
            Paragraph(f"UID-{user_info.get('user_id', 'N/A')}", body_bold)
        ],
        [
            Paragraph("<b>Email:</b>", body_style),
            Paragraph(str(user_info.get("email", "Not Provided")), body_style),
            Paragraph("<b>Evaluation Protocol:</b>", body_style),
            Paragraph("MRI-DL + MM-Cog + XAI", body_style)
        ]
    ]
    patient_table = Table(patient_data, colWidths=[1.5 * inch, 2.0 * inch, 1.6 * inch, 1.9 * inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_blue),
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10))

    # 3. BRAIN MRI CLASSIFICATION & EXPLAINABLE AI
    if mri_result:
        story.append(Paragraph("2. BRAIN MRI DEEP LEARNING CLASSIFICATION & GRAD-CAM EXPLANATION", h2_style))
        category = mri_result.get("predicted_category", "Unknown")
        conf = float(mri_result.get("confidence", 0.0))

        # Result badge color
        cat_color = "#16A34A" if category == "Non-Demented" else ("#D97706" if "Mild" in category else "#DC2626")

        mri_summary_data = [
            [
                Paragraph("<b>Classification Category:</b>", body_style),
                Paragraph(f"<font color='{cat_color}'><b>{category}</b></font>", body_bold),
                Paragraph("<b>Model Confidence:</b>", body_style),
                Paragraph(f"<b>{conf * 100:.2f}%</b>", body_bold)
            ]
        ]
        mri_sum_table = Table(mri_summary_data, colWidths=[1.8 * inch, 2.2 * inch, 1.5 * inch, 1.5 * inch])
        mri_sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 1, secondary_blue),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(mri_sum_table)
        story.append(Spacer(1, 8))

        # Images: Original MRI & Grad-CAM side by side
        img_cells = []
        raw_img_path = mri_result.get("image_path")
        gradcam_path = mri_result.get("gradcam_path")

        # Resolve paths
        def resolve_img(p):
            if not p:
                return None
            full_p = PROJECT_ROOT / p if not Path(p).is_absolute() else Path(p)
            return str(full_p) if full_p.exists() else None

        actual_raw = resolve_img(raw_img_path)
        actual_xai = resolve_img(gradcam_path)

        if actual_raw and actual_xai:
            img_table_data = [
                [
                    Paragraph("<b>Original MRI Scan</b>", body_style),
                    Paragraph("<b>Grad-CAM Explainable AI Heatmap Overlay</b>", body_style)
                ],
                [
                    RLImage(actual_raw, width=2.4 * inch, height=2.4 * inch),
                    RLImage(actual_xai, width=3.8 * inch, height=2.4 * inch)
                ]
            ]
            img_table = Table(img_table_data, colWidths=[2.7 * inch, 4.3 * inch])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(img_table)
        elif actual_raw:
            story.append(RLImage(actual_raw, width=2.5 * inch, height=2.5 * inch))

        story.append(Paragraph(
            "<b>Grad-CAM Interpretation Note:</b> Red/yellow activation regions indicate the prominent anatomical features "
            "(such as hippocampal atrophy, lateral ventricular enlargement, or sulcal widening) driving the neural network's category assignment.",
            disclaimer_style
        ))
        story.append(Spacer(1, 10))

    # 4. COGNITIVE ASSESSMENT SECTION
    if cognitive_result:
        story.append(Paragraph("3. COGNITIVE ASSESSMENT DOMAIN EVALUATION", h2_style))
        total_cog = cognitive_result.get("total_score", 0)
        max_cog = cognitive_result.get("max_score", 30)
        tier = cognitive_result.get("performance_tier", "Standard")
        domain_scores = cognitive_result.get("domain_scores", {})

        cog_summary_data = [
            [
                Paragraph("<b>Total Cognitive Score:</b>", body_style),
                Paragraph(f"<b>{total_cog} / {max_cog} points</b> ({(total_cog/max_cog)*100:.1f}%)", body_bold),
                Paragraph("<b>Performance Tier:</b>", body_style),
                Paragraph(f"<b>{tier}</b>", body_bold)
            ]
        ]
        cog_sum_table = Table(cog_summary_data, colWidths=[1.8 * inch, 2.2 * inch, 1.5 * inch, 1.5 * inch])
        cog_sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 1, secondary_blue),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(cog_sum_table)
        story.append(Spacer(1, 6))

        # Domain Breakdown Table
        domain_table_rows = [
            [Paragraph("<b>Cognitive Domain</b>", body_bold),
             Paragraph("<b>Score Obtained</b>", body_bold),
             Paragraph("<b>Max Possible</b>", body_bold),
             Paragraph("<b>Percentage</b>", body_bold)]
        ]
        for dom, sc in domain_scores.items():
            domain_table_rows.append([
                Paragraph(dom, body_style),
                Paragraph(f"{sc}", body_style),
                Paragraph("6", body_style),
                Paragraph(f"{(sc/6)*100:.0f}%", body_style)
            ])

        dom_table = Table(domain_table_rows, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        dom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), light_blue),
            ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(dom_table)
        story.append(Spacer(1, 10))

    # 5. CLINICAL / ACADEMIC DISCLAIMER & SIGNATURE BLOCK
    story.append(KeepTogether([
        HRFlowable(width="100%", thickness=1, color=border_gray, spaceBefore=8, spaceAfter=8),
        Paragraph("<b>ACADEMIC RESEARCH & CLINICAL DISCLAIMER:</b>", ParagraphStyle("DiscTitle", parent=disclaimer_style, fontName="Helvetica-Bold", textColor=warning_red)),
        Paragraph(
            "This report is generated by an academic computer vision and cognitive informatics system. "
            "The 4-class MRI predictions, Grad-CAM neural attention heatmaps, and educational questionnaire scores "
            "do NOT constitute clinical medical diagnoses, radiological reports, or official medical advice. "
            "Neurological conditions such as Alzheimer's Disease and related dementias require comprehensive evaluation by a board-certified "
            "neurologist, structural neuroimaging (3T MRI/PET), laboratory biomarkers, and formal neuropsychological battery tests.",
            disclaimer_style
        ),
        Spacer(1, 16),
        Table([
            [
                Paragraph("<b>System Operator / Researcher:</b><br/>AI Neuroinformatics System<br/>Automated Processing Pipeline", body_style),
                Paragraph("<b>Supervising Clinician / Principal Investigator:</b><br/>____________________________<br/>MD / Ph.D. Verification Signature", body_style)
            ]
        ], colWidths=[3.5 * inch, 3.5 * inch])
    ]))

    doc.build(story)
    print(f"[OK] PDF Report successfully compiled: {output_path}")
    return str(output_path)

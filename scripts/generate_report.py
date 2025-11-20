#!/usr/bin/env python3
import os
import re
from io import BytesIO
from bs4 import BeautifulSoup
import matplotlib
matplotlib.use("Agg")  # REQUIRED for Jenkins / CI/CD
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet


# ============================================================
# Paths & Config
# ============================================================
INPUT_REPORT = 'report/report.html'
OUTPUT_DIR = 'report'
BASE_NAME = 'test_result_report'
VERSION_FILE = os.path.join(OUTPUT_DIR, 'version.txt')


# ============================================================
# Version Helper
# ============================================================
def get_next_version():
    """Reads version.txt → increments → writes new version."""
    version = 0
    if os.path.exists(VERSION_FILE):
        try:
            version = int(open(VERSION_FILE).read().strip())
        except:
            version = 0

    version = version + 1 if version >= 0 else 1
    with open(VERSION_FILE, 'w') as vf:
        vf.write(str(version))

    return version


# ============================================================
# Extract Summary Numbers
# ============================================================
def extract_summary_counts(html_text):
    patterns = {
        'passed': r'(\d+)\s+passed',
        'failed': r'(\d+)\s+failed',
        'skipped': r'(\d+)\s+skipped',
        'error': r'(\d+)\s+errors?',
    }

    counts = {}
    for key, pattern in patterns.items():
        m = re.search(pattern, html_text, re.IGNORECASE)
        counts[key] = int(m.group(1)) if m else 0

    return counts


# ============================================================
# Chart Generator
# ============================================================
def create_summary_chart(counts):
    labels = ['Passed', 'Failed', 'Skipped', 'Errors']
    values = [
        counts['passed'],
        counts['failed'],
        counts['skipped'],
        counts['error']
    ]

    if sum(values) == 0:
        values = [0.001] * 4  # Prevent div-zero

    colors_ = ['#4CAF50', '#F44336', '#FF9800', '#9E9E9E']

    fig, ax = plt.subplots(figsize=(7, 2.5))
    bars = ax.barh(labels, values, color=colors_)
    ax.set_xlabel('Number of Tests', fontsize=10)
    ax.set_title('Test Summary Overview', fontsize=11)
    ax.bar_label(bars, labels=[str(v) for v in values], label_type='edge', fontsize=9)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=180)
    buf.seek(0)
    plt.close(fig)

    return buf


# ============================================================
# PDF Generator
# ============================================================
def generate_pdf_report(version, counts, pass_rate, chart_buf):
    pdf_path = os.path.join(OUTPUT_DIR, f"{BASE_NAME}_v{version}.pdf")

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(
        f"<b>Test Result Report - v{version}</b>",
        styles['Title']
    ))
    elements.append(Spacer(1, 12))

    summary_html = f"""
        <b>Passed:</b> <font color='green'>{counts['passed']}</font> |
        <b>Failed:</b> <font color='red'>{counts['failed']}</font> |
        <b>Skipped:</b> <font color='orange'>{counts['skipped']}</font> |
        <b>Errors:</b> <font color='gray'>{counts['error']}</font><br/>
        <b>Pass Rate:</b> {pass_rate:.1f}%
    """

    elements.append(Paragraph(summary_html, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Chart
    img = Image(chart_buf)
    img._restrictSize(450, 200)
    elements.append(img)
    elements.append(Spacer(1, 20))

    # Table
    data = [
        ["Metric", "Count"],
        ["Passed", counts["passed"]],
        ["Failed", counts["failed"]],
        ["Skipped", counts["skipped"]],
        ["Errors", counts["error"]],
        ["Pass Rate", f"{pass_rate:.1f}%"]
    ]

    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
    ]))

    elements.append(table)
    doc.build(elements)

    print(f"📄 PDF report generated: {pdf_path}")
    return pdf_path


# ============================================================
# HTML Enhancer
# ============================================================
def enhance_html_report():
    if not os.path.exists(INPUT_REPORT):
        raise SystemExit(f"❌ Base HTML report missing: {INPUT_REPORT}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    html_content = open(INPUT_REPORT, 'r', encoding='utf-8').read()
    soup = BeautifulSoup(html_content, 'html.parser')

    counts = extract_summary_counts(html_content)
    total = sum(counts.values()) or 1
    pass_rate = (counts['passed'] / total) * 100

    summary_block = f"""
        <div style='background:#f9f9f9;border:1px solid #ccc;padding:15px;margin-bottom:15px;'>
            <h2>🔍 Test Execution Summary</h2>
            <p>
              <span style='color:#4CAF50;'>🟢 Passed: {counts['passed']}</span> |
              <span style='color:#F44336;'>🔴 Failed: {counts['failed']}</span> |
              <span style='color:#FF9800;'>🟠 Skipped: {counts['skipped']}</span> |
              <span style='color:#9E9E9E;'>⚫ Errors: {counts['error']}</span>
            </p>
            <p><b>Pass Rate:</b> {pass_rate:.1f}%</p>
        </div>
    """

    body = soup.body if soup.body else soup
    body.insert(0, BeautifulSoup(summary_block, 'html.parser'))

    version = get_next_version()

    html_out = os.path.join(OUTPUT_DIR, f"{BASE_NAME}_v{version}.html")
    with open(html_out, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f"✅ Enhanced HTML report created: {html_out}")
    print(f"🔢 Version v{version}")

    chart_buf = create_summary_chart(counts)
    pdf_path = generate_pdf_report(version, counts, pass_rate, chart_buf)

    return html_out, pdf_path


# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    enhance_html_report()

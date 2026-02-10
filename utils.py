import pandas as pd
from io import BytesIO
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Fixes main thread errors for plots

def generate_csv_report(data, columns, filename="report.csv"):
    df = pd.DataFrame(data, columns=columns)
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='text/csv')

def generate_excel_report(data, columns, filename="report.xlsx"):
    df = pd.DataFrame(data, columns=columns)
    buffer = BytesIO()
    # Requires 'openpyxl' installed: pip install openpyxl
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance Report')
    buffer.seek(0)
    return send_file(
        buffer, 
        as_attachment=True, 
        download_name=filename, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def generate_pdf_report(data, columns, filename="report.pdf", chart_title="Attendance Chart"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Attendance Report")
    y -= 30

    c.setFont("Helvetica", 10)
    row_height = 20

    # Draw Headers
    for i, col in enumerate(columns):
        c.drawString(50 + i*100, y, str(col))
    y -= row_height

    # Draw Rows
    for row in data:
        for i, item in enumerate(row):
            c.drawString(50 + i*100, y, str(item))
        y -= row_height
        if y < 150: 
            c.showPage()
            y = height - 50

    try:
        df = pd.DataFrame(data, columns=columns)
        if "Status" in df.columns:
            chart_data = df["Status"].value_counts()
            plt.figure(figsize=(4, 3))
            chart_data.plot(kind="pie", autopct="%1.1f%%", startangle=90)
            plt.title(chart_title)
        elif "Attendance %" in df.columns:
            plt.figure(figsize=(5, 3))
            df.plot(kind="bar", x="Name", y="Attendance %", legend=False)
            plt.title(chart_title)
            plt.ylabel("Percentage")
            plt.xticks(rotation=45, ha="right")

        img_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format="PNG")
        plt.close()
        img_buffer.seek(0)

        c.drawImage(img_buffer, 50, 50, width=400, height=200)
    except Exception as e:
        c.setFont("Helvetica", 10)
        c.drawString(50, 100, f"Chart could not be generated: {e}")

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")
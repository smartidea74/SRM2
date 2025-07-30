
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import re

def extract_table_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    lines = text.splitlines()

    data = []
    for line in lines:
        if re.search(r'\d+\.\d{2}', line):  # има числа с десетични
            parts = line.split()
            try:
                float(parts[-4].replace(",", "."))
                row = {
                    "Наименование": " ".join(parts[:-5]),
                    "Кол.": float(parts[-5].replace(",", ".")),
                    "Цена пр. с ДДС": float(parts[-4].replace(",", ".")),
                }
                data.append(row)
            except:
                continue

    return pd.DataFrame(data)

def generate_modified_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 10)

    x_start = 20 * mm
    y_start = 270 * mm
    y = y_start

    headers = ["Наименование", "Кол.", "Цена пр. с ДДС", "Цена в евро"]
    for i, header in enumerate(headers):
        c.drawString(x_start + i * 40 * mm, y, header)

    y -= 10
    for _, row in df.iterrows():
        c.drawString(x_start + 0 * 40 * mm, y, str(row["Наименование"])[:25])
        c.drawString(x_start + 1 * 40 * mm, y, f'{row["Кол."]:.2f}')
        c.drawString(x_start + 2 * 40 * mm, y, f'{row["Цена пр. с ДДС"]:.2f}')
        c.drawString(x_start + 3 * 40 * mm, y, f'{row["Цена в евро"]:.2f}')
        y -= 10
        if y < 50:
            c.showPage()
            y = y_start

    c.save()
    buffer.seek(0)
    return buffer

def run_app():
    st.title("PDF Обработчик: Добавяне на колона 'Цена в евро'")
    uploaded_file = st.file_uploader("Качи PDF файл", type="pdf")

    if uploaded_file:
        df = extract_table_from_pdf(uploaded_file.read())

        if df.empty:
            st.error("Не е открита таблица с данни.")
            return

        df["Цена в евро"] = df["Цена пр. с ДДС"] / 1.95583
        df["Цена в евро"] = df["Цена в евро"].round(2)

        st.write("Обработена таблица:")
        st.dataframe(df)

        pdf_bytes = generate_modified_pdf(df)
        st.download_button(
            label="📥 Изтегли новия PDF с колонка 'Цена в евро'",
            data=pdf_bytes,
            file_name="modified_invoice.pdf",
            mime="application/pdf"
        )

run_app()

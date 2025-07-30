
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import re

def extract_lines_with_numbers(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    lines = text.splitlines()

    numeric_lines = []
    pattern = re.compile(r"(\d+[\.,]\d{2}\s+){5,}\d+[\.,]\d{2}$")  # търси редове с поне 6 десетични числа
    for line in lines:
        if pattern.search(line):
            numeric_lines.append(line.strip())
    return numeric_lines

def parse_lines_to_dataframe(lines):
    rows = []
    for line in lines:
        parts = line.split()
        numbers = []
        texts = []

        for part in parts[::-1]:
            try:
                numbers.insert(0, float(part.replace(",", ".")))
            except:
                texts.insert(0, part)

        if len(numbers) >= 6:
            rows.append({
                "Наименование": " ".join(texts),
                "Числа": numbers
            })
    return pd.DataFrame(rows)

def generate_modified_pdf(df, col_name):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 9)

    x_start = 10 * mm
    y_start = 270 * mm
    y = y_start

    headers = df.columns.tolist()
    for i, header in enumerate(headers):
        c.drawString(x_start + i * 40 * mm, y, header)

    y -= 10
    for _, row in df.iterrows():
        for i, col in enumerate(headers):
            value = row[col]
            text = f"{value:.2f}" if isinstance(value, float) else str(value)[:30]
            c.drawString(x_start + i * 40 * mm, y, text)
        y -= 10
        if y < 40:
            c.showPage()
            y = y_start

    c.save()
    buffer.seek(0)
    return buffer

def safe_eval(formula, x):
    try:
        return eval(formula, {"x": x, "__builtins__": {}})
    except:
        return None

def run_app():
    st.title("PDF Обработчик: Формула по позиция отдясно")

    uploaded_file = st.file_uploader("Качи PDF файл", type="pdf")

    if uploaded_file:
        lines = extract_lines_with_numbers(uploaded_file.read())
        df = parse_lines_to_dataframe(lines)

        if df.empty:
            st.error("Не са открити редове с числови стойности.")
            return

        st.write("Преглед на извлечените редове:")
        st.dataframe(df[["Наименование", "Числа"]])

        max_pos = len(df.iloc[0]["Числа"]) if not df.empty else 6
        pos = st.number_input(f"Коя позиция отдясно да използваме? (напр. 3 = трето число отдясно)", min_value=1, max_value=max_pos, value=3)
        formula = st.text_input("Въведи формула (пример: x / 1.95583):", value="x / 1.95583")
        new_col_name = st.text_input("Име на новата колонка:", value="Цена в евро")

        if st.button("Добави колоната"):
            try:
                df[new_col_name] = df["Числа"].apply(lambda lst: round(safe_eval(formula, lst[-pos]), 2) if len(lst) >= pos else "")
                df_final = df[["Наименование", new_col_name]]
                st.success(f"Колоната '{new_col_name}' е добавена успешно!")
                st.dataframe(df_final)

                pdf_bytes = generate_modified_pdf(df_final, new_col_name)
                st.download_button(
                    label="📥 Изтегли новия PDF",
                    data=pdf_bytes,
                    file_name="modified_invoice.pdf",
                    mime="application/pdf"
                )
            except:
                st.error("Формулата не можа да бъде приложена. Провери синтаксиса.")

run_app()

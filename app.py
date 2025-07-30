
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

    pattern = re.compile(
        r"^(?P<name>.+?)\s+(?P<qty>\d+[\.,]?\d*)\s+(?P<price1>\d+[\.,]?\d*)\s+(?P<price2>\d+[\.,]?\d*)\s+(?P<avg>\d+[\.,]?\d*)\s+(?P<markup>\d+[\.,]?\d*)\s+(?P<total>\d+[\.,]?\d*)$"
    )

    for line in lines:
        match = pattern.match(line.strip())
        if match:
            try:
                data.append({
                    "Наименование": match.group("name"),
                    "Количество": float(match.group("qty").replace(",", ".")),
                    "Цена пр. с ДДС": float(match.group("price1").replace(",", ".")),
                    "Цена пр. без": float(match.group("price2").replace(",", ".")),
                    "Ср. цена": float(match.group("avg").replace(",", ".")),
                    "Надценка": float(match.group("markup").replace(",", ".")),
                    "Стойност": float(match.group("total").replace(",", "."))
                })
            except:
                continue

    return pd.DataFrame(data)

def generate_modified_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 9)

    x_start = 10 * mm
    y_start = 270 * mm
    y = y_start

    headers = df.columns.tolist()
    for i, header in enumerate(headers):
        c.drawString(x_start + i * 30 * mm, y, header)

    y -= 10
    for _, row in df.iterrows():
        for i, col in enumerate(headers):
            value = row[col]
            text = f"{value:.2f}" if isinstance(value, float) else str(value)[:20]
            c.drawString(x_start + i * 30 * mm, y, text)
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
    st.title("PDF Обработчик: Формула по избор върху избрана колона")

    uploaded_file = st.file_uploader("Качи PDF файл", type="pdf")

    if uploaded_file:
        df = extract_table_from_pdf(uploaded_file.read())

        if df.empty:
            st.error("Не е открита таблица с данни.")
            return

        st.write("Разпознати колони:")
        st.dataframe(df.head())

        selected_column = st.selectbox("Избери колона за изчисление:", df.columns)
        formula = st.text_input("Въведи формула (пример: x / 1.95583):", value="x / 1.95583")
        new_col_name = st.text_input("Име на новата колонка:", value="Цена в евро")

        if st.button("Добави колоната"):
            try:
                df[new_col_name] = df[selected_column].apply(lambda x: round(safe_eval(formula, x), 2) if pd.notnull(x) else "")
                st.success(f"Колоната '{new_col_name}' е добавена успешно!")
                st.dataframe(df)

                pdf_bytes = generate_modified_pdf(df)
                st.download_button(
                    label="📥 Изтегли новия PDF",
                    data=pdf_bytes,
                    file_name="modified_invoice.pdf",
                    mime="application/pdf"
                )
            except:
                st.error("Формулата не можа да бъде приложена. Провери синтаксиса.")

run_app()

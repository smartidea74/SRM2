
import streamlit as st
import pandas as pd
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Font
from tempfile import NamedTemporaryFile

st.set_page_config(layout="wide")

def ocr_extract_lines_from_pdf(pdf_bytes):
    images = convert_from_bytes(pdf_bytes)
    all_lines = []
    for img in images:
        text = pytesseract.image_to_string(img, lang="eng")
        lines = text.splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        all_lines.extend(lines)
    return all_lines

def detect_tabular_data(lines):
    pattern = re.compile(r"([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)$")
    rows = []
    for line in lines:
        match = pattern.search(line)
        if match:
            qty, price, total = match.groups()
            text = line[:match.start()].strip()
            rows.append([text, qty, price, total])
    return rows

def generate_excel_from_dataframe(df):
    wb = Workbook()
    ws = wb.active
    ws.title = "Таблица"

    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.alignment = Alignment(horizontal="center")
            if r_idx == 1:
                cell.font = Font(bold=True)

    for col_idx, col in enumerate(ws.columns, start=1):
        max_length = max(len(str(cell.value)) for cell in col if cell.value)
        if col_idx == 2:
            max_length = min(max_length, 40)  # ограничаваме ширината на втората колона
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    tmp = NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    tmp.seek(0)
    return tmp.read()

def safe_eval(formula, x):
    try:
        return eval(formula, {"x": x, "__builtins__": {}})
    except:
        return None

def run():
    st.title("🧾 OCR PDF към Excel с формула")
    uploaded_file = st.file_uploader("Качи сканиран PDF (или с неструктуриран текст)", type="pdf")

    if uploaded_file:
        with st.spinner("Извличане на текст чрез OCR..."):
            lines = ocr_extract_lines_from_pdf(uploaded_file.read())

        rows = detect_tabular_data(lines)

        if not rows:
            st.warning("❌ Не бяха открити редове с количествени данни.")
            return

        df = pd.DataFrame(rows, columns=["Описание", "Количество", "Цена", "Сума"])
        st.write("📋 Разпозната таблица:")
        st.dataframe(df)

        formula = st.text_input("Формула за нова колонка (напр. x / 1.95583):", value="x / 1.95583")
        new_col_name = st.text_input("Име на новата колонка:", value="Цена в лева")

        if st.button("Добави колоната"):
            try:
                def try_calc(val):
                    try:
                        x = float(str(val).replace(",", "."))
                        return round(safe_eval(formula, x), 2)
                    except:
                        return ""

                df[new_col_name] = df["Сума"].apply(try_calc)
                st.success("✅ Колоната е добавена!")
                st.dataframe(df)

                excel_bytes = generate_excel_from_dataframe(df)
                st.download_button(
                    label="📥 Изтегли Excel",
                    data=excel_bytes,
                    file_name="ocr_table.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Грешка при изчисление: {e}")

run()

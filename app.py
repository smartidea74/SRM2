
import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Font
from tempfile import NamedTemporaryFile

def extract_table_from_pdf_plumber(pdf_bytes):
    rows = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and any(cell for cell in row):
                        rows.append(row)
    return rows

def convert_to_dataframe(table_rows):
    df = pd.DataFrame(table_rows)
    df = df.dropna(how='all')
    df = df[df.apply(lambda row: any(str(cell).strip() for cell in row), axis=1)]
    return df

def safe_eval(formula, x):
    try:
        return eval(formula, {"x": x, "__builtins__": {}})
    except:
        return None

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

    for col in ws.columns:
        max_length = max(len(str(cell.value)) for cell in col if cell.value)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    tmp = NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    tmp.seek(0)
    return tmp.read()

def run_app():
    st.title("📄 PDF към Excel с изчислена колонка")

    uploaded_file = st.file_uploader("Качи PDF файл", type="pdf")

    if uploaded_file:
        table_rows = extract_table_from_pdf_plumber(uploaded_file.read())

        if not table_rows:
            st.error("Не бяха открити таблици в PDF файла.")
            return

        skip_first = st.checkbox("Пропусни първия ред (заглавия)?", value=True)
        if skip_first:
            table_rows = table_rows[1:]

        df = convert_to_dataframe(table_rows)
        st.write("📋 Извлечена таблица:")
        st.dataframe(df)

        max_cols = len(df.columns)
        selected_position = st.number_input("Избери позиция на колоната за изчисление отдясно (напр. 5 = пета отдясно):", min_value=1, max_value=max_cols, value=5)
        selected_name_position = st.number_input("Избери позиция на колоната с наименования отдясно:", min_value=1, max_value=max_cols, value=6)
        formula = st.text_input("Формула (пример: x / 1.95583):", value="x / 1.95583")
        new_col_name = st.text_input("Име на новата колонка:", value="Цена в евро")

        if st.button("Добави колоната"):
            try:
                target_col_index = -selected_position
                name_col_index = -selected_name_position

                def try_calc(val):
                    try:
                        x = float(str(val).replace(",", "."))
                        return round(safe_eval(formula, x), 2)
                    except:
                        return ""

                df[new_col_name] = df.iloc[:, target_col_index].apply(try_calc)
                st.success("✅ Колоната е добавена успешно!")
                st.dataframe(df)

                name_col = df.columns[name_col_index]
                target_col = df.columns[target_col_index]
                df_export = df[[name_col, target_col, new_col_name]]

                excel_bytes = generate_excel_from_dataframe(df_export)
                st.download_button(
                    label="📥 Изтегли Excel с наименования, база и нова колонка",
                    data=excel_bytes,
                    file_name="converted.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Грешка при обработка: {e}")

run_app()

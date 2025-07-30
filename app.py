
import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

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
    df = df.dropna(how='all')  # премахва изцяло празни редове
    df = df[df.apply(lambda row: any(str(cell).strip() for cell in row), axis=1)]
    return df

def safe_eval(formula, x):
    try:
        return eval(formula, {"x": x, "__builtins__": {}})
    except:
        return None

def generate_pdf_from_dataframe(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 8)

    x_start = 10 * mm
    y_start = 270 * mm
    y = y_start

    headers = df.columns.tolist()
    for i, header in enumerate(headers):
        c.drawString(x_start + i * 30 * mm, y, str(header)[:20])

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

def run_app():
    st.title("PDF Обработчик с PDFPlumber: Формула по позиция отдясно")

    uploaded_file = st.file_uploader("Качи PDF файл", type="pdf")

    if uploaded_file:
        table_rows = extract_table_from_pdf_plumber(uploaded_file.read())

        if not table_rows:
            st.error("Не бяха открити таблици в PDF файла.")
            return

        df = convert_to_dataframe(table_rows)
        st.write("Извлечена таблица:")
        st.dataframe(df)

        max_cols = len(df.columns)
        selected_position = st.number_input("Избери позиция на колоната отдясно (напр. 3 = трета отдясно):", min_value=1, max_value=max_cols, value=3)
        formula = st.text_input("Формула (пример: x / 1.95583):", value="x / 1.95583")
        new_col_name = st.text_input("Име на новата колонка:", value="Цена в евро")

        if st.button("Добави колоната"):
            target_col_index = -selected_position
            try:
                df[new_col_name] = df.iloc[:, target_col_index].apply(lambda val: round(safe_eval(formula, float(str(val).replace(',', '.'))), 2) if val not in [None, ''] else "")
                st.success("Колоната е добавена успешно!")
                st.dataframe(df)

                pdf_bytes = generate_pdf_from_dataframe(df[[df.columns[0], new_col_name]])
                st.download_button(
                    label="📥 Изтегли PDF с новата колонка",
                    data=pdf_bytes,
                    file_name="converted.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Грешка при обработка: {e}")

run_app()

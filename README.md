
# PDF Processor with Currency Conversion

This Streamlit app allows you to upload a Bulgarian invoice or stock PDF document
and automatically adds a column **"Цена в евро"** (Price in EUR),
calculated by dividing the **"Цена пр. с ДДС"** column by 1.95583 and rounding to 2 decimal places.

## ✅ Features
- Extracts tables from PDF documents (expected format: warehouse or invoice).
- Adds a calculated column with euro-converted prices.
- Generates a new PDF for download.

## ▶️ How to Use
1. Install the required packages:
   ```
   pip install streamlit pandas PyMuPDF reportlab
   ```

2. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

3. Upload your PDF and download the modified version.

---

Created by: Ваня Иванова

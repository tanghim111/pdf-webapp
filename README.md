# PDF Scan-like & Page Remover (Streamlit)

- حذف صفحات PDF (الگوی `1,3,5-7`)
- تبدیل PDF متنی به PDF تصویری با حس «اسکن» (کجی جزئی، نویز، کنتراست متغیر)

## محلی (لوکال)
1) نصب Python 3.10+
2) نصب poppler (Windows: دانلود و افزودن به PATH)
3) `pip install -r requirements.txt`
4) `streamlit run app_streamlit.py`

## استقرار آنلاین (Hugging Face Spaces)
- این مخزن را به عنوان Space با **SDK: Streamlit** بسازید.
- `packages.txt` باعث نصب `poppler-utils` و وابستگی‌های لازم می‌شود.
- بعد از Build، لینک عمومی Space آماده است.

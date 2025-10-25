import streamlit as st
import tempfile, os, shutil, io
from pdf_scanner_like import pdf_text_to_scanned_pdf, remove_pages, parse_page_list
from PyPDF2 import PdfReader

st.set_page_config(page_title="PDF Scan-like & Page Remover", page_icon="🖨️", layout="centered")
st.title("🖨️ PDF — حذف صفحات + تبدیل به نسخه‌ی شبیه اسکن")

with st.expander("راهنما", expanded=False):
    st.markdown("""
- یک PDF آپلود کن.
- اگر می‌خواهی صفحاتی حذف شوند، مثل `1,3,5-7` وارد کن.
- اگر می‌خواهی خروجی «شبیه اسکن» باشد، تیک بزن.
- دکمه «اجرا» را بزن و فایل خروجی را دانلود کن.
""")

uploaded = st.file_uploader("فایل PDF را آپلود کن", type=["pdf"])
remove_input = st.text_input("صفحات برای حذف (مثال: 1,3,5-7) — خالی: بدون حذف", "")
do_scan = st.checkbox("تبدیل به PDF شبیه اسکن (متنی → تصویری با حس اسکن)")
dpi = st.slider("DPI رندر صفحات (برای حالت شبیه اسکن)", min_value=120, max_value=300, value=200, step=10)

run_btn = st.button("اجرا")

if run_btn:
    if not uploaded:
        st.error("اول فایل PDF را آپلود کن.")
        st.stop()

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "input.pdf")
        with open(in_path, "wb") as f:
            f.write(uploaded.read())

        # بررسی اولیه PDF
        try:
            reader = PdfReader(in_path)
            total_pages = len(reader.pages)
        except Exception as e:
            st.error(f"خطا در خواندن PDF: {e}")
            st.stop()

        st.info(f"تعداد صفحات فایل: {total_pages}")

        work_input = in_path
        # حذف صفحات
        if remove_input.strip():
            try:
                remove_list = parse_page_list(remove_input, maxpage=total_pages)
                if not remove_list:
                    st.warning("الگوی صفحات معتبر نبود یا خارج از بازه بود؛ حذف انجام نشد.")
                else:
                    tmp_removed = os.path.join(tmpdir, "removed.pdf")
                    remove_pages(work_input, remove_list, tmp_removed)
                    work_input = tmp_removed
                    st.success(f"صفحات {remove_list} حذف شدند.")
            except Exception as e:
                st.error(f"خطا در حذف صفحات: {e}")
                st.stop()

        out_path = os.path.join(tmpdir, "output.pdf")
        try:
            if do_scan:
                # روی هاست آنلاین (Hugging Face) poppler-utils نصب می‌شود (از packages.txt)
                pdf_text_to_scanned_pdf(work_input, out_path, poppler_path=None, dpi=dpi)
            else:
                shutil.copy(work_input, out_path)

            st.success("تمام شد. فایل خروجی آمادهٔ دانلود است.")
            with open(out_path, "rb") as f:
                st.download_button("دانلود PDF خروجی", f, file_name="output.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"خطا هنگام پردازش: {e}")

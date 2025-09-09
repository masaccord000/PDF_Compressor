import streamlit as st
import zipfile
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import tempfile

st.set_page_config(page_title="PDF圧縮ツール", layout="centered")
st.title("📄 PDF圧縮ツール（ZIPアップロード + パスワード解凍）")

uploaded_zip = st.file_uploader("📤 ZIPファイルをアップロード", type=["zip"])
password = st.text_input("🔑 ZIPパスワード", type="password")
quality = st.slider("📉 JPEG圧縮品質（低いほど高圧縮）", min_value=10, max_value=95, value=50)

if uploaded_zip and password:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())

        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.setpassword(password.encode())
                zf.extractall(tmpdir)
                st.success("✅ ZIPファイルを解凍しました")
        except RuntimeError:
            st.error("❌ パスワードが間違っているか、ZIPファイルが壊れています")
            st.stop()

        pdf_files = [f for f in os.listdir(tmpdir) if f.lower().endswith(".pdf")]
        if not pdf_files:
            st.warning("⚠️ 解凍されたZIPにPDFファイルが見つかりませんでした")
            st.stop()

        for pdf_file in pdf_files:
            input_path = os.path.join(tmpdir, pdf_file)
            output_path = os.path.join(tmpdir, f"compressed_{pdf_file}")

            doc = fitz.open(input_path)
            new_doc = fitz.open()

            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=quality)
                img_bytes = buffer.getvalue()

                rect = fitz.Rect(0, 0, img.width, img.height)
                new_page = new_doc.new_page(width=rect.width, height=rect.height)
                new_page.insert_image(rect, stream=img_bytes)

            new_doc.save(output_path)
            new_doc.close()
            doc.close()

            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 {pdf_file} をダウンロード",
                    data=f,
                    file_name=f"compressed_{pdf_file}",
                    mime="application/pdf"
                )

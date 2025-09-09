import streamlit as st
import zipfile
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import tempfile

# ページ設定
st.set_page_config(page_title="PDF圧縮ツール", layout="centered")
st.title("📄 PDF圧縮ツール（ZIPアップロード + パスワード解凍）")

# 入力UI
uploaded_zip = st.file_uploader("📤 ZIPファイルをアップロード", type=["zip"])
password = st.text_input("🔑 ZIPパスワード", type="password")
quality = st.slider("📉 JPEG圧縮品質（低いほど高圧縮）", min_value=10, max_value=95, value=50)
scale = st.slider("🔍 DPIスケール（1 = 約72dpi）", min_value=1.0, max_value=3.0, value=1.5, step=0.1)

# 処理開始
if uploaded_zip and password:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())

        # ZIP解凍（パスワード付き）
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.setpassword(password.encode())
                zf.extractall(tmpdir)
                st.success("✅ ZIPファイルを解凍しました")
        except RuntimeError:
            st.error("❌ パスワードが間違っているか、ZIPファイルが壊れています")
            st.stop()

        # PDFファイル抽出
        pdf_files = [f for f in os.listdir(tmpdir) if f.lower().endswith(".pdf")]
        if not pdf_files:
            st.warning("⚠️ 解凍されたZIPにPDFファイルが見つかりませんでした")
            st.stop()

        # 圧縮処理
        for pdf_file in pdf_files:
            input_path = os.path.join(tmpdir, pdf_file)
            output_path = os.path.join(tmpdir, f"compressed_{pdf_file}")

            doc = fitz.open(input_path)
            new_doc = fitz.open()
            matrix = fitz.Matrix(scale, scale)

            for page in doc:
                pix = page.get_pixmap(matrix=matrix)
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

            # ファイルサイズ比較
            original_size = os.path.getsize(input_path) / 1024
            compressed_size = os.path.getsize(output_path) / 1024
            reduction_rate = 100 * (1 - compressed_size / original_size)

            st.markdown(f"""
            ### 📄 {pdf_file}
            - 元サイズ: `{original_size:.2f} KB`
            - 圧縮後: `{compressed_size:.2f} KB`
            - 圧縮率: `{reduction_rate:.1f}%`
            """)

            # ダウンロードボタン
            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 圧縮済PDF（{pdf_file}）をダウンロード",
                    data=f,
                    file_name=f"compressed_{pdf_file}",
                    mime="application/pdf"
                )

import streamlit as st
import zipfile
import os
import tempfile
import io
import aspose.pdf as ap

st.set_page_config(page_title="PDF圧縮ツール", layout="centered")
st.title("📄 PDF圧縮ツール（ZIPアップロード + パスワード解凍）")

uploaded_zip = st.file_uploader("📤 ZIPファイルをアップロード", type=["zip"])
password = st.text_input("🔑 ZIPパスワード", type="password")
quality = st.slider("📉 画像品質（低いほど高圧縮）", min_value=10, max_value=95, value=50)

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

            doc = ap.Document(input_path)

            # 最適化オプションの設定
            opt = ap.optimization.OptimizationOptions()
            opt.image_compression_options.compress_images = True
            opt.image_compression_options.image_quality = quality
            opt.remove_unused_objects = True
            opt.remove_unused_streams = True

            doc.optimize_resources(opt)
            doc.save(output_path)

            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 {pdf_file} をダウンロード",
                    data=f,
                    file_name=f"compressed_{pdf_file}",
                    mime="application/pdf"
                )

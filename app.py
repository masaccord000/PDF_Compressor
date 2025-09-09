import streamlit as st
import zipfile
import os
import tempfile
import aspose.pdf as ap

# ページ設定
st.set_page_config(page_title="PDF圧縮ツール", layout="centered")
st.title("📄 PDF圧縮ツール（パスワード付きZIP対応）")

# ファイルアップロードとパスワード入力
uploaded_zip = st.file_uploader("📤 パスワード付きZIPファイルをアップロード", type=["zip"])
password = st.text_input("🔑 ZIPパスワードを入力", type="password")
quality = st.slider("📉 画像品質（低いほど高圧縮）", min_value=10, max_value=95, value=50)

# 入力が揃ったら処理開始
if uploaded_zip and password:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")

        # ZIPファイルを一時保存
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

        # PDFファイルを抽出
        pdf_files = [f for f in os.listdir(tmpdir) if f.lower().endswith(".pdf")]
        if not pdf_files:
            st.warning("⚠️ 解凍されたZIPにPDFファイルが見つかりませんでした")
            st.stop()

        # 各PDFを圧縮処理
        for pdf_file in pdf_files:
            input_path = os.path.join(tmpdir, pdf_file)
            output_path = os.path.join(tmpdir, f"compressed_{pdf_file}")

            # PDF読み込み
            doc = ap.Document(input_path)

            # 圧縮オプション設定
            opt = ap.optimization.OptimizationOptions()
            opt.image_compression_options.compress_images = True
            opt.image_compression_options.image_quality = quality
            opt.remove_unused_objects = True
            opt.remove_unused_streams = True
            opt.remove_private_info = True

            # 圧縮処理の実行
            doc.optimize_resources(opt)
            doc.linearize()
            doc.save(output_path)

            # 圧縮前後のサイズ比較
            original_size = os.path.getsize(input_path) / 1024
            compressed_size = os.path.getsize(output_path) / 1024
            reduction_rate = 100 * (1 - compressed_size / original_size)

            st.write(f"📄 元PDFサイズ: {original_size:.2f} KB")
            st.write(f"📉 圧縮後PDFサイズ: {compressed_size:.2f} KB")
            st.write(f"✅ 圧縮率: {reduction_rate:.1f}%")

            # ダウンロードボタン表示
            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 圧縮済PDF（{pdf_file}）をダウンロード",
                    data=f,
                    file_name=f"compressed_{pdf_file}",
                    mime="application/pdf"
                )

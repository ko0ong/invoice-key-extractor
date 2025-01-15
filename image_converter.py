import fitz
import io
from PIL import Image
import base64
import streamlit as st

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def file_to_base64_image(file):
    if file.type == "application/pdf":
        try:
            pdf_document = fitz.open(stream=file.read(), filetype="pdf")
            page = pdf_document.load_page(0)
            pix = page.get_pixmap()
            with Image.open(io.BytesIO(pix.tobytes())) as img:
                img.verify()

            img = Image.open(io.BytesIO(pix.tobytes()))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            return encode_image(img_bytes.read())

        except Exception as e:
            st.error(f"PDF에서 이미지를 추출하는 중 오류가 발생했습니다: {e}")
            return None 
    elif file.type in ["image/png", "image/jpeg"]:
        try:
            file_bytes = file.read()
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()
            return encode_image(file_bytes)

        except Exception as e:
            st.error(f"이미지가 손상되었거나 지원하지 않는 형식입니다: {e}")
            return None

    else:
        st.error("지원하지 않는 파일 형식입니다. PDF, PNG, JPEG만 지원됩니다.")
        return None
import fitz
import io
from PIL import Image
import base64
import streamlit as st  # 만약 Streamlit을 사용 중이라면

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def file_to_base64_image(file):
    """PDF, PNG, JPEG 파일을 base64로 인코딩하여 반환.
       예외 상황이 발생하면 streamlit 오류 메시지 표시(또는 raise).
    """
    if file.type == "application/pdf":
        try:
            pdf_document = fitz.open(stream=file.read(), filetype="pdf")
            page = pdf_document.load_page(0)
            pix = page.get_pixmap()

            # pdf -> 이미지 변환 시도
            with Image.open(io.BytesIO(pix.tobytes())) as img:
                # 필요하다면 verify()로 무결성 체크
                img.verify()

            # 다시 Image.open()해서 실제 PIL 객체로 만들어 저장
            img = Image.open(io.BytesIO(pix.tobytes()))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            return encode_image(img_bytes.read())

        except Exception as e:
            # 여기서 어떻게 처리할지 결정.
            # Streamlit에 오류 표시 후, 함수 자체를 종료하거나,
            # ValueError 등으로 재-raise해서 상위 로직에서 처리하게 만들 수도 있음.
            st.error(f"PDF에서 이미지를 추출하는 중 오류가 발생했습니다: {e}")
            return None  # 혹은 raise e

    elif file.type in ["image/png", "image/jpeg"]:
        try:
            file_bytes = file.read()
            # Pillow로 실제 이미지 무결성 체크
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()
            # verify()가 성공하면 Base64 인코딩
            return encode_image(file_bytes)

        except Exception as e:
            st.error(f"이미지가 손상되었거나 지원하지 않는 형식입니다: {e}")
            return None

    else:
        # 지원하지 않는 파일 형식일 때
        st.error("지원하지 않는 파일 형식입니다. PDF, PNG, JPEG만 지원됩니다.")
        return None

# import fitz
# import io
# from PIL import Image
# import base64

# def encode_image(image_bytes):
#     return base64.b64encode(image_bytes).decode('utf-8')

# def file_to_base64_image(file):
#     if file.type == "application/pdf":
#         pdf_document = fitz.open(stream=file.read(), filetype="pdf")
#         page = pdf_document.load_page(0)  
#         pix = page.get_pixmap()  
#         img = Image.open(io.BytesIO(pix.tobytes()))  

#         img_bytes = io.BytesIO()
#         img.save(img_bytes, format="PNG")
#         img_bytes.seek(0)
#         return encode_image(img_bytes.read())

#     elif file.type in ["image/png", "image/jpeg"]:
#         return encode_image(file.read())

#     else:
#         raise ValueError("지원하지 않는 파일 형식입니다. PDF 또는 PNG/JPEG 파일만 지원됩니다.")
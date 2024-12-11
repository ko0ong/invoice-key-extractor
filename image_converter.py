import fitz
import io
from PIL import Image
import base64

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def file_to_base64_image(file):
    if file.type == "application/pdf":
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        page = pdf_document.load_page(0)  
        pix = page.get_pixmap()  
        img = Image.open(io.BytesIO(pix.tobytes()))  

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return encode_image(img_bytes.read())

    elif file.type in ["image/png", "image/jpeg"]:
        return encode_image(file.read())

    else:
        raise ValueError("지원하지 않는 파일 형식입니다. PDF 또는 PNG/JPEG 파일만 지원됩니다.")
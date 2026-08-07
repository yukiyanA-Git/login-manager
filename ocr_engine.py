import io
import asyncio
import unicodedata
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab

def preprocess_image_for_ocr(pil_image: Image.Image) -> Image.Image:
    if pil_image is None:
        return None

    img = pil_image.convert('RGB')
    w, h = img.size
    img_scaled = img.resize((w * 3, h * 3), Image.Resampling.LANCZOS)
    gray = img_scaled.convert('L')

    enh_contrast = ImageEnhance.Contrast(gray)
    img_contrast = enh_contrast.enhance(2.2)

    enh_sharp = ImageEnhance.Sharpness(img_contrast)
    img_sharp = enh_sharp.enhance(2.5)

    return img_sharp

def clean_ocr_text(text: str) -> str:
    if not text:
        return ""

    norm = unicodedata.normalize('NFKC', text)
    lines = [line.strip() for line in norm.splitlines() if line.strip()]

    clean_lines = []
    for l in lines:
        cleaned = l.strip(" |[]()-:：・_™®©")
        if len(cleaned) >= 1:
            clean_lines.append(cleaned)

    result = " ".join(clean_lines)
    return result

def perform_ocr_on_image(pil_image: Image.Image) -> str:
    if pil_image is None:
        return ""

    processed_img = preprocess_image_for_ocr(pil_image)

    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

        async def _run_ocr(img_to_ocr):
            img_byte_arr = io.BytesIO()
            img_to_ocr.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            stream = InMemoryRandomAccessStream()
            writer = DataWriter(stream.get_output_stream_at(0))
            writer.write_bytes(img_bytes)
            await writer.store_async()
            await writer.flush_async()

            decoder = await BitmapDecoder.create_async(stream)
            software_bitmap = await decoder.get_software_bitmap_async()

            ocr_engine = OcrEngine.try_create_from_user_profile_languages()
            if not ocr_engine:
                return ""

            result = await ocr_engine.recognize_async(software_bitmap)
            return result.text

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        raw_text = loop.run_until_complete(_run_ocr(processed_img))
        loop.close()

        cleaned = clean_ocr_text(raw_text)
        if cleaned:
            return cleaned
    except Exception as e:
        print(f"[High-Accuracy OCR Notice] WinRT OCR error/fallback: {e}")

    return ""

class WinRTOcrEngine:
    def recognize_region(self, x: int, y: int, w: int, h: int) -> str:
        try:
            bbox = (x, y, x + w, y + h)
            img = ImageGrab.grab(bbox=bbox)
            return perform_ocr_on_image(img)
        except Exception as e:
            print(f"Error capturing screen region: {e}")
            return ""

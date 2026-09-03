"""
core/image_analyzer.py
OCR analysis using pytesseract.
Gracefully handles missing dependencies.
"""

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

def extract_text(image_data) -> dict:
    """
    Extracts text from an image using OCR.
    Returns:
        {
            "success": bool,
            "text": str,
            "error": str,
            "warning": str
        }
    """
    result = {
        "success": False,
        "text": "",
        "error": None,
        "warning": None
    }

    if not HAS_PIL:
        result["error"] = "Pillow (PIL) is not installed. Cannot process images."
        return result

    if not HAS_TESSERACT:
        result["warning"] = "OCR is not available on this system. Please paste the message text manually."
        return result

    try:
        if isinstance(image_data, bytes):
            import io
            img = Image.open(io.BytesIO(image_data)).convert('RGB')
        else:
            img = image_data.convert('RGB')
            
        text = pytesseract.image_to_string(img)
        if text.strip():
            result["text"] = text.strip()
            result["success"] = True
        else:
            result["error"] = "No text could be extracted from the image. Please paste the message manually."
            
    except Exception as e:
        # pytesseract throws specific exceptions if the executable is not found
        if "tesseract is not installed or it's not in your PATH" in str(e):
            result["warning"] = "OCR is not available on this system. Please paste the message text manually."
        else:
            result["error"] = f"Error processing image for OCR: {str(e)}"

    return result

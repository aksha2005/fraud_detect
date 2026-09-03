import cv2
import numpy as np

def decode_qr(image):
    """Exact function name required by app.py"""
    try:
        # Streamlit passes bytes, so we decode it for OpenCV
        if isinstance(image, bytes):
            np_arr = np.frombuffer(image, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        elif not isinstance(image, np.ndarray):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)
        
        # Wrapped in the dictionary format that app.py strictly expects
        if data:
            return {"success": True, "text": data, "error": None, "warning": None}
        else:
            return {"success": False, "text": "", "error": "No QR detected", "warning": None}
    except Exception as e:
        return {"success": False, "text": "", "error": f"Error: {str(e)}", "warning": None}

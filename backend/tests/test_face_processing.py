import io
from PIL import Image

from app.services.face_processing import face_detector


def test_face_detector_returns_jpeg_bytes_for_blank_frame():
    img = Image.new("RGB", (320, 240), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    processed, roi = face_detector.detect(buf.getvalue())

    assert isinstance(processed, (bytes, bytearray))
    assert len(processed) > 0
    assert roi is None

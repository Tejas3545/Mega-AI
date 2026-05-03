import io
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

try:
    import mediapipe as mp
except Exception:
    mp = None


logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    x: int
    y: int
    width: int
    height: int
    confidence: float


class FaceDetector:
    def __init__(self) -> None:
        self._detector = None
        if mp is not None and hasattr(mp, "solutions"):
            self._detector = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.35,
            )
        else:
            mp_ver = getattr(mp, "__version__", "not-installed")
            logger.warning(
                "Mediapipe face solutions are unavailable (version=%s). ROI detection is disabled.",
                mp_ver,
            )

    def detect(self, image_bytes: bytes) -> tuple[bytes, Optional[DetectionResult]]:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(image)
        h, w, _ = arr.shape

        detection_result: Optional[DetectionResult] = None
        if self._detector is not None:
            result = self._detector.process(arr)
            if result.detections:
                det = result.detections[0]
                box = det.location_data.relative_bounding_box
                x = max(0, int(box.xmin * w))
                y = max(0, int(box.ymin * h))
                width = min(w - x, int(box.width * w))
                height = min(h - y, int(box.height * h))
                confidence = float(det.score[0])
                detection_result = DetectionResult(x=x, y=y, width=width, height=height, confidence=confidence)

                draw = ImageDraw.Draw(image)
                draw.rectangle([(x, y), (x + width, y + height)], outline=(0, 255, 0), width=3)

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85)
        return output.getvalue(), detection_result


class StreamState:
    def __init__(self) -> None:
        self._latest_frame: dict[str, bytes] = {}
        self._frame_no: dict[str, int] = defaultdict(int)
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

    def set_frame(self, stream_id: str, frame: bytes) -> int:
        with self._locks[stream_id]:
            self._frame_no[stream_id] += 1
            self._latest_frame[stream_id] = frame
            return self._frame_no[stream_id]

    def get_frame(self, stream_id: str) -> Optional[bytes]:
        with self._locks[stream_id]:
            return self._latest_frame.get(stream_id)


face_detector = FaceDetector()
stream_state = StreamState()

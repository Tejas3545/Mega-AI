import asyncio
import base64
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import FaceROI, VideoStream
from app.schemas.roi import ROIOut
from app.services.face_processing import face_detector, stream_state

router = APIRouter(prefix="/api/v1", tags=["stream"])


@router.post("/stream/frame")
async def ingest_frame(
    stream_id: str = Form(...),
    timestamp_ms: int = Form(...),
    frame: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if frame.content_type not in {"image/jpeg", "image/jpg", "image/png"}:
        raise HTTPException(status_code=400, detail="Frame must be JPEG or PNG")

    payload = await frame.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty frame")

    processed_frame, detection = face_detector.detect(payload)

    stream = await db.get(VideoStream, stream_id)
    if stream is None:
        db.add(VideoStream(id=stream_id))

    frame_number = stream_state.set_frame(stream_id, processed_frame)

    roi_payload = None
    if detection is not None:
        roi = FaceROI(
            stream_id=stream_id,
            frame_number=frame_number,
            x=detection.x,
            y=detection.y,
            width=detection.width,
            height=detection.height,
            confidence=detection.confidence,
            timestamp_ms=timestamp_ms,
        )
        db.add(roi)
        roi_payload = {
            "x": detection.x,
            "y": detection.y,
            "width": detection.width,
            "height": detection.height,
            "confidence": detection.confidence,
        }

    await db.commit()
    return {"status": "ok", "stream_id": stream_id, "frame_number": frame_number, "roi": roi_payload}


@router.get("/stream/{stream_id}/video")
async def stream_video(stream_id: str):
    boundary = "frame"

    async def generator():
        while True:
            frame_data = stream_state.get_frame(stream_id)
            if frame_data:
                yield (
                    f"--{boundary}\r\n"
                    "Content-Type: image/jpeg\r\n\r\n"
                ).encode("utf-8") + frame_data + b"\r\n"
            await asyncio.sleep(0.06)

    return StreamingResponse(generator(), media_type=f"multipart/x-mixed-replace; boundary={boundary}")


@router.get("/stream/{stream_id}/rois", response_model=list[ROIOut])
async def list_rois(stream_id: str, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        select(FaceROI).where(FaceROI.stream_id == stream_id).order_by(FaceROI.frame_number.desc()).limit(200)
    )
    return rows.scalars().all()


@router.websocket("/ws/stream/{stream_id}")
async def ws_stream(websocket: WebSocket, stream_id: str):
    await websocket.accept()
    try:
        while True:
            frame_data = stream_state.get_frame(stream_id)
            if frame_data:
                await websocket.send_json({
                    "stream_id": stream_id,
                    "image_base64": base64.b64encode(frame_data).decode("ascii"),
                })
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        return

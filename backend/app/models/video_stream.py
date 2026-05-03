from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class VideoStream(Base):
    __tablename__ = "video_streams"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rois = relationship("FaceROI", back_populates="stream", cascade="all, delete-orphan")

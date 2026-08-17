from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, new_uuid, utcnow
from app.models.enums import MessageRole


class StoryMessage(Base):
    __tablename__ = "story_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    save_slot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("save_slots.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            native_enum=False,
            length=16,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)

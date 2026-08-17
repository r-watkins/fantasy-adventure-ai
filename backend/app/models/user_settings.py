from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow
from app.models.enums import ThemePreference


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    theme_preference: Mapped[ThemePreference] = mapped_column(
        Enum(
            ThemePreference,
            native_enum=False,
            length=8,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ThemePreference.SYSTEM,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

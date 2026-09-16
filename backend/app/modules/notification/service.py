import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.modules.notification.models import Notification, NotificationPreference
from app.modules.notification.schemas import NotificationCreate, PreferenceUpdate

class NotificationService:
    @staticmethod
    async def create_notification(db: AsyncSession, payload: NotificationCreate) -> Notification:
        notification = Notification(
            user_id=payload.user_id,
            role=payload.role,
            title=payload.title,
            message=payload.message,
            type=payload.type,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(notification)
        await db.flush()
        return notification

    @staticmethod
    async def get_notifications_for_user(
        db: AsyncSession, user_id: Optional[str] = None, role: Optional[str] = None, unread_only: bool = False
    ) -> List[Notification]:
        stmt = select(Notification)
        
        conditions = []
        if user_id:
            conditions.append(Notification.user_id == user_id)
        if role:
            conditions.append(Notification.role == role)
            
        if conditions:
            stmt = stmt.where(or_(*conditions))
        else:
            stmt = stmt.where(Notification.role.is_(None), Notification.user_id.is_(None))

        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))

        stmt = stmt.order_by(Notification.created_at.desc())
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def mark_as_read(db: AsyncSession, notification_id: str) -> bool:
        try:
            n_uuid = uuid.UUID(notification_id)
            stmt = select(Notification).where(Notification.id == n_uuid)
        except ValueError:
            stmt = select(Notification).where(Notification.user_id == notification_id)

        res = await db.execute(stmt)
        notification = res.scalars().first()
        if not notification:
            return False

        notification.is_read = True
        db.add(notification)
        await db.flush()
        return True

    @staticmethod
    async def mark_all_read(db: AsyncSession, user_id: Optional[str] = None, role: Optional[str] = None) -> int:
        stmt = select(Notification).where(Notification.is_read.is_(False))
        conditions = []
        if user_id:
            conditions.append(Notification.user_id == user_id)
        if role:
            conditions.append(Notification.role == role)

        if conditions:
            stmt = stmt.where(or_(*conditions))

        res = await db.execute(stmt)
        notifications = res.scalars().all()
        count = 0
        for n in notifications:
            n.is_read = True
            db.add(n)
            count += 1
        await db.flush()
        return count

    @staticmethod
    async def get_or_create_preference(db: AsyncSession, user_id: str) -> NotificationPreference:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        res = await db.execute(stmt)
        pref = res.scalars().first()

        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                email_enabled=True,
                push_enabled=True,
                min_freshness_threshold=50.0,
                storage_alerts_enabled=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(pref)
            await db.flush()

        return pref

    @staticmethod
    async def update_preference(db: AsyncSession, user_id: str, data: PreferenceUpdate) -> NotificationPreference:
        pref = await NotificationService.get_or_create_preference(db, user_id)
        if data.email_enabled is not None:
            pref.email_enabled = data.email_enabled
        if data.push_enabled is not None:
            pref.push_enabled = data.push_enabled
        if data.min_freshness_threshold is not None:
            pref.min_freshness_threshold = data.min_freshness_threshold
        if data.storage_alerts_enabled is not None:
            pref.storage_alerts_enabled = data.storage_alerts_enabled

        db.add(pref)
        await db.flush()
        return pref

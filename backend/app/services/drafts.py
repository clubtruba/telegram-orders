from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DraftStatus, Item, ItemDraft, ItemStatus


class DraftError(ValueError):
    pass


@dataclass(frozen=True)
class OpenDraftCommand:
    customer_user_id: UUID
    telegram_chat_id: int
    telegram_message_id: int
    product_url: str


class DraftService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def open(self, command: OpenDraftCommand) -> ItemDraft:
        existing = await self.session.scalar(select(ItemDraft).where(
            ItemDraft.telegram_chat_id == command.telegram_chat_id,
            ItemDraft.telegram_message_id == command.telegram_message_id))
        if existing is not None:
            return existing
        draft = ItemDraft(customer_user_id=command.customer_user_id,
            telegram_chat_id=command.telegram_chat_id, telegram_message_id=command.telegram_message_id,
            product_url=command.product_url, quantity=1, status=DraftStatus.OPEN,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7))
        self.session.add(draft)
        await self.session.flush()
        return draft

    async def set_size(self, draft_id: UUID, user_id: UUID, size: str | None) -> ItemDraft:
        draft = await self._locked_open_draft(draft_id, user_id)
        draft.size = size
        await self.session.flush()
        return draft

    async def confirm(self, draft_id: UUID, user_id: UUID, customer_id: UUID) -> Item:
        draft = await self._locked_open_draft(draft_id, user_id)
        item = Item(customer_id=customer_id, product_url=draft.product_url, size=draft.size,
            color=draft.color, quantity=draft.quantity, customer_note=draft.customer_note,
            status=ItemStatus.TO_BUY)
        self.session.add(item)
        draft.status = DraftStatus.CONFIRMED
        await self.session.flush()
        return item

    async def _locked_open_draft(self, draft_id: UUID, user_id: UUID) -> ItemDraft:
        draft = await self.session.scalar(select(ItemDraft).where(
            ItemDraft.id == draft_id, ItemDraft.customer_user_id == user_id).with_for_update())
        if draft is None:
            raise DraftError("draft not found")
        if draft.status is not DraftStatus.OPEN:
            raise DraftError("draft is no longer open")
        if draft.expires_at < datetime.now(timezone.utc):
            draft.status = DraftStatus.EXPIRED
            raise DraftError("draft has expired")
        return draft

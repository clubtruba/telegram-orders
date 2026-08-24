import pytest
from sqlalchemy import select

from app.db.session import SessionFactory
from app.models import DraftStatus, Item, ItemDraft
from app.services.drafts import DraftError, DraftService, OpenDraftCommand
from app.services.users import UserService


@pytest.mark.asyncio
async def test_parallel_drafts_remain_isolated_and_duplicate_confirmation_is_blocked():
    async with SessionFactory() as session:
        async with session.begin():
            user, customer = await UserService(session).register_customer(
                9_000_000_002, "Parallel", "Customer", "parallel_customer"
            )
            service = DraftService(session)
            first = await service.open(OpenDraftCommand(user.id, 9_000_000_002, 101, "https://example.com/a"))
            second = await service.open(OpenDraftCommand(user.id, 9_000_000_002, 102, "https://example.com/b"))
            repeated = await service.open(OpenDraftCommand(user.id, 9_000_000_002, 101, "https://example.com/a"))
            assert repeated.id == first.id

            await service.set_size(first.id, user.id, "M")
            await service.set_size(second.id, user.id, "S")
            item = await service.confirm(first.id, user.id, customer.id)
            await session.flush()

            assert item.size == "M"
            assert first.status is DraftStatus.CONFIRMED
            assert second.status is DraftStatus.OPEN
            assert await session.scalar(select(Item).where(Item.id == item.id))
            assert await session.scalar(select(ItemDraft).where(ItemDraft.id == second.id))
            with pytest.raises(DraftError, match="no longer open"):
                await service.confirm(first.id, user.id, customer.id)

            await session.rollback()

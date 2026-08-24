import pytest
from sqlalchemy import select

from app.db.session import SessionFactory
from app.models import (
    AppUser,
    CollectionStatus,
    Customer,
    CustomerAddress,
    Item,
    ItemStatus,
    ItemStatusHistory,
    ShipmentItem,
    UserRole,
)
from app.services.shipments import CreateShipmentCommand, ShipmentService


@pytest.mark.asyncio
async def test_create_shipment_snapshots_address_and_reserves_item():
    async with SessionFactory() as session:
        async with session.begin():
            user = AppUser(
                telegram_user_id=9_000_000_001,
                role=UserRole.ADMIN,
                username="integration_admin",
                first_name="Integration",
                last_name="Admin",
            )
            session.add(user)
            await session.flush()
            customer = Customer(
                app_user_id=None,
                display_name="Test Customer",
                collection_status=CollectionStatus.COLLECTING,
                financial_details_visible=False,
            )
            session.add(customer)
            await session.flush()
            address = CustomerAddress(
                customer_id=customer.id,
                label="Home",
                recipient_name="Original Name",
                country_code="RU",
                postal_code="162600",
                city="Cherepovets",
                address_line1="Original address",
                is_default=True,
            )
            item = Item(
                customer_id=customer.id,
                product_url="https://example.com/product",
                quantity=1,
                status=ItemStatus.RECEIVED,
            )
            session.add_all([address, item])
            await session.flush()

            shipment = await ShipmentService(session).create(
                CreateShipmentCommand(
                    customer_id=customer.id,
                    address_id=address.id,
                    item_ids=(item.id,),
                    actor_user_id=user.id,
                )
            )
            address.recipient_name = "Changed Later"
            await session.flush()

            assert shipment.address_recipient_name == "Original Name"
            assert item.status is ItemStatus.ASSIGNED_TO_SHIPMENT
            assert await session.scalar(
                select(ShipmentItem).where(ShipmentItem.item_id == item.id)
            )
            history = await session.scalar(
                select(ItemStatusHistory).where(ItemStatusHistory.item_id == item.id)
            )
            assert history is not None
            assert history.from_status is ItemStatus.RECEIVED
            assert history.to_status is ItemStatus.ASSIGNED_TO_SHIPMENT

            await session.rollback()

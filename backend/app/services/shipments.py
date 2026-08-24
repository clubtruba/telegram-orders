from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CustomerAddress,
    CustomerShipment,
    AuditLog,
    Item,
    ItemStatus,
    ItemStatusHistory,
    ShipmentItem,
    ShipmentStatus,
)


class ShipmentValidationError(ValueError):
    pass


@dataclass(frozen=True)
class CreateShipmentCommand:
    customer_id: UUID
    address_id: UUID
    item_ids: tuple[UUID, ...]
    actor_user_id: UUID
    currency: str = "EUR"


class ShipmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, command: CreateShipmentCommand) -> CustomerShipment:
        if not command.item_ids:
            raise ShipmentValidationError("shipment requires at least one item")
        if len(set(command.item_ids)) != len(command.item_ids):
            raise ShipmentValidationError("duplicate item ids are not allowed")
        if len(command.currency) != 3:
            raise ShipmentValidationError("currency must be an ISO 4217 code")

        address = await self.session.scalar(
            select(CustomerAddress)
            .where(
                CustomerAddress.id == command.address_id,
                CustomerAddress.customer_id == command.customer_id,
            )
            .with_for_update()
        )
        if address is None:
            raise ShipmentValidationError("address does not belong to customer")

        items = list(
            (
                await self.session.scalars(
                    select(Item).where(Item.id.in_(command.item_ids)).with_for_update()
                )
            ).all()
        )
        if len(items) != len(command.item_ids):
            raise ShipmentValidationError("one or more items do not exist")
        if any(item.customer_id != command.customer_id for item in items):
            raise ShipmentValidationError("all items must belong to the shipment customer")
        if any(item.status is not ItemStatus.RECEIVED for item in items):
            raise ShipmentValidationError("only RECEIVED items can be assigned")

        shipment = CustomerShipment(
            customer_id=command.customer_id,
            status=ShipmentStatus.PREPARING,
            currency=command.currency.upper(),
            shipping_cost=Decimal("0"),
            packaging_cost=Decimal("0"),
            insurance_cost=Decimal("0"),
            customs_fee=Decimal("0"),
            other_fee=Decimal("0"),
            address_recipient_name=address.recipient_name,
            address_phone=address.phone,
            address_country_code=address.country_code,
            address_postal_code=address.postal_code,
            address_region=address.region,
            address_city=address.city,
            address_line1=address.address_line1,
            address_line2=address.address_line2,
        )
        self.session.add(shipment)
        await self.session.flush()

        for item in items:
            item.status = ItemStatus.ASSIGNED_TO_SHIPMENT
            self.session.add(ShipmentItem(shipment_id=shipment.id, item_id=item.id))
            self.session.add(
                ItemStatusHistory(
                    item_id=item.id,
                    from_status=ItemStatus.RECEIVED,
                    to_status=ItemStatus.ASSIGNED_TO_SHIPMENT,
                    changed_by_user_id=command.actor_user_id,
                    reason=f"assigned to shipment {shipment.id}",
                )
            )
        self.session.add(
            AuditLog(
                actor_user_id=command.actor_user_id,
                action="SHIPMENT_CREATED",
                entity_type="CustomerShipment",
                entity_id=shipment.id,
                payload={
                    "customer_id": str(command.customer_id),
                    "address_id": str(command.address_id),
                    "item_ids": [str(item.id) for item in items],
                },
            )
        )
        await self.session.flush()
        return shipment

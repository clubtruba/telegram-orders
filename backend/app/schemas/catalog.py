from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import CollectionStatus, ItemStatus


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    customer_id: UUID
    product_url: str
    size: str | None
    color: str | None
    quantity: int
    customer_note: str | None
    status: ItemStatus
    listed_price: Decimal | None
    listed_currency: str | None
    created_at: datetime


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_name: str
    phone: str | None
    collection_status: CollectionStatus


class DashboardResponse(BaseModel):
    to_buy: int
    on_the_way: int
    received: int
    assigned_to_shipment: int

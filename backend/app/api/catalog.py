from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RequestActor, get_request_actor
from app.db.session import get_session
from app.models import Customer, Item, ItemStatus, UserRole
from app.schemas.catalog import CustomerResponse, DashboardResponse, ItemResponse

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_request_actor)])


@router.get("/items", response_model=list[ItemResponse], tags=["items"])
async def list_items(actor: RequestActor = Depends(get_request_actor),
                     session: AsyncSession = Depends(get_session)):
    query = select(Item).order_by(Item.created_at.desc())
    if actor.role is UserRole.CUSTOMER:
        if actor.customer_id is None:
            return []
        query = query.where(Item.customer_id == actor.customer_id)
    return list((await session.scalars(query)).all())


@router.get("/items/{item_id}", response_model=ItemResponse, tags=["items"])
async def get_item(item_id: UUID, actor: RequestActor = Depends(get_request_actor),
                   session: AsyncSession = Depends(get_session)):
    item = await session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    actor.require_customer_access(item.customer_id)
    return item


@router.get("/customers/{customer_id}", response_model=CustomerResponse, tags=["customers"])
async def get_customer(customer_id: UUID, actor: RequestActor = Depends(get_request_actor),
                       session: AsyncSession = Depends(get_session)):
    actor.require_customer_access(customer_id)
    customer = await session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.get("/admin/customers", response_model=list[CustomerResponse], tags=["admin"])
async def admin_customers(actor: RequestActor = Depends(get_request_actor),
                          session: AsyncSession = Depends(get_session)):
    actor.require_admin()
    return list((await session.scalars(select(Customer).order_by(Customer.display_name))).all())


@router.get("/dashboard", response_model=DashboardResponse, tags=["dashboard"])
async def dashboard(actor: RequestActor = Depends(get_request_actor),
                    session: AsyncSession = Depends(get_session)):
    query = select(Item.status, func.count(Item.id)).group_by(Item.status)
    if actor.role is UserRole.CUSTOMER:
        if actor.customer_id is None:
            counts = {}
        else:
            counts = dict((await session.execute(query.where(
                Item.customer_id == actor.customer_id))).all())
    else:
        counts = dict((await session.execute(query)).all())
    return DashboardResponse(
        to_buy=counts.get(ItemStatus.TO_BUY, 0),
        on_the_way=counts.get(ItemStatus.ON_THE_WAY_TO_US, 0),
        received=counts.get(ItemStatus.RECEIVED, 0),
        assigned_to_shipment=counts.get(ItemStatus.ASSIGNED_TO_SHIPMENT, 0),
    )


@router.get("/admin/warehouse", response_model=list[ItemResponse], tags=["admin"])
async def warehouse(actor: RequestActor = Depends(get_request_actor),
                    session: AsyncSession = Depends(get_session)):
    actor.require_admin()
    query = select(Item).where(Item.status.in_([
        ItemStatus.RECEIVED, ItemStatus.ASSIGNED_TO_SHIPMENT])).order_by(Item.customer_id)
    return list((await session.scalars(query)).all())

"""Account management REST endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas import (
    AccountResponse,
    CreateAccountRequest,
)
from app.services.portfolio import PortfolioService

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    body: CreateAccountRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new trading account.

    For simulated accounts, an initial balance is allocated.
    For live accounts, api_key and api_secret are required.
    """
    svc = PortfolioService(db)

    if body.account_type == "live" and (not body.api_key or not body.api_secret):
        raise HTTPException(
            status_code=400,
            detail="Live accounts require api_key and api_secret",
        )

    if body.account_type == "simulated" and (body.api_key or body.api_secret):
        raise HTTPException(
            status_code=400,
            detail="Simulated accounts must not have api_key or api_secret",
        )

    try:
        account = await svc.create_account(
            name=body.name,
            account_type=body.account_type.value,
            quote_asset=body.quote_asset,
            initial_balance=body.initial_balance,
            api_key=body.api_key,
            api_secret=body.api_secret,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AccountResponse(
        id=str(account.id),
        name=account.name,
        account_type=account.account_type,
        quote_asset=account.quote_asset,
        initial_balance=str(account.initial_balance),
        status=account.status,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get account details by account_id."""
    svc = PortfolioService(db)
    try:
        aid = uuid.UUID(account_id)
        account = await svc.get_account(aid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id format")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return AccountResponse(
        id=str(account.id),
        name=account.name,
        account_type=account.account_type,
        quote_asset=account.quote_asset,
        initial_balance=str(account.initial_balance),
        status=account.status,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )

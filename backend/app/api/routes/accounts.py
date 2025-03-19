
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Account, AccountCreate, AccountPublic, AccountUpdate, Message

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=list[AccountPublic])
def read_accounts(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve accounts.
    """
    if current_user.is_superuser:
        statement = select(Account).offset(skip).limit(limit)
    else:
        statement = (
            select(Account)
            .where(Account.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
    accounts = session.exec(statement).all()
    return accounts


@router.get("/{id}", response_model=AccountPublic)
def read_account(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get account by ID.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not current_user.is_superuser and (account.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return account


@router.post("/", response_model=AccountPublic)
def create_account(
    *, session: SessionDep, current_user: CurrentUser, account_in: AccountCreate
) -> Any:
    """
    Create new account.
    """
    account = Account.model_validate(account_in, update={"user_id": current_user.id})
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.post("/{id}", response_model=AccountPublic)
def update_account(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    account_in: AccountUpdate,
) -> Any:
    """
    Update an account.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not current_user.is_superuser and (account.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    update_dict = account_in.model_dump(exclude_unset=True)
    account.sqlmodel_update(update_dict)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.delete("/{id}")
def delete_account(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an account.
    """
    account = session.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not current_user.is_superuser and (account.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(account)
    session.commit()
    return Message(message="Account deleted successfully")


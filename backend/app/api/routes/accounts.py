
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import func, select
import httpx

from app.api.deps import CurrentUser, SessionDep
from app.models import Account, AccountCreate, AccountPublic, AccountUpdate, Message, AccountType, UberAccountConnect, \
    UberOAuthResponse, LyftAccountConnect, LyftOAuthResponse
from app.core.config import settings

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

@router.post("/uber/connect", response_model=AccountPublic)
async def connect_uber_account(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    auth_data: UberAccountConnect
) -> Any:
    """
    Connect Uber account using OAuth authorization code.
    """
    try:
        # Exchange authorization code for access token
        token_url = "https://auth.uber.com/oauth/v2/token"
        data = {
            "client_id": settings.UBER_CLIENT_ID,
            "client_secret": settings.UBER_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": auth_data.code,
            "redirect_uri": settings.UBER_REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to obtain Uber access token"
                )
            
            oauth_response = UberOAuthResponse(**response.json())
            
            # Get Uber account details
            uber_api_url = "https://api.uber.com/v1/me"
            headers = {
                "Authorization": f"Bearer {oauth_response.access_token}"
            }
            
            user_response = await client.get(uber_api_url, headers=headers)
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch Uber account details"
                )
            
            uber_user_data = user_response.json()
            
            # Check if account already exists
            existing_account = session.exec(
                select(Account)
                .where(Account.user_id == current_user.id)
                .where(Account.type == AccountType.UBER)
            ).first()
            
            if existing_account:
                # Update existing account
                existing_account.token = oauth_response.access_token
                existing_account.connection_status = True
                existing_account.description = f"Connected Uber account: {uber_user_data.get('email')}"
                session.add(existing_account)
                session.commit()
                session.refresh(existing_account)
                return existing_account
            
            # Create new account
            account_data = AccountCreate(
                type=AccountType.UBER,
                token=oauth_response.access_token,
                connection_status=True,
                description=f"Connected Uber account: {uber_user_data.get('email')}"
            )
            
            new_account = Account.model_validate(
                account_data,
                update={"user_id": current_user.id}
            )
            session.add(new_account)
            session.commit()
            session.refresh(new_account)
            
            return new_account
            
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Error communicating with Uber services"
        )

@router.post("/uber/disconnect/{account_id}")
async def disconnect_uber_account(
    account_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Message:
    """
    Disconnect Uber account.
    """
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not current_user.is_superuser and (account.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    if account.type != AccountType.UBER:
        raise HTTPException(status_code=400, detail="Not an Uber account")
    
    try:
        if account.token:
            # Revoke Uber access token
            revoke_url = "https://auth.uber.com/oauth/v2/revoke"
            data = {
                "client_id": settings.UBER_CLIENT_ID,
                "client_secret": settings.UBER_CLIENT_SECRET,
                "token": account.token
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(revoke_url, data=data)
        
        # Update account status
        account.token = None
        account.connection_status = False
        account.description = "Disconnected Uber account"
        session.add(account)
        session.commit()
        
        return Message(message="Uber account disconnected successfully")
        
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Error communicating with Uber services"
        )

@router.get("/uber/status/{account_id}")
async def check_uber_connection_status(
    account_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> dict:
    """
    Check Uber account connection status.
    """
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not current_user.is_superuser and (account.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    if account.type != AccountType.UBER:
        raise HTTPException(status_code=400, detail="Not an Uber account")
    
    return {
        "account_id": account.id,
        "connection_status": account.connection_status,
        "last_updated": account.last_updated
    }

@router.post("/lyft/connect", response_model=AccountPublic)
async def connect_lyft_account(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    auth_data: LyftAccountConnect
) -> Any:
    """
    Connect Lyft account using OAuth authorization code.
    """
    try:
        # Exchange authorization code for access token
        token_url = "https://api.lyft.com/oauth/token"
        data = {
            "client_id": settings.LYFT_CLIENT_ID,
            "client_secret": settings.LYFT_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": auth_data.code,
            "redirect_uri": settings.LYFT_REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url, 
                data=data,
                auth=(settings.LYFT_CLIENT_ID, settings.LYFT_CLIENT_SECRET)
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to obtain Lyft access token"
                )
            
            oauth_response = LyftOAuthResponse(**response.json())
            
            # Get Lyft account details
            lyft_api_url = "https://api.lyft.com/v1/profile"
            headers = {
                "Authorization": f"Bearer {oauth_response.access_token}"
            }
            
            user_response = await client.get(lyft_api_url, headers=headers)
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch Lyft account details"
                )
            
            lyft_user_data = user_response.json()
            
            # Check if account already exists
            existing_account = session.exec(
                select(Account)
                .where(Account.user_id == current_user.id)
                .where(Account.type == AccountType.LYFT)
            ).first()
            
            if existing_account:
                # Update existing account
                existing_account.token = oauth_response.access_token
                existing_account.connection_status = True
                existing_account.description = f"Connected Lyft account: {lyft_user_data.get('id')}"
                session.add(existing_account)
                session.commit()
                session.refresh(existing_account)
                return existing_account
            
            # Create new account
            account_data = AccountCreate(
                type=AccountType.LYFT,
                token=oauth_response.access_token,
                connection_status=True,
                description=f"Connected Lyft account: {lyft_user_data.get('id')}"
            )
            
            new_account = Account.model_validate(
                account_data,
                update={"user_id": current_user.id}
            )
            session.add(new_account)
            session.commit()
            session.refresh(new_account)
            
            return new_account
            
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Error communicating with Lyft services"
        )

@router.post("/lyft/disconnect/{account_id}")
async def disconnect_lyft_account(
    account_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Message:
    """
    Disconnect Lyft account.
    """
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not current_user.is_superuser and (account.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    if account.type != AccountType.LYFT:
        raise HTTPException(status_code=400, detail="Not a Lyft account")
    
    try:
        if account.token:
            # Revoke Lyft access token
            revoke_url = "https://api.lyft.com/oauth/revoke_refresh_token"
            headers = {
                "Authorization": f"Bearer {account.token}"
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(revoke_url, headers=headers)
        
        # Update account status
        account.token = None
        account.connection_status = False
        account.description = "Disconnected Lyft account"
        session.add(account)
        session.commit()
        
        return Message(message="Lyft account disconnected successfully")
        
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Error communicating with Lyft services"
        )

@router.get("/lyft/status/{account_id}")
async def check_lyft_connection_status(
    account_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> dict:
    """
    Check Lyft account connection status.
    """
    account = session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not current_user.is_superuser and (account.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    if account.type != AccountType.LYFT:
        raise HTTPException(status_code=400, detail="Not a Lyft account")
    
    return {
        "account_id": account.id,
        "connection_status": account.connection_status,
        "last_updated": account.last_updated
    }


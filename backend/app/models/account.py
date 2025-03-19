import uuid
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

class AccountType(str, Enum):
    SAVINGS = "savings"
    CHECKING = "checking"
    CREDIT = "credit"
    INVESTMENT = "investment"
    WALLET = "wallet"

##
#---------------------------------------- Account Model -------------------------------------------
##

# Shared properties
class AccountBase(SQLModel):
    type: AccountType = Field(default=AccountType.WALLET)
    balance: float = Field(default=0.0)
    token: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    description: str | None = Field(default=None, max_length=255)

# Properties to receive on account creation
class AccountCreate(AccountBase):
    pass

# Properties to receive on account update
class AccountUpdate(SQLModel):
    type: AccountType | None = None
    balance: float | None = None
    token: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    description: str | None = Field(default=None, max_length=255)

# Database model
class Account(AccountBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    user: "User" = Relationship(back_populates="accounts")

# Properties to return via API
class AccountPublic(AccountBase):
    id: uuid.UUID
    user_id: uuid.UUID

# Response model for multiple accounts
class AccountsPublic(SQLModel):
    data: list[AccountPublic]
    count: int

# Response model for account balance
class AccountBalance(SQLModel):
    balance: float
    last_updated: datetime

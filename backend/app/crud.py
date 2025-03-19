import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate, Account, AccountCreate, AccountUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def create_account(*, session: Session, account_in: AccountCreate, user_id: uuid.UUID) -> Account:
    db_account = Account.model_validate(account_in, update={"user_id": user_id})
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    return db_account


def get_account(*, session: Session, account_id: uuid.UUID) -> Account | None:
    return session.get(Account, account_id)


def get_accounts_by_user(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Account]:
    statement = (
        select(Account)
        .where(Account.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def update_account(
    *, session: Session, db_account: Account, account_in: AccountUpdate
) -> Account:
    update_data = account_in.model_dump(exclude_unset=True)
    db_account.sqlmodel_update(update_data)
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    return db_account


def delete_account(*, session: Session, account_id: uuid.UUID) -> None:
    account = session.get(Account, account_id)
    if account:
        session.delete(account)
        session.commit()

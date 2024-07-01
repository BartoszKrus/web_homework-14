from typing import List, Optional

from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, extract

from src.database.models import Contact, User
from src.schemas import ContactUpdate, ContactCreate


async def get_contacts(skip: int, limit: int, user: User, db: Session) -> List[Contact]:
    """
    Retrieve a list of contacts for a user, with pagination.

    :param skip: The number of contacts to skip for pagination.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param user: The current authenticated user.
    :type user: User
    :param db: The database session dependency.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[Contact]
    """
    return db.query(Contact).filter(Contact.owner_id == user.id).offset(skip).limit(limit).all()


async def get_contact(contact_id: int, user: User, db: Session) -> Contact:
    """
    Retrieve a single contact by its ID.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param user: The current authenticated user.
    :type user: User
    :param db: The database session dependency.
    :type db: Session
    :return: The contact with the specified ID, or None if not found.
    :rtype: Contact
    """
    return db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == user.id).first()


async def create_contact(body: ContactCreate, user: User, db: Session) -> Contact:
    """
    Create a new contact for a user.

    :param body: The contact details.
    :type body: ContactCreate
    :param user: The current authenticated user.
    :type user: User
    :param db: The database session dependency.
    :type db: Session
    :return: The created contact.
    :rtype: Contact
    """
    contact = Contact(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone_number=body.phone_number,
        birth_date=body.birth_date,
        additional_info=body.additional_info,
        owner_id=user.id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdate, user: User, db: Session) -> Contact | None:
    """
    Update an existing contact.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated contact details.
    :type body: ContactUpdate
    :param user: The current authenticated user.
    :type user: User
    :param db: The database session dependency.
    :type db: Session
    :return: The updated contact, or None if not found.
    :rtype: Contact | None
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == user.id).first()
    if db_contact:
        db_contact.first_name = body.first_name
        db_contact.last_name = body.last_name
        db_contact.email = body.email
        db_contact.phone_number = body.phone_number
        db_contact.birth_date = body.birth_date
        db_contact.additional_info = body.additional_info
        db.commit()
        db.refresh(db_contact)
    return db_contact


async def remove_contact(contact_id: int, user: User, db: Session) -> Contact | None:
    """
    Remove a contact by its ID.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param user: The current authenticated user.
    :type user: User
    :param db: The database session dependency.
    :type db: Session
    :return: The removed contact, or None if not found.
    :rtype: Contact | None
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == user.id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def search_contact(first_name: Optional[str], last_name: Optional[str], email: Optional[str], user: User, db: Session) -> List[Contact]:
    """
    Search for contacts based on the provided criteria.

    :param first_name: The first name to search for (optional).
    :type first_name: Optional[str]
    :param last_name: The last name to search for (optional).
    :type last_name: Optional[str]
    :param email: The email address to search for (optional).
    :type email: Optional[str]
    :param user: The current authenticated user.
    :type user: User
    :param db: The database session dependency.
    :type db: Session
    :return: A list of contacts matching the search criteria.
    :rtype: List[Contact]
    """
    query = db.query(Contact).filter(Contact.owner_id == user.id)
    if first_name:
        query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    return query.all()


async def get_upcoming_birthdays(user: User, db: Session) -> List[Contact]:
    """
    Retrieve a list of contacts with upcoming birthdays within the next 7 days.

    :param user: The current authenticated user.
    :type user: User
    :param db: The database session dependency.
    :type db: Session
    :return: A list of contacts with birthdays within the next 7 days.
    :rtype: List[Contact]
    """
    today = datetime.now().date()
    seven_days_later = today + timedelta(days=7)
    upcoming_birthdays = db.query(Contact).filter(
        Contact.owner_id == user.id,
        or_(
            and_(
                extract('month', Contact.birth_date) == today.month,
                extract('day', Contact.birth_date) >= today.day,
                extract('day', Contact.birth_date) < (today.day + 7)
            ),
            and_(
                extract('month', Contact.birth_date) == (today.replace(month=today.month % 12 + 1)).month,
                extract('day', Contact.birth_date) <= seven_days_later.day
            )
        )
    ).all()
    filtered_birthdays = [
        contact for contact in upcoming_birthdays
        if (datetime(today.year, contact.birth_date.month, contact.birth_date.day).date() - today).days in range(7)
        or (datetime(today.year + 1, contact.birth_date.month, contact.birth_date.day).date() - today).days in range(7)
    ]    
    return filtered_birthdays
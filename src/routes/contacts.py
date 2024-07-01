from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status

from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import ContactResponse, ContactCreate, ContactUpdate
from src.repository import contacts
from src.services.auth import auth_service
from src.database.models import User, Contact

from fastapi_limiter.depends import RateLimiter


router = APIRouter(prefix='/contacts', tags=["contacts"])


@router.post("/create", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Create a new contact for the current user.

    This endpoint allows the user to create a new contact. It checks if a contact with the same email 
    already exists for the user and raises an error if it does.

    :param contact: The contact details to be created.
    :type contact: ContactCreate
    :param db: The database session dependency.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The created contact's details.
    :rtype: ContactResponse
    """
    existing_contact = db.query(Contact).filter(Contact.email == contact.email, Contact.owner_id == current_user.id).first()
    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact with this email already exists."
        )
    return await contacts.create_contact(contact, current_user, db)


@router.get("/read_contacts", response_model=List[ContactResponse], description="No more than 10 requests per minute", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Read a list of contacts for the current user.

    This endpoint allows the user to retrieve a list of their contacts. The response is paginated, 
    allowing the user to specify how many contacts to skip and the limit on the number of contacts returned.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param db: The database session dependency.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: A list of the user's contacts.
    :rtype: List[ContactResponse]
    """
    return await contacts.get_contacts(skip, limit, current_user, db)


@router.get("/read_contact/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Read a specific contact by its ID.

    This endpoint allows the user to retrieve details of a specific contact using its ID.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session dependency.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The contact's details.
    :rtype: ContactResponse
    """
    db_contact = await contacts.get_contact(contact_id, current_user, db)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@router.put("/update_contact/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Update an existing contact.

    This endpoint allows the user to update details of an existing contact using its ID.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated contact details.
    :type body: ContactUpdate
    :param db: The database session dependency.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The updated contact's details.
    :rtype: ContactResponse
    """
    db_contact = await contacts.update_contact(contact_id, body, current_user, db)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@router.delete("/delete_contact/{contact_id}", response_model=ContactResponse)
async def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Delete a contact by its ID.

    This endpoint allows the user to delete a contact using its ID.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: The database session dependency.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The details of the deleted contact.
    :rtype: ContactResponse
    """
    db_contact = await contacts.remove_contact(contact_id, current_user, db)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(first_name: Optional[str] = Query(None), last_name: Optional[str] = Query(None), email: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Search for contacts based on query parameters.

    This endpoint allows the user to search for contacts using first name, last name, or email as 
    query parameters.

    :param first_name: The first name of the contact to search for.
    :type first_name: Optional[str]
    :param last_name: The last name of the contact to search for.
    :type last_name: Optional[str]
    :param email: The email of the contact to search for.
    :type email: Optional[str]
    :param db: The database session dependency.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: A list of contacts matching the search criteria.
    :rtype: List[ContactResponse]
    """
    db_contacts = await contacts.search_contact(first_name, last_name, email, current_user, db)
    if db_contacts is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contacts


@router.get("/birthdays", response_model=List[ContactResponse])
async def get_upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Get contacts with upcoming birthdays.

    This endpoint allows the user to retrieve a list of contacts who have birthdays coming up.

    :param db: The database session dependency.
    :type db: Session
    :param current_user: The current authenticated user.
    :type current_user: User
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[ContactResponse]
    """
    db_contacts = await contacts.get_upcoming_birthdays(current_user, db)
    if db_contacts is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contacts








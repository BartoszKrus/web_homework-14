from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel

from libgravatar import Gravatar


async def get_user_by_email(email: str, db: Session) -> User:
    """
    Retrieve a user by their email address.

    :param email: The email address of the user to retrieve.
    :type email: str
    :param db: The database session dependency.
    :type db: Session
    :return: The user with the specified email, or None if no user is found.
    :rtype: User
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    Create a new user.

    This function creates a new user and assigns an avatar using the Gravatar service if possible.

    :param body: The user details.
    :type body: UserModel
    :param db: The database session dependency.
    :type db: Session
    :return: The created user, or None if a user with the same email already exists.
    :rtype: User
    """
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        return None
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.model_dump(), avatar=avatar) #dict()
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    Update the refresh token for a user.

    :param user: The user whose token is to be updated.
    :type user: User
    :param token: The new token value, or None to remove the token.
    :type token: str | None
    :param db: The database session dependency.
    :type db: Session
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """
    Confirm the email address of a user.

    This function sets the user's confirmed status to True.

    :param email: The email address of the user to confirm.
    :type email: str
    :param db: The database session dependency.
    :type db: Session
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    """
    Update the avatar URL for a user.

    :param email: The email address of the user whose avatar is to be updated.
    :type email: str
    :param url: The new avatar URL.
    :type url: str
    :param db: The database session dependency.
    :type db: Session
    :return: The updated user.
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user
from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

import cloudinary
import cloudinary.uploader

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail, UserDb
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email
from src.database.models import User
from src.conf.config import settings


router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Register a new user.

    This endpoint allows a new user to sign up by providing their details. If the email is already 
    in use, it returns a conflict error. Upon successful registration, a confirmation email is sent 
    in the background.

    :param body: The user details for signing up.
    :type body: UserModel
    :param background_tasks: Background tasks for sending the confirmation email.
    :type background_tasks: BackgroundTasks
    :param request: The HTTP request object.
    :type request: Request
    :param db: The database session dependency.
    :type db: Session
    :return: A dictionary with the new user's details and a success message.
    :rtype: dict
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created"}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return access and refresh tokens.

    This endpoint allows a user to log in by providing their credentials. It checks the user's 
    email, confirmation status, and password. Upon successful authentication, it returns the 
    access and refresh tokens.

    :param body: The login form containing username (email) and password.
    :type body: OAuth2PasswordRequestForm
    :param db: The database session dependency.
    :type db: Session
    :return: A dictionary with the access token, refresh token, and token type.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    Refresh the access token using a refresh token.

    This endpoint allows a user to get a new access token by providing a valid refresh token. 
    It validates the refresh token and issues new access and refresh tokens.

    :param credentials: The HTTP authorization credentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session dependency.
    :type db: Session
    :return: A dictionary with the new access token, refresh token, and token type.
    :rtype: dict
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm a user's email using a token.

    This endpoint confirms a user's email by decoding the token and updating the user's 
    confirmed status in the database.

    :param token: The token for email confirmation.
    :type token: str
    :param db: The database session dependency.
    :type db: Session
    :return: A dictionary with a confirmation message.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Request an email confirmation.

    This endpoint allows a user to request a new confirmation email if they haven't confirmed 
    their email yet.

    :param body: The request body containing the user's email.
    :type body: RequestEmail
    :param background_tasks: Background tasks for sending the confirmation email.
    :type background_tasks: BackgroundTasks
    :param request: The HTTP request object.
    :type request: Request
    :param db: The database session dependency.
    :type db: Session
    :return: A dictionary with a message indicating that the confirmation email was sent.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    Get the current authenticated user's information.

    This endpoint returns the details of the currently authenticated user.

    :param current_user: The current authenticated user.
    :type current_user: User
    :return: The current user's details.
    :rtype: UserDb
    """
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """
    Update the current user's avatar.

    This endpoint allows the authenticated user to update their avatar by uploading a new image. 
    The image is uploaded to Cloudinary and the user's avatar URL is updated in the database.

    :param file: The new avatar file.
    :type file: UploadFile
    :param current_user: The current authenticated user.
    :type current_user: User
    :param db: The database session dependency.
    :type db: Session
    :return: The updated user's details with the new avatar URL.
    :rtype: UserDb
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'NotesApp/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user
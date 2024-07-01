import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserModel
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
)


class TestUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)

    async def test_get_user_by_email_found(self):
        user = User(email="test@example.com")
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email="test@example.com", db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email="test@example.com", db=self.session)
        self.assertIsNone(result)

    @patch('src.repository.users.Gravatar')
    async def test_create_user(self, mock_gravatar):
        mock_gravatar.return_value.get_image.return_value = "avatar_url"
        body = UserModel(username="testuser", email="test@example.com", password="password")
        self.session.query().filter().first.return_value = None
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.email, body.email)
        self.assertTrue(hasattr(result, "id"))

    async def test_create_user_existing(self):
        body = UserModel(username="testuser", email="test@example.com", password="password")
        self.session.query().filter().first.return_value = User()
        result = await create_user(body=body, db=self.session)
        self.assertIsNone(result)

    async def test_update_token(self):
        user = User()
        await update_token(user=user, token="new_token", db=self.session)
        self.assertEqual(user.refresh_token, "new_token")

    async def test_confirmed_email(self):
        user = User(email="test@example.com", confirmed=False)
        self.session.query().filter().first.return_value = user
        await confirmed_email(email="test@example.com", db=self.session)
        self.assertTrue(user.confirmed)

    async def test_update_avatar(self):
        user = User(email="test@example.com")
        self.session.query().filter().first.return_value = user
        result = await update_avatar(email="test@example.com", url="new_avatar_url", db=self.session)
        self.assertEqual(result.avatar, "new_avatar_url")


if __name__ == '__main__':
    unittest.main()
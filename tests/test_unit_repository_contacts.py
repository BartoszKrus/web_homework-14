import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import date
from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate
from src.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    update_contact,
    remove_contact,
    search_contact,
    get_upcoming_birthdays,
)


class TestContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().offset().limit().all.return_value = contacts
        result = await get_contacts(skip=0, limit=10, user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactCreate(first_name="John", last_name="Doe", email="john@example.com", phone_number="1234567890", birth_date=date(1990, 1, 1))
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_contact_found(self):
        body = ContactUpdate(first_name="Jane", last_name="Doe", email="jane@example.com", phone_number="1234567890", birth_date=date(1990, 1, 1))
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_update_contact_not_found(self):
        body = ContactUpdate(first_name="Jane", last_name="Doe", email="jane@example.com", phone_number="1234567890", birth_date=date(1990, 1, 1))
        self.session.query().filter().first.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_search_contact_by_first_name(self):
        contact = Contact(first_name="John", last_name="Doe", email="john@example.com")
        self.session.query().filter().filter().all.return_value = [contact]
        result = await search_contact(first_name="John", last_name=None, email=None, user=self.user, db=self.session)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].first_name, contact.first_name)

    async def test_search_contact_by_last_name(self):
        contact = Contact(first_name="Jane", last_name="Smith", email="jane@example.com")
        self.session.query().filter().filter().all.return_value = [contact]
        result = await search_contact(first_name="", last_name="Smith", email="", user=self.user, db=self.session)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].last_name, contact.last_name)

    async def test_search_contact_by_email(self):
        contact = Contact(first_name="Alice", last_name="Johnson", email="alice@example.com")
        self.session.query().filter().filter().all.return_value = [contact]
        result = await search_contact(first_name="", last_name="", email="alice@example.com", user=self.user, db=self.session)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].email, contact.email)

    async def test_search_contact_multiple_criteria(self):
        contact = Contact(first_name="Bob", last_name="Brown", email="bob@example.com")
        self.session.query().filter().filter().filter().all.return_value = [contact]
        result = await search_contact(first_name="Bob", last_name="Brown", email="", user=self.user, db=self.session)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].first_name, "Bob")
        self.assertEqual(result[0].last_name, "Brown")

    async def test_search_contact_no_results(self):
        self.session.query().filter().all.return_value = []
        result = await search_contact(first_name="", last_name="", email="", user=self.user, db=self.session)
        self.assertEqual(len(result), 0)

    async def test_search_contact_partial_match(self):
        contacts = [
            Contact(first_name="John", last_name="Doe", email="john@example.com"),
            Contact(first_name="Johnny", last_name="Smith", email="johnny@example.com")
        ]
        self.session.query().filter().filter().all.return_value = contacts
        result = await search_contact(first_name="John", last_name="", email="", user=self.user, db=self.session)
        self.assertEqual(len(result), 2)
        self.assertTrue(all("John" in contact.first_name for contact in result))

    async def test_get_upcoming_birthdays_found(self):
        contacts = [Contact(birth_date=date.today()), Contact(birth_date=date.today())]
        self.session.query().filter().all.return_value = contacts
        result = await get_upcoming_birthdays(user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_upcoming_birthdays_not_found(self):
        self.session.query().filter().all.return_value = []
        result = await get_upcoming_birthdays(user=self.user, db=self.session)
        self.assertEqual(result, [])
    

if __name__ == '__main__':
    unittest.main()
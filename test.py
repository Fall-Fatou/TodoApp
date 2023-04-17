import unittest
import pymongo
from datetime import datetime
from bson import ObjectId
from app import app

class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Setup database for testing
        cls.client = pymongo.MongoClient("mongodb+srv://72046:zTOtdyBLxI544XEt@cluster0.dk1cjbn.mongodb.net/?retryWrites=true&w=majority")
        cls.db = cls.client['test_flask_db']
        cls.todos = cls.db['todos']
        cls.records = cls.db['register']
        cls.app = app.test_client()

    @classmethod
    def tearDownClass(cls):
        # Remove the testing database and all its data
        cls.client.drop_database('test_flask_db')

    def test_index(self):
        # Test the home page
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://localhost/login')

    def test_login_page(self):
        # Test the login page
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        # Test the registration page
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)

    def test_todo_list_page(self):
        # Test the to-do list page
        response = self.app.get('/todolist/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://localhost/login')

    def test_add_todo_item(self):
        # Test adding a new to-do item
        with self.app as c:
            with c.session_transaction() as session:
                session['email'] = 'test@example.com'
            data = {
                'content': 'Test to-do item',
                'due_date': '2023-04-20',
                'degree': 'Important'
            }
            response = self.app.post('/todolist/', data=data, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test to-do item', response.data)

    def test_complete_todo_item(self):
        # Test completing a to-do item
        todo = self.todos.insert_one({'content': 'Test to-do item 2', 'due_date': '2023-04-20', 'degree': 'Important',
                                       'completed': False, 'created_at': datetime.utcnow()})
        todo_id = str(todo.inserted_id)
        with self.app as c:
            with c.session_transaction() as session:
                session['email'] = 'test@example.com'
            response = self.app.post(f'/{todo_id}/complete_todo', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.todos.find_one({'_id': ObjectId(todo_id)})['completed'])

    def test_delete_todo_item(self):
        # Test deleting a to-do item
        todo = self.todos.insert_one({'content': 'Test to-do item 3', 'due_date': '2023-04-20', 'degree': 'Important',
                                       'completed': False, 'created_at': datetime.utcnow()})
        todo_id = str(todo.inserted_id)
        with self.app as c:
            with c.session_transaction() as session:
                session['email'] = 'test@example.com'
            response = self.app.post(f'/{todo_id}/delete', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(self.todos.find_one({'_id': ObjectId(todo_id)}))

if __name__ == '__main__':
    unittest.main()

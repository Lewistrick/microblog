from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Post

class UserModelCase(unittest.TestCase):
	def setUp(self):
		# create own small database
		app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def test_password_hashing(self):
		u = User(name='Tim')
		u.set_pass('T0tt@105')
		self.assertFalse(u.check_pass('Gino@2000'))
		self.assertTrue(u.check_pass('T0tt@105'))

	def test_avatar(self):
		u = User(name='Erick', email='erick@totta.nl')
		self.assertEqual(u.avatar(200), \
			'https://gravatar.com/avatar/ff6e37ae50d2d7f913aeeda39046527d?d=robohash&s=200')

	def test_follow(self):
		u1 = User(name='Tim', email='tim@totta.nl')
		u2 = User(name='Erick', email='erick@totta.nl')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		self.assertEqual(u1.followed.all(), [])
		self.assertEqual(u1.followers.all(), [])

		u1.follow(u2)
		db.session.commit()
		self.assertTrue(u1.follows(u2))
		self.assertEqual(u1.followed.count(), 1)
		self.assertEqual(u1.followed.first().name, 'Erick')
		self.assertEqual(u2.followers.count(), 1)
		self.assertEqual(u2.followers.first().name, 'Tim')

		u1.unfollow(u2)
		db.session.commit()
		self.assertFalse(u1.follows(u2))
		self.assertEqual(u1.followed.count(), 0)
		self.assertEqual(u2.followers.count(), 0)

	def test_follow_posts(self):
		# create four users
		u1 = User(name='Tim', email='tim@totta.nl')
		u2 = User(name='Erick', email='erick@totta.nl')
		u3 = User(name='Francina', email='francina@totta.nl')
		u4 = User(name='Bart', email='bart@totta.nl')
		db.session.add_all([u1, u2, u3, u4])

		# create four posts
		now = datetime.utcnow()
		p1 = Post(content="Bericht van Tim", author=u1,
				  timestamp=now + timedelta(seconds=1))
		p2 = Post(content="Bericht van Erick", author=u2,
				  timestamp=now + timedelta(seconds=4))
		p2b = Post(content="Nog een bericht van Erick", author=u2,
				  timestamp=now + timedelta(seconds=5))
		p3 = Post(content="Bericht van Francina", author=u3,
				  timestamp=now + timedelta(seconds=3))
		p4 = Post(content="Bericht van Bart", author=u4,
				  timestamp=now + timedelta(seconds=2))
		db.session.add_all([p1, p2, p2b, p3, p4])
		db.session.commit()

		# setup the followers
		u1.follow(u2)  # Tim volgt Erick
		u1.follow(u4)  # Tim volgt Bart
		u2.follow(u3)  # Erick volgt Francina
		u3.follow(u4)  # Francina volgt Bart
		db.session.commit()

		# check the followed posts of each user
		f1 = u1.timeline().all()
		f2 = u2.timeline().all()
		f3 = u3.timeline().all()
		f4 = u4.timeline().all()
		self.assertEqual(f1, [p2b, p2, p4, p1])
		self.assertEqual(f2, [p2b, p2, p3])
		self.assertEqual(f3, [p3, p4])
		self.assertEqual(f4, [p4])

if __name__ == '__main__':
	unittest.main(verbosity=2)

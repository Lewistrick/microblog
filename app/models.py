from datetime import datetime
from flask_login import UserMixin
from hashlib import md5
from jwt import encode as jwt_encode, decode as jwt_decode
from jwt.exceptions import InvalidSignatureError
from time import time
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db, login

"""This *Table* class `followers` contains follower-leader (many-to-many) relationships.

A 'Follow' (quotes because it's not a real but an auxiliary table) entry has the following fields:
	int `followed_by`: the ID of the User that follows
	int `follows`: the ID of the User that is followed (i.e. the leader)
"""
followers = db.Table('followers',
	db.Column('followed_by', db.Integer, db.ForeignKey('user.id')),
	db.Column('follows', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
	"""A User class.

	This is a Flask class that keeps track of the login state of the user,
	*as well as* a database table class that connects with the user's data in the database.
	So this is class exploits multiple inheritance.

	A User entry in the database has the following fields:
		int `id`: unique id of the user
		string `name`: username
		string `email`: user's email address
		string `passhash`: an md5-hashed representation of the user's password
		string `about`: a small backstory of the user self
		datetime `lastseen`: the date and time of the user's last activity on the client side

	This entry connects to the following tables and can be called as the following datatypes:
		list `posts`: a list of Post objects
		list `followed`: a list of User objects (self-reference) followed by this user
	"""
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	passhash = db.Column(db.String(128))
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	about = db.Column(db.String(140))
	lastseen = db.Column(db.DateTime, default=datetime.utcnow)
	followed = db.relationship( # see also the creation of the 'followers' table at the top
		'User', # this is the right side entity of the relationship (User self is the left side)
		secondary=followers, # this is the association table
		primaryjoin=(followers.c.follows == id), # link followers.follows to users.id
		secondaryjoin=(followers.c.followed_by == id), # link followers.followed_by to users.id
		backref=db.backref( # how to access rel'ship from right side
			'followers', # the left side was 'followed' so the right side is 'followers'
			lazy='dynamic'), # don't run backref (right side) until specifically requested
		lazy='dynamic') # don't run query (left side) until specifically requested

	def __repr__(self):
		"""Represent this user as a string."""
		return "<User '{}'>".format(self.name)

	def avatar(self, size=200, d="robohash"):
		"""Load the avatar of this user using gravatar."""
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		g = "https://gravatar.com/avatar/{}?d={}&s={}".format(digest, d, size)
		return g

	def check_pass(self, pw):
		"""Check whether an entered password is correct."""
		check = check_password_hash(self.passhash, pw)
		if not check:
			logger.warn("Ongeldig wachtwoord voor {}: {}".format(self.name, pw))
			logger.warn(self.passhash)
			logger.warn(generate_password_hash(pw))
		return check

	@staticmethod
	def check_passreset_token(token):
		try:
			uid = jwt_decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])['reset_pass']
		except InvalidSignatureError:
			return None
		return User.query.get(uid)

	def follow(self, other):
		"""Make this User follow an `other` User."""
		if not self.follows(other):
			self.followed.append(other)

	def follows(self, other):
		"""Check if self is a follower of an `other` User."""
		return self.followed.filter(followers.c.followed_by == other.id).count() > 0

	def get_passreset_token(self, expiration_secs=1800):
		"""Create a token for a user to reset the account password."""
		return jwt_encode({'reset_pass': self.id, 'exp': time() + expiration_secs},
			app.config['SECRET_KEY'], algorithm="HS256").decode('utf-8')

	def last_activity(self):
		"""Read the last activity of this user."""
		if not self.lastseen:
			return 'nooit'

		# this was once made by myself (Erick)
		# return self.lastseen.strftime("%d %B %Y, %H:%M:%S")

		# this is later added by the author of the Flask Tutorial (Michael)
		return moment(self.lastseen).format('LLL')

	def set_pass(self, pw):
		"""Save a hash of the user's password in the database."""
		self.passhash = generate_password_hash(pw)

	def timeline(self):
		"""Get all posts of users that are followed by this User.

		Join has kinda the same functionality as merge in pandas: it unites two tables on a given
		column. In this case, it takes the Post table (the table to execute the query upon,
		because we want to see posts) and joins it with the table in the first argument: followers
		(i.e. the auxiliary table that links users). The second argument of join is a condition:
		the column names to match. On the left side, it's the user_id of the Post; on the right,
		it's the followed_by of the follower.
		This yields a list of all the posts that are followed by any user, so the filter is used
		to get posts that are followed by the current user.
		"""
		flwd = Post.query.join( # Create temporary table joining posts and ...
			followers, # ... followers (seemly skipping the User table at first) ...
			(Post.user_id == followers.c.followed_by) # ... using user_id to connect them ...
		).filter(
			followers.c.follows == self.id # ... but only select posts from followed users.
		)

		# Get all posts from the current user ...
		own = Post.query.filter_by(user_id=self.id)
		# ... and show them among the post of its followers, ordered by newest.
		tl = flwd.union(own).order_by(Post.timestamp.desc())

		return tl

	def unfollow(self, other):
		"""Make this User unfollow an `other` User."""
		if self.follows(other):
			self.followed.remove(other)

class Post(db.Model):
	"""Post class.

	Stores posts (by users) in the database.
	A Post entry has the following fields:
		int `id`: a unique post ID
		string `content`: the body text of the post
		datetime `timestamp`: the time the post was created
		int `user_id`: a reference to the ID of the user that created the post, backreferenced
			from User as `author` so that Post.author returns a User object
	"""
	id = db.Column(db.Integer, primary_key=True)
	content = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		"""Represent this post as a string."""
		return "<Post #{}: {}>".format(self.id, self.content)

	def timefmt(self):
		return self.timestamp.strftime("%d %B %Y, %H:%M:%S")

@login.user_loader # flask login requires to have a user_loader function
def load_user(id):
	"""Load user's data from the database"""
	return User.query.get(int(id))

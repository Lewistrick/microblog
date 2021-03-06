from datetime import datetime
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from app import app, db
from app.email import send_passreset_email
from app.forms import EditProfileForm, LoginForm, PasswordForgottenForm, PostForm, \
	RegistrationForm, ResetPassForm
from app.models import User, Post
from app.textanalytics import word_counts

@app.before_request
def before_request():
	"""On every request a user does, change the 'last seen' time of this user in the database."""
	if current_user.is_authenticated:
		current_user.lastseen = datetime.utcnow()
		db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	"""Preloads page for editing a user's profile"""
	# Let op: dit formulier heeft een argument 'curruser' nodig!
	form = EditProfileForm(curruser=current_user.name)
	if form.validate_on_submit():
		current_user.name = form.un.data
		current_user.about = form.abt.data
		db.session.commit()
		flash('Wijzigingen opgeslagen!')
		return redirect(url_for('edit_profile'))
	elif request.method == 'GET':
		# Het initiele request is 'GET'; vul het formulier met de bestaande data
		form.un.data = current_user.name
		form.abt.data = current_user.about
	return render_template('edit_profile.html', title='Profiel wijzigen', form=form)

@app.route('/explore')
@login_required
def explore():
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'],
		False)

	next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
	prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None

	return render_template('index.html', title='Bladeren', posts=posts.items,
		nextpage=next_url, prevpage=prev_url)

@app.route('/follow/<username>')
@login_required
def follow(username):
	"""Functionality for following users"""
	# Find user by username
	user = User.query.filter_by(name=username).first()

	# Do checks on the user to be followed
	if user is None:
		flash("Gebruiker niet gevonden: {}".format(username))
		return redirect(url_for("index"))
	elif user == current_user:
		flash("Je volgt jezelf al automatisch, gekkie.")
		return redirect(url_for("view_profile", username=username))

	# Follow the user and redirect back
	current_user.follow(user)
	db.session.commit()
	flash("Je volgt nu {}.".format(username))
	return redirect(url_for("view_profile", username=username))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
	"""Preloads page for password resetting"""
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = PasswordForgottenForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.mail.data).first()
		if not user:
			flash('Deze gebruiker bestaat niet.')
		else:
			send_passreset_email(user)
			flash('Er is een mail verstuurd naar {}'.format(form.mail.data) + \
				'met instructies voor het herstellen van je wachtwoord.')
		return redirect(url_for('login'))
	return render_template('forgot_password.html', title='Herstel wachtwoord', form=form)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
	"""Preloads index page (that shows posts from followed users)"""
	form = PostForm()
	if form.validate_on_submit():
		post = Post(content=form.msg.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Bericht succesvol geplaatst!')
		return redirect(url_for('index'))

	page = request.args.get('page', 1, type=int)
	posts = current_user.timeline().paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=posts.next_num) if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
	return render_template('index.html', title='Microblog Home', form=form, posts=posts.items,
		nextpage=next_url, prevpage=prev_url)

@app.route('/login', methods=['GET', 'POST']) # `methods` holds allowed requests; default only GET
def login():
	"""Preloads login page"""
	# if the user is already logged in, redirect to index
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	# load the login form (created in forms.py)
	form = LoginForm()

	# The validate_on_submit() function does all the form processing work
	# It checks whether a GET or POST request is received:
	# - when POST, it evaluates to True and redirects to index;
	# - when GET, it evaluates to False and it skips the if statement.
	if form.validate_on_submit():
		# At this point, all data from the form is gathered and validated
		# The form instance has now attributes with the names of the elements

		# Query the user from the database
		user = User.query.filter_by(name=form.un.data).first()

		# Check if the username exists
		if user is None:
			flash("Gebruikersnaam bestaat niet.")
			return redirect(url_for('login'))
		# Check if the entered password is correct
		if not user.check_pass(form.pw.data):
			flash("Wachtwoord bij gebruiker is onjuist!")
			return redirect(url_for('login'))
		login_user(user, remember=form.remember.data)

		# If the page that redirected to login was given, redirect to that page
		next_page = request.args.get('next')
		# If not given, or when the url doesn't point relatively, then set the next page to index
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')

		return redirect(next_page)

	# Form has not been submitted, render the page
	return render_template('login.html', title='Inloggen', form=form)

@app.route('/logout')
def logout():
	"""Logs user out and redirects to index"""
	logout_user()
	return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Preloads user registration page"""
	# if the user is already logged in, redirect to index
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(name=form.un.data, email=form.mail.data)
		user.set_pass(form.pw.data)
		db.session.add(user)
		db.session.commit()
		flash('De gebruiker is succesvol aangemaakt!')
		return redirect(url_for('login'))
	return render_template('register.html', title='Registreren', form=form)

@app.route('/resetpass/<token>', methods=['GET', 'POST'])
def resetpass(token):
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	user = User.check_passreset_token(token)

	# check if the token is valid
	if not user:
		return redirect(url_for('index'))

	form = ResetPassForm()
	if form.validate_on_submit():
		user.set_pass(form.pw.data)
		db.session.commit()
		flash('Je wachtwoord is hersteld.')
		return redirect(url_for('login'))

	return render_template('resetpass.html', form=form)

@app.route('/textanalysis', methods=['POST'])
@login_required
def textanalysis():
	return jsonify(
		{'text': word_counts(
			request.form['text'] # request.form bevat alle data van de request
		)}
	)

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
	"""Functionality for unfollowing a user."""
	# Read the user from the database and convert to user object
	user = User.query.filter_by(name=username).first()
	if user is None:
		flash("Er bestaat geen gebruiker met deze naam: {}.".format(username))
		return redirect(url_for('index'))
	elif user == current_user:
		flash("Je kunt jezelf niet ontvolgen.")
		return redirect(url_for('view_profile', username=username))
	current_user.unfollow(user)
	db.session.commit()
	flash("Je hebt {} ontvolgd.".format(username))
	return redirect(url_for('view_profile', username=username))

@app.route('/users')
@login_required
def users():
	"""Preloads page that shows all users."""
	users = User.query.all()
	return render_template('users.html', title='Alle gebruikers', users=users)

@app.route('/view_profile/<username>')
@login_required
def view_profile(username):
	"""Preloads user profile page"""
	user = User.query.filter_by(name=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'],
		False)

	next_url = url_for('view_profile', username=user.name, page=posts.next_num) if posts.has_next \
		else None
	prev_url = url_for('view_profile', username=user.name, page=posts.prev_num) if posts.has_prev \
		else None

	return render_template("view_profile.html", title="Gebruiker", user=user, posts=posts.items,
		nextpage=next_url, prevpage=prev_url)

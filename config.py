import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Het opslaan van configuratie in een class is slechts één van de mogelijkheden,
# maar volgens The Flask Mega Tutorial is het wel de beste (separation of concerns).
class Config(object):
	# Lees de secret key uit de environment variables (WAUW dit is SLIM!)
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'onraadbaar-wachtwoord'

	# Initialiseer en configureer de database
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	ADMINS = ['erwipro@gmail.com', 'erick@totta.nl']

	POSTS_PER_PAGE = 25

from flask import render_template
from flask_mail import Message
from threading import Thread

from app import app, mail

def sendmail(subject, from_addr, to_addr, text_body, html_body):
	"""Send an e-mail.

	Arguments:
		str `subject`: The subject of the e-mail
		str `from_addr`: The sender of the e-mail
		var `to_addr`: The recipients of the e-mail (can be a string or a list of strings)
		str `text_body`: The textual version of the e-mail
		str `html_body`: The html version of the e-mail. Both a text and an HTML version are needed
			because of the settings of some e-mail clients.
	"""
	if isinstance(to_addr, str):
		to_addr = [to_addr]

	msg = Message(subject, sender=from_addr, recipients=to_addr)
	msg.body = text_body
	msg.html = html_body

	# send email asynchronously, so that the process runs in the background and the app won't load
	Thread(target=sendmail_async, args=(app, msg)).start()

def sendmail_async(app, msg):
	with app.app_context():
		mail.send(msg)

def send_passreset_email(user):
	token = user.get_passreset_token()
	sendmail('[Microblog] Wachtwoordherstel aangevraagd',
		from_addr = app.config['ADMINS'][0],
		to_addr = user.email,
		text_body = render_template('email/resetpass.txt', user=user, token=token),
		html_body = render_template('email/resetpass.html', user=user, token=token)
	)

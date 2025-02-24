import logging

from app.tasks.emails import send_user_email


def _has_newline(line):
	"""Used by has_bad_header to check for \\r or \\n"""
	if line and ("\r" in line or "\n" in line):
		return True
	return False

def _is_bad_subject(subject):
	"""Copied from: flask_mail.py class Message def has_bad_headers"""
	if _has_newline(subject):
		for linenum, line in enumerate(subject.split("\r\n")):
			if not line:
				return True
			if linenum > 0 and line[0] not in "\t ":
				return True
			if _has_newline(line):
				return True
			if len(line.strip()) == 0:
				return True
	return False


class FlaskMailSubjectFormatter(logging.Formatter):
	def format(self, record):
		record.message = record.getMessage()
		if self.usesTime():
			record.asctime = self.formatTime(record, self.datefmt)
		s = self.formatMessage(record)
		return s

class FlaskMailTextFormatter(logging.Formatter):
	pass

class FlaskMailHTMLFormatter(logging.Formatter):
	def formatException(self, exc_info):
		formatted_exception = logging.Handler.formatException(self, exc_info)
		return "<pre>%s</pre>" % formatted_exception
	def formatStack(self, stack_info):
		return "<pre>%s</pre>" % stack_info


# see: https://github.com/python/cpython/blob/3.6/Lib/logging/__init__.py (class Handler)

class FlaskMailHandler(logging.Handler):
	def __init__(self, send_to, subject_template, level=logging.NOTSET):
		logging.Handler.__init__(self, level)
		self.send_to = send_to
		self.subject_template = subject_template

	def setFormatter(self, text_fmt):
		"""
		Set the formatters for this handler. Provide at least one formatter.
		When no text_fmt is provided, no text-part is created for the email body.
		"""
		assert text_fmt != None, "At least one formatter should be provided"
		if type(text_fmt)==str:
			text_fmt = FlaskMailTextFormatter(text_fmt)
		self.formatter = text_fmt

	def getSubject(self, record):
		fmt = FlaskMailSubjectFormatter(self.subject_template)
		subject = fmt.format(record)
		# Since templates can cause header problems, and we rather have a incomplete email then an error, we fix this
		if _is_bad_subject(subject):
			subject="FlaskMailHandler log-entry from ContentDB [original subject is replaced, because it would result in a bad header]"
		return subject

	def emit(self, record):
		subject = self.getSubject(record)
		text = self.format(record)				if self.formatter	  else None
		html = "<pre>{}</pre>".format(text)

		if "The recipient has exceeded message rate limit. Try again later" in subject:
			return

		for email in self.send_to:
			send_user_email.delay(email, "en", subject, text, html)


def build_handler(app):
	subject_template = "ContentDB %(message)s (%(module)s > %(funcName)s)"
	text_template = ("Message type: %(levelname)s\n"
		"Location: %(pathname)s:%(lineno)d\n"
		"Module:   %(module)s\n"
		"Function: %(funcName)s\n"
		"Time:     %(asctime)s\n"
		"Message: %(message)s\n\n")

	mail_handler = FlaskMailHandler(app.config["MAIL_UTILS_ERROR_SEND_TO"], subject_template)
	mail_handler.setLevel(logging.ERROR)
	mail_handler.setFormatter(text_template)
	return mail_handler

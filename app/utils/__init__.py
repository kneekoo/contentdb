# ContentDB
# Copyright (C) 2018-21 rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import secrets

from .flask import *
from .models import *
from .user import *
from flask import current_app

YESES = ["yes", "true", "1", "on"]


def is_username_valid(username):
	return username is not None and len(username) >= 2 and \
			re.match(r"^[A-Za-z0-9._-]*$", username) and not re.match(r"^\.*$", username)


def isYes(val):
	return val and val.lower() in YESES


def isNo(val):
	return val and not isYes(val)


def nonEmptyOrNone(str):
	if str is None or str == "":
		return None

	return str


def shouldReturnJson():
	return "application/json" in request.accept_mimetypes and \
			not "text/html" in request.accept_mimetypes


def randomString(n):
	return secrets.token_hex(int(n / 2))


def has_blocked_domains(text: str, username: str, location: str) -> bool:
	if text is None:
		return False

	blocked_domains = current_app.config["BLOCKED_DOMAINS"]
	for domain in blocked_domains:
		if domain in text:
			from app.tasks.webhooktasks import post_discord_webhook
			post_discord_webhook.delay(username,
					f"Attempted to post blocked domain {domain} in {location}",
					True)
			return True

	return False

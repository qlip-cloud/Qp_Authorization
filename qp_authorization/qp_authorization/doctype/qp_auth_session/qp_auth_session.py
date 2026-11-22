# Copyright (c) 2023, Rafael Licett and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import getdate
from frappe.utils import get_datetime, now_datetime

PASSWORD_FIELDS = ("access_token", "refresh_token", "code")


class qp_auth_session(Document):

	def on_trash(self):

		from frappe.utils.password import remove_encrypted_password

		for fieldname in PASSWORD_FIELDS:

			remove_encrypted_password(self.doctype, self.name, fieldname)

		if self.enviroment:

			from qp_authorization.use_case.bearer.authorize import clear_session_cache

			clear_session_cache(self.enviroment)
	
	def is_valid(self):
     
		if not self.expire_date:
      
			return False
		
		self.expire_date = get_datetime(self.expire_date)

		return self.expire_date >= now_datetime()

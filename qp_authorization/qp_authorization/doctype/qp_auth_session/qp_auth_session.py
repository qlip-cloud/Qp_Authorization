# Copyright (c) 2023, Rafael Licett and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import getdate

class qp_auth_session(Document):
	
	def is_valid(self):
		
		format_string = "%Y-%m-%d %H:%M:%S"

		if not isinstance(self.expire_date, datetime):
		
			self.expire_date = datetime.strptime(self.expire_date, format_string)

		return self.expire_date >= datetime.now()

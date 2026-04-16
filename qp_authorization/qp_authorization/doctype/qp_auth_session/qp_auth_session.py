# Copyright (c) 2023, Rafael Licett and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import getdate
from frappe.utils import get_datetime, now_datetime

class qp_auth_session(Document):
	
	def is_valid(self):
     
		if not self.expire_date:
      
			return False
		
		self.expire_date = get_datetime(self.expire_date)

		return self.expire_date >= now_datetime()

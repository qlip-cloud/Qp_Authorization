# Copyright (c) 2024, Rafael Licett and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from qp_authorization.use_case.bearer.authorize import search_token

class qp_auth_Enviroment(Document):
	
	def validate(self):

		search_token(self)

	def get_url(self, url, id = None):

		url_base = self.url + url

		if id:
			
			return url_base + '/' + str(id)
		
		return url_base

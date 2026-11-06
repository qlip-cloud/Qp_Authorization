# Copyright (c) 2024, Rafael Licett and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from qp_authorization.use_case.bearer.authorize import search_token

class qp_auth_Enviroment(Document):

	def _clear_client_credentials_cache(self):

		import frappe

		try:

			frappe.cache().delete_keys(
				"qp_authorization:client_credentials:{0}:*".format(self.name)
			)

		except Exception:

			pass

	def on_update(self):

		self._clear_client_credentials_cache()

	def on_trash(self):

		from frappe.utils.password import remove_encrypted_password

		remove_encrypted_password(self.doctype, self.name, "password")

		self._clear_client_credentials_cache()
	
	def validate(self):
		pass
		#search_token(self)

	def get_url(self, url, id = None):

		url_base = self.url + url

		if id:
			
			return url_base + '/' + str(id)
		
		return url_base

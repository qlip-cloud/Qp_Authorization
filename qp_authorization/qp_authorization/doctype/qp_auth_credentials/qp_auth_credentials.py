# Copyright (c) 2023, Rafael Licett and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class qp_auth_credentials(Document):

	def _clear_client_credentials_cache(self):

		import frappe

		try:

			frappe.cache().delete_keys(
				"qp_authorization:client_credentials:*:{0}".format(self.name)
			)

		except Exception:

			pass

	def on_update(self):

		self._clear_client_credentials_cache()

	def on_trash(self):

		from frappe.utils.password import remove_encrypted_password

		for fieldname in ("client_secret", "password"):

			remove_encrypted_password(self.doctype, self.name, fieldname)

		self._clear_client_credentials_cache()

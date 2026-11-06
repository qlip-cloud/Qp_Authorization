# Copyright (c) 2023, Rafael Licett and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class qp_auth_credentials(Document):

	def on_trash(self):

		from frappe.utils.password import remove_encrypted_password

		for fieldname in ("client_secret", "password"):

			remove_encrypted_password(self.doctype, self.name, fieldname)

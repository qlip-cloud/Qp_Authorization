import json
import os
import unittest


APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCTYPE_ROOT = os.path.join(APP_ROOT, "qp_authorization", "doctype")

DIRECTORIES = {
    "qp_auth_credentials": "qp_auth_credentials",
    "qp_auth_Enviroment": "qp_auth_enviroment",
    "qp_auth_session": "qp_auth_session",
}


def load_fields(doctype):
    directory = DIRECTORIES[doctype]
    path = os.path.join(DOCTYPE_ROOT, directory, "{0}.json".format(directory))

    with open(path) as handle:
        definition = json.load(handle)

    return {
        field.get("fieldname"): field for field in definition.get("fields", [])
    }


class TestSensitiveFields(unittest.TestCase):

    def assert_password_field(self, doctype, fieldname):
        fields = load_fields(doctype)

        self.assertIn(fieldname, fields)
        self.assertEqual(
            fields[fieldname].get("fieldtype"),
            "Password",
            "{0}.{1} must use Password".format(doctype, fieldname),
        )

    def test_credentials_client_secret_is_password(self):
        self.assert_password_field("qp_auth_credentials", "client_secret")

    def test_environment_password_is_password(self):
        self.assert_password_field("qp_auth_Enviroment", "password")

    def test_session_tokens_are_password(self):
        self.assert_password_field("qp_auth_session", "access_token")
        self.assert_password_field("qp_auth_session", "refresh_token")
        self.assert_password_field("qp_auth_session", "code")


if __name__ == "__main__":
    unittest.main()

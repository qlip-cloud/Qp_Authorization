import unittest

from qp_authorization.service.secrets import get_secret


class DocWithPassword(object):

    def __init__(self, value):
        self.value = value

    def get_password(self, fieldname, raise_exception=True):
        return self.value


class DocWithLegacySignature(object):

    def __init__(self, value):
        self.value = value

    def get_password(self, fieldname):
        return self.value


class PlainDoc(object):

    def __init__(self, value):
        self.value = value

    def get(self, fieldname):
        return self.value


class TestSecrets(unittest.TestCase):

    def test_uses_get_password_for_frappe_documents(self):
        self.assertEqual(
            get_secret(DocWithPassword("decrypted"), "client_secret"),
            "decrypted",
        )

    def test_supports_legacy_get_password_signature(self):
        self.assertEqual(
            get_secret(DocWithLegacySignature("decrypted"), "password"),
            "decrypted",
        )

    def test_falls_back_to_get_for_plain_objects(self):
        self.assertEqual(
            get_secret(PlainDoc("raw"), "client_secret"),
            "raw",
        )

    def test_returns_default_when_value_is_empty(self):
        self.assertEqual(
            get_secret(DocWithPassword(""), "client_secret", "fallback"),
            "fallback",
        )

    def test_returns_default_for_none(self):
        self.assertEqual(get_secret(None, "password", "fallback"), "fallback")


if __name__ == "__main__":
    unittest.main()

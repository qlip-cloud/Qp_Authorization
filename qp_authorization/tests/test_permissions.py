import json
import os
import unittest


APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCTYPE_ROOT = os.path.join(APP_ROOT, "qp_authorization", "doctype")

DIRECTORIES = {
    "qp_auth_credentials": "qp_auth_credentials",
    "qp_auth_Enviroment": "qp_auth_enviroment",
    "qp_auth_Endpoint": "qp_auth_endpoint",
    "qp_auth_Setup": "qp_auth_setup",
    "qp_auth_session": "qp_auth_session",
}


def load_permissions(doctype):
    directory = DIRECTORIES[doctype]
    path = os.path.join(DOCTYPE_ROOT, directory, "{0}.json".format(directory))

    with open(path) as handle:
        definition = json.load(handle)

    return definition.get("permissions", [])


class TestPermissions(unittest.TestCase):

    def test_no_all_role_on_auth_doctypes(self):
        for doctype in DIRECTORIES:
            roles = [
                permission.get("role")
                for permission in load_permissions(doctype)
            ]

            self.assertNotIn(
                "All",
                roles,
                "{0} must not grant permissions to All".format(doctype),
            )

    def test_system_manager_keeps_access(self):
        for doctype in DIRECTORIES:
            roles = [
                permission.get("role")
                for permission in load_permissions(doctype)
            ]

            self.assertIn(
                "System Manager",
                roles,
                "{0} must keep System Manager access".format(doctype),
            )


if __name__ == "__main__":
    unittest.main()

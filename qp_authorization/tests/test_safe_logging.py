import json
import unittest

from qp_authorization.use_case.rest.safe_logging import (
    build_request_log,
    describe_http_error,
    redact,
    sanitize_url,
    summarize_payload,
    summarize_response,
)


class FakeResponse(object):

    def __init__(self, status_code=200, reason="OK", text=""):
        self.status_code = status_code
        self.reason = reason
        self.text = text


class TestSafeLogging(unittest.TestCase):

    def test_redact_removes_sensitive_values(self):
        payload = {
            "Authorization": "Bearer VALUE-TOKEN",
            "username": "supplier",
            "password": "VALUE-PASSWORD",
            "client_secret": "VALUE-SECRET",
            "access_token": "VALUE-ACCESS",
            "refresh_token": "VALUE-REFRESH",
            "nested": {"api_key": "VALUE-API-KEY", "safe": "visible"},
        }

        result = redact(payload)

        serialized = json.dumps(result)

        self.assertNotIn("VALUE-TOKEN", serialized)
        self.assertNotIn("VALUE-PASSWORD", serialized)
        self.assertNotIn("VALUE-SECRET", serialized)
        self.assertNotIn("VALUE-ACCESS", serialized)
        self.assertNotIn("VALUE-REFRESH", serialized)
        self.assertNotIn("VALUE-API-KEY", serialized)
        self.assertEqual(result["username"], "supplier")
        self.assertEqual(result["nested"]["safe"], "visible")

    def test_sanitize_url_removes_query_userinfo_and_fragment(self):
        url = "https://user:pass@api.example.com:8443/v1/token?code=VALUE-CODE#frag"

        self.assertEqual(
            sanitize_url(url),
            "https://api.example.com:8443/v1/token",
        )

    def test_sanitize_url_handles_invalid_port(self):
        self.assertEqual(
            sanitize_url("http://api.example.com:not-a-port/v1"),
            "http://api.example.com/v1",
        )

    def test_sanitize_url_rejects_missing_scheme(self):
        self.assertEqual(sanitize_url("user:secret@host/path"), "<invalid-url>")

    def test_summarize_payload_never_includes_values(self):
        summary = summarize_payload(
            {"password": "VALUE-PASSWORD", "client_id": "public-id"}
        )

        serialized = json.dumps(summary)

        self.assertIn("password", serialized)
        self.assertNotIn("VALUE-PASSWORD", serialized)

    def test_summarize_response_keeps_only_metadata(self):
        response = FakeResponse(
            status_code=400,
            reason="Bad Request",
            text='{"access_token": "VALUE-ACCESS", "error": "invalid_grant"}',
        )

        summary = summarize_response(response)

        serialized = json.dumps(summary)

        self.assertNotIn("VALUE-ACCESS", serialized)
        self.assertEqual(summary["status"], 400)
        self.assertIn("access_token", summary["json_keys"])

    def test_build_request_log_does_not_leak_values(self):
        response = FakeResponse(
            status_code=401,
            reason="Unauthorized",
            text='{"access_token": "VALUE-ACCESS"}',
        )

        message = build_request_log(
            method="POST",
            url="https://user:pass@api.example.com/v1/token?code=VALUE-CODE",
            payload={"password": "VALUE-PASSWORD"},
            headers={
                "Authorization": "Basic VALUE-BASIC",
                "Content-Type": "application/json",
            },
            response=response,
        )

        self.assertNotIn("VALUE-ACCESS", message)
        self.assertNotIn("VALUE-PASSWORD", message)
        self.assertNotIn("VALUE-BASIC", message)
        self.assertNotIn("VALUE-CODE", message)
        self.assertIn("https://api.example.com/v1/token", message)
        self.assertIn("status", message)

    def test_describe_http_error_omits_tokens(self):
        response = FakeResponse(
            status_code=400,
            text=json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "bad code",
                    "access_token": "VALUE-ACCESS",
                }
            ),
        )

        description = describe_http_error(response)

        self.assertIn("invalid_grant", description)
        self.assertNotIn("VALUE-ACCESS", description)
        self.assertNotIn("bad code", description)


if __name__ == "__main__":
    unittest.main()

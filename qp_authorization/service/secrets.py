"""Accessors for sensitive DocType fields.

Frappe stores ``Password`` fields in the ``__Auth`` table and replaces the
column value with a dummy mask (``*****``). Callers must use
``Document.get_password`` to read the real value. This module keeps that
contract in one place and degrades gracefully for plain objects used in tests.
"""


def get_secret(owner, fieldname, default=""):
    """Return a decrypted secret for a Frappe document or a raw mapping."""

    if owner is None:
        return default

    get_password = getattr(owner, "get_password", None)

    if callable(get_password):
        try:
            value = get_password(fieldname, raise_exception=False)
        except TypeError:
            value = get_password(fieldname)

        return value if value else default

    getter = getattr(owner, "get", None)

    if callable(getter):
        value = getter(fieldname)

        return value if value else default

    value = getattr(owner, fieldname, None)

    return value if value else default

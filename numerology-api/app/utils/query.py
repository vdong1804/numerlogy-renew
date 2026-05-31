"""Query utilities — helpers for safe SQLAlchemy query building."""


def escape_like(value: str) -> str:
    """Escape LIKE/ILIKE wildcards in user-supplied input.

    Replaces backslash, percent, and underscore so they are treated as
    literals when wrapped in %…% for a partial-match search.

    Usage:
        User.email.ilike(f"%{escape_like(email)}%", escape="\\\\")

    SQLAlchemy passes the escape character to the underlying DB driver,
    which honours '\\\\' as the escape sequence in LIKE patterns.
    """
    value = value.replace("\\", "\\\\")
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    return value


__all__ = ["escape_like"]

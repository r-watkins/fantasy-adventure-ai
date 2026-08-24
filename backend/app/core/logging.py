import logging

# aiosqlite (and SQLAlchemy's own engine/pool loggers, dormant today since
# nothing sets echo=True) log full SQL statements with bound parameters at
# DEBUG level - including story_messages.content (player prompts and
# narrator output verbatim), users.email, and the argon2/session-token
# hashes used in WHERE clauses. Pin these below DEBUG regardless of
# whatever the root/app logger level is configured to (e.g. a developer
# debugging locally, or a verbose LOG_LEVEL in production), so raising
# general verbosity can never accidentally spill row content into logs.
_SENSITIVE_THIRD_PARTY_LOGGERS = (
    "aiosqlite",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
)


def silence_sensitive_third_party_loggers() -> None:
    for name in _SENSITIVE_THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

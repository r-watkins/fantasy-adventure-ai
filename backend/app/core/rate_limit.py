from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory backend (slowapi's default `limits` storage) - fine for a
# single-process deployment (this stack's SQLite-backed API can only ever
# run as one write-capable process anyway, see design.md's WAL/SQLite
# constraint). Per-IP key, since auth endpoints run before any session
# exists to key on.
limiter = Limiter(key_func=get_remote_address)

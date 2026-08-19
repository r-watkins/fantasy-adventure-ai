from argon2 import PasswordHasher

from app.core.security import hash_password, needs_rehash, verify_password


def test_hash_password_produces_argon2id_hash() -> None:
    hashed = hash_password("correct horse battery staple")

    assert hashed.startswith("$argon2id$")


def test_hash_password_uses_unique_salt_per_call() -> None:
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")

    assert first != second


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_incorrect_password() -> None:
    hashed = hash_password("correct horse battery staple")

    assert verify_password("wrong password", hashed) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert verify_password("anything", "not-a-real-hash") is False


def test_needs_rehash_false_for_current_params() -> None:
    hashed = hash_password("correct horse battery staple")

    assert needs_rehash(hashed) is False


def test_needs_rehash_true_for_weaker_params() -> None:
    weak_hasher = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    weak_hash = weak_hasher.hash("correct horse battery staple")

    assert needs_rehash(weak_hash) is True

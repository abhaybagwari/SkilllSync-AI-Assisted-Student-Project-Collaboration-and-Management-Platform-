from backend.utils.jwt_handler import create_access_token, verify_access_token


def test_create_access_token():
    token = create_access_token(1, "Team Member")
    assert isinstance(token, str)


def test_verify_access_token():
    token = create_access_token(1, "Team Member")
    payload = verify_access_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "Team Member"


def test_invalid_token():
    payload = verify_access_token("invalid-token")
    assert payload is None
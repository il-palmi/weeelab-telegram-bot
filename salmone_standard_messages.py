import json

TLS_HANDSHAKE = {
    "command": "TLS_START"
}

TLS_READY = {
    "command": "TLS_READY"
}


def authorization_command(user: str) -> str:
    AUTHORIZATION = {
        "command": "GET_AUTHORIZATION",
        "user": user
    }
    return json.dumps(AUTHORIZATION)

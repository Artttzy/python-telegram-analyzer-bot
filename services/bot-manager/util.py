import hashlib


def get_container_name(token):
    return hashlib.md5(
        string=token.encode(encoding='utf-8'),
        usedforsecurity=False).hexdigest()

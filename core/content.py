import hashlib
from typing import Optional


class Content:

    def __init__(self, data: bytes) -> None:
        self.data: bytes = data
        self.hash: Optional[bytes] = None

    def get_hash(self) -> bytes:
        if self.hash:
            return self.hash

        s = hashlib.md5()
        s.update(self.data)
        self.hash = s.digest()
        return self.hash

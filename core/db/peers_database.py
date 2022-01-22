from typing import List


class PeersDatabase:

    def __init__(self):
        self.peers = set()

    def add_peer(self, peer_id):
        self.peers.add(peer_id)

    def get_peers(self) -> List[int]:
        return list(self.peers)

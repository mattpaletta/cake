import hashlib
import logging
import uuid


def find_peers(hostname, port, id):
    peers_hostnames = []
    num_skipped = 0

    current_peer = 0
    while num_skipped < 3:
        current_peer_hostname = "{0}-{1}:{2}".format(hostname,
                                                     current_peer,
                                                     port)

        # if peer.connect(id) == 1 (with GRPC futures)
        if True:
            peers_hostnames.append(current_peer_hostname)
        else:
            num_skipped += 1
        current_peer += 1

    return peers_hostnames


class Cake(object):
    def __init__(self, port: int, num_peers: int, hostname: str):
        self._port = port
        hash_val = hashlib.sha256(str(uuid.uuid1()).encode("utf")).hexdigest()
        self._id = int(hash_val, 16)
        self._current_nonce = 0

        logging.info("Starting system with ID: " + str(self._id))
        self._peers = find_peers(hostname, port, self._id)

    def connect(self, id):
        # If they're the same, we've found ourself!
        if id == self._id:
            return 1
        else:
            return -1

    def set(self, key: str, value: int):
        # current_nonce = self._current_nonce
        # TODO:// Assume it's always the next node.
        key_node_id = self._get_key_hash(key) % self._num_peers

    def get(self, key: str):
        pass

    def remove(self, key: str):
        pass

    def exists(self, key: str):
        pass

    @property
    def _num_peers(self):
        return len(self._peers)

    def _get_key_hash(self, key: str):
        hash_val = hashlib.sha256(key.encode("utf")).hexdigest()
        as_int = int(hash_val, 16)
        return as_int

    def _get_peer(self, id: int):
        if id > self._num_peers:
            return None
        else:
            return self._peers[id]

    def _get_from_peer(self, peer: str, key: str):
        # connect to peer, get the value.
        # LRU of connections
        pass
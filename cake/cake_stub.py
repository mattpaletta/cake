import hashlib
import logging
import uuid
import grpc
from cake.proto.cake_pb2_grpc import CakePeerServicer, CakePeerStub
from cake.proto.cake_pb2 import Node, Obj, PubObj


def find_peers(hostname, port, id):
    peers_hostnames = []
    num_skipped = 0
    my_id = Node(id = id)

    current_peer = 0
    while num_skipped < 3:
        current_peer_hostname = "{0}-{1}:{2}".format(hostname,
                                                     current_peer,
                                                     port)

        channel = grpc.insecure_channel("{0}:2018".format(current_peer_hostname))
        connection = CakePeerStub(channel = channel)
        try:
            grpc.channel_ready_future(channel).result(5)
        except grpc.FutureTimeoutError:
            # Did not hear back from node.
            num_skipped += 1
            continue

        if connection.connect_internal(my_id).resp != id:
            # If they are not the same, it's not us!
            peers_hostnames.append(current_peer_hostname)
        else:
            num_skipped += 1
        current_peer += 1

    return peers_hostnames


class Cake(CakePeerServicer):
    def __init__(self, port: int, num_peers: int, hostname: str):
        self._port = port
        hash_val = hashlib.sha256(str(uuid.uuid1()).encode("utf")).hexdigest()
        self._id = int(str(int(hash_val, 16))[:10])
        self._current_nonce = 0

        logging.info("Starting system with ID: " + str(self._id))

        logging.info("Finding peers.")
        self._peers = find_peers(hostname, port, self._id)
        logging.info("Found: {0} peers")
        
    def get(self, request, context):
        pass

    def get_internal(self, request, context):
        pass

    def connect_internal(self, request: Node, context: any) -> Node:
        return Node(id = request.id, resp = self._id)

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
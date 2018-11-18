import hashlib
import logging
import uuid
from typing import Union, Tuple, Dict, List
import grpc

from cake.proto.cake_pb2_grpc import CakePeerServicer, CakePeerStub
from cake.proto.cake_pb2 import Node, Obj, PubObj


def find_peers(hostname, port, id):
    peers_hostnames = []
    num_skipped = 0
    my_id = Node(id = id)

    current_peer = 1
    while num_skipped < 3:
        current_peer_hostname = "{0}_{1}:{2}".format(hostname,
                                                     current_peer,
                                                     port)

        logging.debug("Trying peer:" + current_peer_hostname)

        channel = grpc.insecure_channel("{0}".format(current_peer_hostname))
        connection = CakePeerStub(channel = channel)

        current_peer += 1
        try:
            grpc.channel_ready_future(channel).result(5)
        except grpc.FutureTimeoutError:
            # Did not hear back from node.
            num_skipped += 1
            continue

        other_node_reply: Node = connection.connect_internal(my_id)
        if other_node_reply.resp != id:
            # If they are not the same, it's not us!
            peers_hostnames.append(current_peer_hostname)
        else:
            num_skipped += 1

    return peers_hostnames


class Cake(CakePeerServicer):
    def __init__(self, port: int, num_peers: int, hostname: str):
        self._hostname = hostname

        self._port = port
        hash_val = hashlib.sha256(str(uuid.uuid1()).encode("utf")).hexdigest()
        self._id = int(str(int(hash_val, 16))[:10])
        self._current_nonce = 0

        logging.info("Starting system with ID: " + str(self._id))
        self._peers: List[str] = []

        # TODO:// Update this so it's not all just in memory.
        self._data: Dict[str, Union[str, int, float, bool]] = {}

    def bootstrap(self):
        logging.info("Finding peers.")
        self._peers = find_peers(self._hostname, self._port, self._id)
        logging.info("Found: {0} peers".format(len(self._peers)))

    # Public methods
    def get(self, request: PubObj, context) -> PubObj:
        return self._handle_internal_extern(request = request,
                                            fun = "get",
                                            context = context)

    def set(self, request: PubObj, context) -> PubObj:
        return self._handle_internal_extern(request = request,
                                            fun = "set",
                                            context = context)

    def set_internal(self, request: Obj, context) -> Obj:
        return self._handle_internal(request, "set")

    def get_internal(self, request: Obj, context) -> Obj:
        return self._handle_internal(request, "get")

    def _handle_internal(self, request: Obj, fun) -> Obj:
        key = request.pubkey

        if fun == "get":
            logging.debug("Getting value:" + str(key))
            if key in self._data.keys():
                logging.debug("Got key: " + str(key))
                value = self._data.get(key)
            else:
                value = False
                logging.warning("Invalid Key!")

        elif fun == "set":
            logging.debug("Setting key: " + str(key))
            _, value = self._get_value(request)
            if value is not None:
                logging.debug("Updating key: " + str(key))
                self._data.update({key: value})
        else:
            logging.error("Invalid function.")
            return request

        if value is not None:
            return_data = self._set_value(value)
            return Obj(pubkey = key, key = request.key, **return_data)
        else:
            return request

    def connect_internal(self, request: Node, context) -> Node:
        if request.id not in self._peers:
            # If we don't have this node added, let's add it!
            # TODO:// This should be a hostname
            # self._peers.append(str(request.id))
            logging.warning("Found a new node!")

        # Return with our hello!
        return Node(id = request.id, resp = self._id)

    def _handle_internal_extern(self, request: PubObj, fun: str, context) -> PubObj:
        internal_obj = self._pub_to_obj(request)

        peer = self._find_peer(request.key)
        logging.debug("Using method: " + fun)

        resp: Obj = None
        if fun == "set":
            resp = peer.set_internal(request = internal_obj,
                                          context = context)
        elif fun == "get":
            resp = peer.get_internal(request = internal_obj,
                                          context = context)
        else:
            logging.error("Invalid function!")
            return request

        assert type(resp) is Obj, "Invalid return type."
        return self._obj_to_pub(resp)

    def _obj_to_pub(self, obj: Obj) -> PubObj:
        option_key, option_val = self._get_value(obj)
        return PubObj(key = obj.pubkey, **{option_key: option_val})

    def _pub_to_obj(self, pub: PubObj) -> Obj:
        # current_nonce = self._current_nonce
        # TODO:// Assume it's always the next node.

        key_node_id = self._get_key_hash(pub.key) % self._num_peers

        option_key, option_val = self._get_value(pub)
        return Obj(key = key_node_id,
                   pubkey = pub.key,
                   **{option_key: option_val})

    def _set_value(self, value: Union[str, int, float, bool]) -> Dict[str, Union[None, str, int, float, bool]]:
        ty = type(value)
        return {str(ty): value}

    def _get_value(self, obj: Union[PubObj, Obj]) -> Tuple[str, Union[str, int, float, bool, None]]:
        which = str(obj.WhichOneof("value"))

        if which == "str":
            parsed_val = obj.str
        elif which == "bigint":
            parsed_val = obj.bigint
        elif which == "int":
            parsed_val = obj.int
        elif which == "dbl":
            parsed_val = obj.dbl
        elif which == "flt":
            parsed_val = obj.flt
        elif which == "bool":
            parsed_val = obj.bool
        else:
            parsed_val = None
            raise NotImplementedError("Can't parse value type: " + which)
        return which, parsed_val

    def _find_peer(self, key):
        # TODO:// Update to store LRU of connections for peers.
        # If we don't know of anybody else (like local mode, ask ourselves)
        if len(self._peers) > 0:
            return self._peers[0]
        else:
            return self

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
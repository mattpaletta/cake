import hashlib
import logging
import uuid
from typing import Union, Tuple, Callable, Dict

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

        channel = grpc.insecure_channel("{0}".format(current_peer_hostname))
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

        # TODO:// Update this so it's not all just in memory.
        self._data = {}

    # Public methods
    def get(self, request: PubObj, context: any) -> PubObj:
        return self._handle_internal_extern(request = request,
                                            fun = "get",
                                            context = context)

    def set(self, request: PubObj, context: any) -> PubObj:
        return self._handle_internal_extern(request = request,
                                            fun = "set",
                                            context = context)

    def set_internal(self, request: Obj, context: any) -> Obj:
        return self._handle_internal(request, "set")

    def get_internal(self, request: Obj, context: any) -> Obj:
        return self._handle_internal(request, "get")

    def _handle_internal(self, request: Obj, fun: str) -> Obj:
        key = request.pubkey

        if fun == "get":
            if key in self._data.keys():
                value = self._data.get(key)
            else:
                value = False
                logging.warning("Invalid Key!")

        elif fun == "set":
            value = self._get_value(request)
            self._data.update({key: value})

        else:
            logging.error("Invalid fucntion.")
            return request

        return_data = self._set_value(value)
        return Obj(pubkey = key, key = request.key, **return_data)

    def connect_internal(self, request: Node, context: any) -> Node:
        if request.id not in map(lambda peer: peer.id, self._peers):
            # If we don't have this node added, let's add it!
            # TODO:// This should be a hostname
            # self._peers.append(str(request.id))
            logging.warning("Found a new node!")

        # Return with our hello!
        return Node(id = request.id, resp = self._id)

    def _handle_internal_extern(self, request: PubObj, fun: str, context: any) -> PubObj:
        internal_obj = self._pub_to_obj(request)

        peer = self._find_peer(request.key)
        options = {
            "set": peer.set_internal,
            "get": peer.get_internal
        }
        if fun not in options.keys():
            logging.error("Invalid function!")
            return request

        fun_to_call = options.get(fun)

        resp: Obj = fun_to_call(request = internal_obj,
                                context = context)

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

    def _set_value(self, value: Union[str, int, float, bool]) -> Dict[str, Union[str, int, float, bool]]:
        ty = type(value)
        return {str(ty): value}

    def _get_value(self, obj: Union[PubObj, Obj]) -> Tuple[str, Union[str, int, float, bool]]:
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
            raise NotImplementedError("Can't parse value type: " + which)
        return which, parsed_val

    def _find_peer(self, key):
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
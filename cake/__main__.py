import logging
import os
import sys
from concurrent import futures

import grpc
from configs.parser import Parser

from cake import ONE_DAY_IN_SECONDS
from cake.cake_stub import Cake
from cake.proto import cake_pb2_grpc


def main():
    root = logging.getLogger()
    root.setLevel(logging.NOTSET)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)s]')
    ch.setFormatter(formatter)
    root.addHandler(ch)

    this_dir, _ = os.path.split(__file__)
    DATA_PATH = os.path.join(this_dir, "resources", "argparse.yml")
    LOCAL_DATA_PATH = os.path.join("./resources", "argparse.yml")

    if os.path.exists(DATA_PATH):
        logging.debug("Found installed configs")
        final_data_path = DATA_PATH
    elif os.path.exists(LOCAL_DATA_PATH):
        logging.debug("Found local configs")
        final_data_path = LOCAL_DATA_PATH
    else:
        raise ImportError("Could not find argparse file.")

    configs = Parser(argparse_file = final_data_path).get()

    hostname = os.environ["HOSTNAME_BOOTSTRAP"] if os.path.exists("/.dockerenv") else "localhost"

    c = Cake(port = configs["port"],
             hostname = hostname,
             num_peers = 1)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers = 2))
    cake_pb2_grpc.add_CakePeerServicer_to_server(servicer = c,
                                                 server = server)
    server.add_insecure_port('[::]:{0}'.format(configs["port"]))

    server.start()

    # Start listening first, then find peers.
    c.bootstrap()
    try:
        import time
        while True:
            time.sleep(ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    main()

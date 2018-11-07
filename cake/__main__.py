import logging
import os
import sys
from time import sleep

from configs.parser import Parser

from cake.cake_stub import Cake


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

    hostname = os.environ["HOSTNAME_BOOTSTRAP"]

    c = Cake(port = configs["port"], hostname = hostname, num_peers = 1)
    print(c.set("hello", 1))
    sleep(560)


if __name__ == "__main__":
    main()

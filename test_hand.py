import time
import os
import sys

sys.path.append("/home/sy/wk/roh_with_rm65/RM-API2")
# sys.path.append("/home/sy/wk/projects/agv_server")
from projects.agv_server.sdk.hand import DexterousHand # type: ignore


if __name__ == "__main__":
    hand = DexterousHand("192.168.10.19")
    hand.open_all()
    hand.close_all()
    hand.close_finger(0, 50)
    # hand.test_sequence(loops=3)
    # hand.test_seq()

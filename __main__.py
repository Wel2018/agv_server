import time
from agv_server.app import main


def idle():
    while 1:
        print(f"{time.time()} -----x-----")
        time.sleep(60)


if __name__ == '__main__':
    # idle()
    main()

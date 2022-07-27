import socket
import time

def isNetworkDown(host='monitora-pa.it'):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((host,443))
    except Exception as error:
        print(error)
        return True
    else:
        s.close()
        return False

def waitUntilNetworkIsBack(host='monitora-pa.it'):
    period = 0
    count = 0
    print('waitUntilNetworkIsBack', end='')
    while isNetworkDown(host):
        print('waitUntilNetworkIsBack', end='')
        if count % 80 == 0:
            period += 15
        time.sleep(period)
        count += 1
    print()


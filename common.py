version = 7
import sys
import time
from serial import Serial
from serial import SerialException
from serial.tools import list_ports

MTK_PreLoader_VIDPID   = "0E8D:2000"
#MTK_PreLoader_VIDPID   = "0E8D:201d"
MTK_Meta_Mode_VIDPID   = "0E8D:2007"
MTK_Meta_Mode_VIDPID1  = "0E8D:2006"

def hexs(s):
    return hexlify(s).decode("ascii")

def Connect_Preloader(serial_port):
    resp = serial_port.read(5)
    assert resp == b"READY"
    print("Preloader get READY")

def Reboot_to_MetaMode(serial_port):
    serial_port.reset_input_buffer()
    serial_port.write(b'METAMETA')
    serial_port.write(b"\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00")
#    """
    while 1:
        time.sleep(0.1)
        read_len = serial_port.inWaiting()
        if read_len:
#            resp = serial_port.read(read_len)
            print ("len %d" % read_len)
            resp = serial_port.read(13)
            break
        
    assert resp == b"READYATEM0001"
#    """
    """
    time.sleep(0.1)
    resp = serial_port.read(5)
    assert resp == b"READY"
    time.sleep(0.1)
    resp = serial_port.read(8)
    assert resp == b"ATEM0001"
    """
    serial_port.write(b"\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00")
    resp = serial_port.read(8)
    assert resp == b"ATEMATEX"
    serial_port.write(b"DISCONNECT")
    print ("Disconnect")

def Connect_Device(pid_vid,baudrate):
    while True:
        ports = list(list_ports.grep(pid_vid)) 
        if ports:
            break
        else:
            sys.stdout.write("."); sys.stdout.flush()
            time.sleep(0.2)
    sys.stdout.write("\n")
    time.sleep(0.1)
    print ("Get comport:%s - %s" % (ports[0][0],pid_vid))
    while True:
        try:
            s = Serial(ports[0][0], baudrate)
            sys.stdout.write("\n")
            break
        except SerialException:
            sys.stdout.write("."); sys.stdout.flush()
            time.sleep(0.5)
    return s

def connect():
    print ("Connect to preloader.")
    s = Connect_Device(MTK_PreLoader_VIDPID,115200)
    Connect_Preloader(s)
    s.write(b"\xa0")
    resp = s.read(5)
    s.write(b"\xa0\x0a\x50\x05")
    resp = s.read(4)
    assert resp == b"\x5f\xf5\xaf\xfa"
    print("Connected")
    return s

def DisplayHelp():
    print ("Blocks Writer version : 0.%d" % version)
    print ("Usage:  BlocksWriter [-h] [-m] [-r] [-f image_file] [-b address] [-w address] [-s numbers]")
    print ("")
    print ("Example:")
    print ("        BlocksWriter -b 741AE0600001 -w 741AE0600002 -s SOM00000111")
    print ("        BlocksWriter -f boot.img -b 741AE0600001 -w 741AE0600002 -s SOM00000111")
    print ("")
    print ("optional arguments:")
    print ("        -h            show this help message and exit.")
    print ("        -m            only reboot to meta mode.")
    print ("        -f image_file flash image file.")
    print ("        -b address    change BlueTooth address.")
    print ("        -w address    change Wifi Mac address.")
    print ("        -s number     change Serial number.")
    print ("        -r            read All data.")
    print ("engineer arguments:")
    print ("        -a            already in meta mode, don't connect to preloader and reboot.")
    print ("        -d            shut down at meta mode, muse use with -a together.")
    print ("        -m            just connect to preloader and reboot to meta mode.")
    sys.exit()



import sys
import getopt
import os.path
import time
import struct
from binascii import hexlify
from serial import Serial
from ctypes import create_string_buffer  
from array import array
test_mode = 0
show_debug_message = 0
MTK_PRELOADER = "/dev/ttyACM0"
if test_mode:
    MTK_META_MODE = "/dev/ttyACM0"
else:
    MTK_META_MODE = "/dev/ttyACM1"

HEADER  = b"\x55"
WRITE   = b"\x66"
FT_IS_ALIVE_REQ         =   8
FT_IS_ALIVE_CNF         =   9
FT_POWER_OFF_REQ        =   10#a
FT_UTILITY_COMMAND_REQ  =   14#e
FT_UTILITY_COMMAND_CNF  =   15#f
FT_AP_Editor_read_req   =   0x16#22
FT_AP_Editor_read_cnf   =   0x17#23
FT_AP_Editor_write_req  =   0x18#24
FT_AP_Editor_write_cnf  =   0x19#25
FT_CRYPTFS_REQ          =   0x91#145
FT_CRYPTFS_CNF          =   0x92#146
FT_MODEM_REQ            =   0x93#147
FT_MODEM_CNF            =   0x94#148

FT_FILE_OPERATION_REQ   =   0xa3
FT_FILE_OPERATION_CNF   =   0xa4
NVRAM_BLUETOOTH_OFFSET  =   0x01
NVRAM_WIFI_OFFSET       =   0x35#53
NVRAM_ALL_ADDR_OFFSET   =   0x3B#59

def connect_comport(device,baudrate):
    while True:
        try:
            s = Serial(device, baudrate)
            sys.stdout.write("\n")
            break
        except OSError as e:
            sys.stdout.write("."); sys.stdout.flush()
            time.sleep(0.2)
    return s

def connect_and_reboot_to_MetaMode():
    resp = s.read(5)
    assert resp == b"READY"
    print("get READY")
    s.write(b'METAMETA')
    s.write(b"\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00")
    resp = s.read(13)
    assert resp == b"READYATEM0001"
    s.write(b"\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00")
    resp = s.read(8)
    assert resp == b"ATEMATEX"
    s.write(b"DISCONNECT")

def pack_a_message(taken_count,local_param,peer_msg):
    checksum = 0
    peer_len = len(peer_msg)
    param_len = len(local_param)
    parafmt = "=hh{}s{}s".format(param_len,peer_len)
    peer = struct.pack(parafmt, param_len, peer_len, local_param, peer_msg) 
    package_len = len(peer)
    packfmt = ">chc{}s".format(package_len)
    package = struct.pack(packfmt,HEADER, package_len, WRITE, peer)
    for i in range(len(package)):
        checksum ^= package[i]
    package += bytes([checksum])
    if 1:
#    if show_debug_message:
        print ("Write msg:")
        show_raw_data(package)
    return package

def show_raw_data(raw_data):
    print ("       0x00 0x01 0x02 0x03 0x04 0x05 0x06 0x07 0x08 0x09 0x0a 0x0b 0x0c 0x0d 0x0e 0x0f")
    print ("======================================================================================")
    print ("00000: ",end ="")
    for i in range(len(raw_data)):
        if i%16==0 and i != 0:
            print ("")
            print ("00%02x0: " % int(i/16),end ="")
        print ("0x%02x " % raw_data[i],end ="")
    print ("")

def SendPrimitive(taken, cmd, para_1, para_2, peer_msg, read_len):
    if cmd is FT_CRYPTFS_REQ:
        local_param = bytearray(44)
        local_param[0] = taken
        local_param[2] = cmd
        local_param[8] = para_1
    elif cmd is FT_UTILITY_COMMAND_REQ:#16 bytes
        local_param = bytes([taken,0,cmd,0,0,0,0,0,para_1,0,0,0,para_2,0,0,0])
    elif cmd is FT_MODEM_REQ:#16 bytes
        local_param = bytes([taken,0,cmd,0,para_1,0,0,0,0,0,0,0,para_2,0,0,0])
    else:
        local_param = bytes([taken,0,cmd,0,para_1,0,para_2,0])
    s.write(pack_a_message(taken,local_param,peer_msg))
    time.sleep(0)
    return s.read(read_len)

def DisplayHelp():
    print ("Serial Number Writer version : 0.2")
    print ("Usage:  BlocksWriter [-h] [-b address] [-w address] [-s numbers]")
    print ("")
    print ("Example:")
    print ("        BlocksWriter -b 112233445566 -w 778899aabbcc -s SOM00000111")
    print ("")
    print ("optional arguments:")
    print ("        -h            show this help message and exit.")
    print ("        -b address    change BlueTooth address.")
    print ("        -w address    change Wifi Mac address.")
    print ("        -s number     change Serial number.")
    print ("        -r            read All data.")
    sys.exit()
bluetooth_addr = ""
wifi_addr = ""
serial_number = ""
read_only = ""
try:
    opts, args = getopt.getopt(sys.argv[1:], "hrb:w:s:")
except getopt.GetoptError:
    print ("Error option:%s" % sys.argv[1:])
    DisplayHelp()
for opt, arg in opts:
    if opt == "-h" or opt =="":
        print ("Input para")
        sys.exit()
    elif opt in ("-r"):
        read_only = 1
    elif opt in ("-b"):
        bluetooth_addr = arg
    elif opt in ("-w"):
        wifi_addr = arg
    elif opt in ("-s"):
        serial_number = bytes(arg,'utf-8')
if not opts:
    DisplayHelp()

if not test_mode:
    print ("Connect to preloader.")
    s = connect_comport(MTK_PRELOADER,115200)
    connect_and_reboot_to_MetaMode()
    print ("reboot to meta mode.")
    time.sleep(1)
print ("Connect to meta.")
s = connect_comport(MTK_META_MODE,921600)
s.timeout = 0.5
count = 0
peer_msg = bytes(0)
print ("check meta is alive")
while 1:
    s.read(77)
    read_data = SendPrimitive(count, FT_IS_ALIVE_REQ, 0, 0, peer_msg, 17)
    if(read_data[10] == FT_IS_ALIVE_CNF):
        sys.stdout.write("\n")
        break;
    time.sleep(1)
    sys.stdout.write("*"); sys.stdout.flush()
    count += 1
#show_raw_data(read_data)
print ("meta is alive")
""" do need
count += 1
read_data = SendPrimitive(count, FT_UTILITY_COMMAND_REQ, FT_CRYPTFS_REQ, 0, peer_msg, 28+9)
show_raw_data(read_data)
print ("utility command cnf.")
count += 1
read_data = SendPrimitive(count, FT_CRYPTFS_REQ, 0x30, 0, peer_msg, 12+9)
show_raw_data(read_data)
print ("cryptfs done.")
count += 1
read_data = SendPrimitive(count, FT_UTILITY_COMMAND_REQ, FT_MODEM_REQ, 0, peer_msg, 28+9)
show_raw_data(read_data)
print ("utility command cnf.")
count += 1
read_data = SendPrimitive(count, FT_MODEM_REQ, 0, 0, peer_msg, 108+9)
show_raw_data(read_data)
print ("modem req.")
count += 1
read_data = SendPrimitive(count, FT_UTILITY_COMMAND_REQ, FT_MODEM_REQ, 1, peer_msg, 28+9)
show_raw_data(read_data)
print ("utility command cnf.")
count += 1
read_data = SendPrimitive(count, FT_MODEM_REQ, 1, 0, peer_msg, 108+9)
show_raw_data(read_data)
print ("modem req.")
count += 1
read_data = SendPrimitive(count, FT_UTILITY_COMMAND_REQ, FT_MODEM_REQ, 3, peer_msg, 28+9)
show_raw_data(read_data)
print ("utility command cnf.")
count += 1
read_data = SendPrimitive(count, FT_MODEM_REQ, 3, 0, peer_msg, 108+9)
show_raw_data(read_data)
print ("modem req.")
count += 1
read_data = SendPrimitive(count, FT_UTILITY_COMMAND_REQ, FT_MODEM_REQ, 4, peer_msg, 28+9)
show_raw_data(read_data)
print ("utility command cnf.")
count += 1
read_data = SendPrimitive(count, FT_MODEM_REQ, 4, 0, peer_msg, 108+9)
show_raw_data(read_data)
print ("modem req.")
"""
#blue tooth write
if bluetooth_addr:
    count += 1
    peer_msg = bytes(0)
    read_data = SendPrimitive(count, FT_AP_Editor_read_req, NVRAM_BLUETOOTH_OFFSET, 1, peer_msg, 10+72+9)
#    if show_debug_message:
    show_raw_data(read_data)
    take,local_param,peer_msg,ch=struct.unpack("8s10s72ss",read_data) 
#    print ("local_param:")
#    show_raw_data(local_param)
#    print ("peer_msg:")
#    show_raw_data(peer_msg)
    count += 1
    peer_msg_a = bytearray(peer_msg)
#    show_raw_data(peer_msg)
    peer_msg_a[0] = 0x40#64
    peer_msg_a[2] = 1
    bluetooth_addr = bytes.fromhex(bluetooth_addr)
    peer_msg_a[8:14] = bluetooth_addr
#    show_raw_data(peer_msg_a)
#    peer_msg = bytes(peer_msg_a)
    read_data = SendPrimitive(count, FT_AP_Editor_write_req, NVRAM_BLUETOOTH_OFFSET, 1, peer_msg_a, 19)

#    show_raw_data(read_data)
    print ("over write bluetooth address done.")

if wifi_addr:
    count += 1
    peer_msg = bytes(0)
    read_data = SendPrimitive(count, FT_AP_Editor_read_req, NVRAM_WIFI_OFFSET, 1, peer_msg, 539)
    if show_debug_message:
        show_raw_data(read_data)
    take,local_param,peer_msg,ch=struct.unpack("8s10s520ss",read_data) 
    count += 1
    peer_msg_a = bytearray(peer_msg)
    peer_msg_a[1] = 0x02#512
    peer_msg_a[2] = 1
    wifi_addr = bytes.fromhex(wifi_addr)
    peer_msg_a[12:18] = wifi_addr
#    show_raw_data(peer_msg_a)
    read_data = SendPrimitive(count, FT_AP_Editor_write_req, NVRAM_WIFI_OFFSET, 1, peer_msg_a, 19)
#    print ("local_param:")
#    show_raw_data(read_data)
    print ("over write wifi address done.")

if serial_number or bluetooth_addr or wifi_addr:
    count += 1
    peer_msg = bytes(0)
    read_data = SendPrimitive(count, FT_AP_Editor_read_req, NVRAM_ALL_ADDR_OFFSET, 1, peer_msg, 1051)
    take,local_param,peer_msg,ch=struct.unpack("8s10s1032ss",read_data) 
    peer_msg_a = bytearray(peer_msg)
    peer_msg_a[1] = 0x04#1024
    peer_msg_a[2] = 1
    if serial_number:
        peer_msg_a[8:8+len(serial_number)] = serial_number
#        print ("set serial number")
    if bluetooth_addr:
        peer_msg_a[0x70:0x76] = bluetooth_addr
#        print ("set bt addr")
    if wifi_addr:
        peer_msg_a[0x76:0x7c] = wifi_addr
#        print ("set wifi addr")
#    show_raw_data(peer_msg_a)
    read_data = SendPrimitive(count, FT_AP_Editor_write_req, NVRAM_ALL_ADDR_OFFSET, 1, peer_msg_a, 19)
    print ("write all addr done")
    
if read_only:
    peer_msg = bytes(0)
    count += 1
    read_data = SendPrimitive(count, FT_AP_Editor_read_req, NVRAM_BLUETOOTH_OFFSET, 1, peer_msg, 10+72+9)
    take,local_param,peer_msg,ch=struct.unpack("8s10s72ss",read_data) 
    print ("Blue Tooth data:")
#    print ("local_param:")
#    show_raw_data(local_param)
#    print ("peer_msg:")
    show_raw_data(peer_msg)

    count += 1
    peer_msg = bytes(0)
    read_data = SendPrimitive(count, FT_AP_Editor_read_req, NVRAM_WIFI_OFFSET, 1, peer_msg, 539)
    take,local_param,peer_msg,ch=struct.unpack("8s10s520ss",read_data) 
    print ("Wifi data:")
#    print ("local_param:")
#    show_raw_data(local_param)
#    print ("peer_msg:")
    show_raw_data(peer_msg)

    count += 1
    peer_msg = bytes(0)
    read_data = SendPrimitive(count, FT_AP_Editor_read_req, NVRAM_ALL_ADDR_OFFSET, 1, peer_msg, 1051)
    take,local_param,peer_msg,ch=struct.unpack("8s10s1032ss",read_data) 
    print ("All data:")
#    print ("local_param:")
#    show_raw_data(local_param)
#    print ("peer_msg:")
    show_raw_data(peer_msg)

#show_raw_data(peer_msg_a)
print ("over write nvram done.")
    
print ("")

peer_msg = bytes(0)
if not test_mode:
    SendPrimitive(0, FT_POWER_OFF_REQ, 0, 0, peer_msg, 0)
    print("shutdown watch...")

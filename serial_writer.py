import struct
import time
import sys

HEADER  = b"\x55"
WRITE   = b"\x66"
FT_IS_ALIVE_REQ         =   0x08
FT_IS_ALIVE_CNF         =   0x09
FT_POWER_OFF_REQ        =   0x0a#10
FT_UTILITY_COMMAND_REQ  =   0x0e#14
FT_UTILITY_COMMAND_CNF  =   0x0f#15
FT_AP_Editor_read_req   =   0x16#22
FT_AP_Editor_read_cnf   =   0x17#23
FT_AP_Editor_write_req  =   0x18#24
FT_AP_Editor_write_cnf  =   0x19#25
FT_VER_INFO_REQ         =   0x33#51
FT_VER_INFO_CNF         =   0x34#52
FT_CRYPTFS_REQ          =   0x91#145
FT_CRYPTFS_CNF          =   0x92#146
FT_MODEM_REQ            =   0x93#147
FT_MODEM_CNF            =   0x94#148

FT_FILE_OPERATION_REQ   =   0xa3
FT_FILE_OPERATION_CNF   =   0xa4
NVRAM_BLUETOOTH_OFFSET  =   0x01
NVRAM_WIFI_OFFSET       =   0x35#53
NVRAM_ALL_ADDR_OFFSET   =   0x3B#59
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
    """
    if 1:
        print ("Write msg:")
        show_raw_data(package)
    """
    return package

def SendPrimitive(s,taken, cmd, para_1, para_2, peer_msg, read_len):
    if not peer_msg:
        peer_msg = bytes(0)
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
    return s.read(read_len),taken

def show_raw_data(raw_data):
#    print ("       0x00 0x01 0x02 0x03 0x04 0x05 0x06 0x07 0x08 0x09 0x0a 0x0b 0x0c 0x0d 0x0e 0x0f")
#    print ("======================================================================================")
    row = 0
    while raw_data:
        print ("00%02x0: " % int(row),end ="")
        row += 1
        col = 0
        for char in raw_data[:16]:#range(16):
            print ("0x%02x " % char,end ="")
            col += 1
        if (col<16):
            for c in range(col,16):
                sys.stdout.write("     ")
        sys.stdout.write(";")
        for char in raw_data[:16]:#range(16):
            if (int(char)<0x20)or(int(char)>=0x80):
                sys.stdout.write(".")
            else:
                print ("%c" % char,end ="")
        print ("")
        raw_data = raw_data[16:]
    print ("")
    
def write_nvram(serial_port, count, area, peer_msg, data):
    peer_msg_a = bytearray(peer_msg)
    peer_msg_a[0] = 0x40#64
    peer_msg_a[2] = 1
    bluetooth_addr = bytes.fromhex(data)
    peer_msg_a[8:14] = bluetooth_addr
    read_data,count = SendPrimitive(serial_port, count, FT_AP_Editor_write_req, area, 1, peer_msg_a, 19)

def read_nvram(serial_port, count, area):
    if area is NVRAM_BLUETOOTH_OFFSET:
        lenth = 72
        addfmt = "8s6s58s"
        msg = "Blue Tooth Address : "
    elif area is NVRAM_WIFI_OFFSET:
        lenth = 520
        addfmt = "12s6s502s"
        msg = "Wifi MAC Address   : "
    elif area is NVRAM_ALL_ADDR_OFFSET:
        lenth = 1032
        addfmt = "8s11s1013s"
        msg = "Serial number      : "
    read_data,count = SendPrimitive(serial_port, count, FT_AP_Editor_read_req, area, 1, 0, 8 + 10 + lenth + 1)
    parafmt = "8s10s{}ss".format(lenth)
    take,local_param,peer_msg,ch=struct.unpack(parafmt,read_data) 
#    show_raw_data(peer_msg)
    b,data,e=struct.unpack(addfmt,peer_msg) 
    print (msg,end ="")
    if area is NVRAM_ALL_ADDR_OFFSET:
        print ("%s" % bytes.decode(data))
    else:
        for char in data:
            print ("0x%02x " % char,end ="")
        print ("")
    return count,peer_msg

def check_if_func_exist(serial_port, count, func, op_code):
    read_data,count = SendPrimitive(serial_port, count, FT_UTILITY_COMMAND_REQ, func, op_code, 0, 8+28+1)
    take,local_param,ch=struct.unpack("8s28ss",read_data) 
#    show_raw_data(local_param)
    return count
    
def shutdown_meta_mode(serial_port):
    SendPrimitive(serial_port, 0, FT_POWER_OFF_REQ, 0, 0, 0, 0)
    print("shutdown watch...")
    sys.exit()
    
def get_version(serial_port, count):
    print ("get version")
    read_data,count = SendPrimitive(serial_port, count, FT_VER_INFO_REQ, 0, 0, 0, 8+458+1)
    take,local_param,ch=struct.unpack("8s458ss",read_data) 
    header,platform,n,build_date,sw_version,chip_version=struct.unpack("4s6s62s192s64s130s",local_param) 
    print ("Platform         = %s" % bytes.decode(platform))
    print ("Chip Version     = %.3s" % bytes.decode(chip_version))
    print ("Build Date       = %.20s" % bytes.decode(build_date))
    print ("Software Version = %.20s" % bytes.decode(sw_version))
    return count

def set_modem(serial_port, count):
    count = check_if_func_exist(serial_port, count, FT_CRYPTFS_REQ, 0)
    read_data,count = SendPrimitive(serial_port, count, FT_CRYPTFS_REQ, 0x30, 0, 0, 8+12+1)
    take,local_param,ch=struct.unpack("8s12ss",read_data) 
#    show_raw_data(local_param)
    count = check_if_func_exist(serial_port, count, FT_MODEM_REQ, 0)
    read_data,count = SendPrimitive(serial_port, count, FT_MODEM_REQ, 0, 0, 0, 8+108+1)
    take,local_param,ch=struct.unpack("8s108ss",read_data) 
#    show_raw_data(local_param)
    count = check_if_func_exist(serial_port, count, FT_MODEM_REQ, 1)
    read_data,count = SendPrimitive(serial_port, count, FT_MODEM_REQ, 1, 0, 0, 8+108+1)
    take,local_param,ch=struct.unpack("8s108ss",read_data) 
#    show_raw_data(local_param)
    count = check_if_func_exist(serial_port, count, FT_MODEM_REQ, 3)
    read_data,count = SendPrimitive(serial_port, count, FT_MODEM_REQ, 3, 0, 0, 8+108+1)
    take,local_param,ch=struct.unpack("8s108ss",read_data) 
#    show_raw_data(local_param)
    count = check_if_func_exist(serial_port, count, FT_MODEM_REQ, 4)
    read_data,count = SendPrimitive(serial_port, count, FT_MODEM_REQ, 4, 0, 0, 8+108+1)
    take,local_param,ch=struct.unpack("8s108ss",read_data) 
#    show_raw_data(local_param)
    return count

#################################################################
# Program:                                                      #
#   This program can flash MTK6580 Serial Number,               #
#   BT and wifi address.                                        #
#   And also can flash image.                                   #
# History:                                                      #
# 2017/11/03 : sample serial writer done                        #
# 2017/11/20 : add flash image function                         #
# 2017/12/25 : fixd flash system.img can't boot, add read cmd.  #
#                                                               #
#                           Neo Lin(starlin2@gmail.com)         #
#################################################################
import sys
import getopt
import os.path
from serial import Serial
from serial_writer import *
from image_writer import *
from common import *
already_in_meta = 0
show_debug_message = 0

bluetooth_addr  = ""
wifi_addr       = ""
serial_number   = ""
read_only       = ""
flash_file      = ""
boot_meta_only  = 0
shutdown_meta   = 0
dump_area       = 0
sn_write        = 0
preloader_reboot= 0
"""
with open("ota_scatter.txt", "r") as f:
    content = f.readlines()
content = [x.strip() for x in content]
index = 0
con = 0
file_data = [[]]
for c in range(len(content)):
    if content[c].find("partition_index")!=-1:
        file_data[index].append((content[c][(content[c].find(":")+2):]))
    if content[c].find("file_name")!=-1:
        file_data[index].append((content[c][(content[c].find(":")+2):]))
    if content[c].find("is_download")!=-1:
        file_data[index].append((content[c][(content[c].find(":")+2):]))
    if content[c].find("physical_start_addr")!=-1:
        file_data[index].append((content[c][(content[c].find(":")+2):]))
    if content[c].find("partition_size")!=-1:
        file_data[index].append((content[c][(content[c].find(":")+2):]))
        index += 1
        file_data.append([])
if os.path.exists("logo.bin"):
    print ("aaa")
for c in range(len(file_data)-1):
    for d in range(len(file_data[1])):
#        print (file_data[c][d],end ="")
        sys.stdout.write(file_data[c][d])
        sys.stdout.write("\t")
        if(d==1):
            sys.stdout.write("\t\t")
    sys.stdout.write("\n")
#    print (file_data)
for c in range(len(file_data)-1):
    if file_data[c][1]!="NONE":
        if os.path.exists(file_data[c][1]):
            print (file_data[c][1],"is exist.")
        for d in range(len(file_data[1])):
#        print (file_data[c][d],end ="")
            sys.stdout.write(file_data[c][d])
            sys.stdout.write("\t")
        sys.stdout.write("\n")
#    print (file_data)
sys.exit()
"""
try:
    opts, args = getopt.getopt(sys.argv[1:], "Rhadrmc:f:b:w:s:")
except getopt.GetoptError:
    print ("Error option:%s" % sys.argv[1:])
    DisplayHelp()
for opt, arg in opts:
    if opt == "-h" or opt =="":
        DisplayHelp()
    elif opt in ("-R"):
        preloader_reboot = 1
    elif opt in ("-r"):
        read_only = 1
    elif opt in ("-a"):
        already_in_meta = 1
        sn_write = 1
    elif opt in ("-d"):
        shutdown_meta = 1
        sn_write = 1
    elif opt in ("-m"):
        boot_meta_only = 1
        sn_write = 1
    elif opt in ("-f"):
        flash_file = arg
    elif opt in ("-b"):
        bluetooth_addr = arg
        sn_write = 1
    elif opt in ("-w"):
        wifi_addr = arg
        sn_write = 1
    elif opt in ("-c"):
        dump_area = 1#arg
    elif opt in ("-s"):
        serial_number = bytes(arg,'utf-8')
        sn_write = 1
if not opts:
    DisplayHelp()
if preloader_reboot:
    s = Connect_Device(MTK_PreLoader_VIDPID,115200)
    reboot(s)
    sys.exit()
if sn_write:
    if not already_in_meta:
        print ("Connect to preloader.")
        s = Connect_Device(MTK_PreLoader_VIDPID,115200)
        Connect_Preloader(s)
        print ("Reboot to meta mode.")
        Reboot_to_MetaMode(s)
        time.sleep(2)
    print ("Connect to meta.")
    s = Connect_Device(MTK_Meta_Mode_VIDPID,921600)
    if shutdown_meta:
        shutdown_meta_mode(s)
    if boot_meta_only:
        sys.exit()
    s.timeout = 0.5
    count = 0
    print ("Watting meta is ready")
    while 1:
        rbyte = s.inWaiting()
        if rbyte:
            print ("read%d" %rbyte)
            s.read(rbyte)#when run at reapberry need read 77 bytes first....><
        read_data,count = SendPrimitive(s, count, FT_IS_ALIVE_REQ, 0, 0, 0, 17)
        if read_data:
            if (len(read_data) == 17) and (read_data[10] == FT_IS_ALIVE_CNF):
                take,local_param,ch=struct.unpack("8s8ss",read_data)
#            show_raw_data(local_param)
                sys.stdout.write("\n")
                break;
        time.sleep(1)
        sys.stdout.write("*"); sys.stdout.flush()
#show_raw_data(read_data)
    print ("meta is ready")

    count = get_version(s,count)
    #count = set_modem(s, count)

#blue tooth write
if bluetooth_addr:
    count,peer_msg = read_nvram(s, count, NVRAM_BLUETOOTH_OFFSET)
    show_raw_data(peer_msg)
    peer_msg_a = bytearray(peer_msg)
#    show_raw_data(peer_msg)
    peer_msg_a[0] = 0x40#64
    peer_msg_a[2] = 1
    bluetooth_addr = bytes.fromhex(bluetooth_addr)
    peer_msg_a[8:14] = bluetooth_addr
#    show_raw_data(peer_msg_a)
    read_data,count = SendPrimitive(s, count, FT_AP_Editor_write_req, NVRAM_BLUETOOTH_OFFSET, 1, peer_msg_a, 19)
    print ("over write bluetooth address done.")

if wifi_addr:
    count,peer_msg = read_nvram(s, count, NVRAM_WIFI_OFFSET)
    peer_msg_a = bytearray(peer_msg)
    peer_msg_a[1] = 0x02#512
    peer_msg_a[2] = 1
    wifi_addr = bytes.fromhex(wifi_addr)
    peer_msg_a[12:18] = wifi_addr
#    show_raw_data(peer_msg_a)
    read_data,count = SendPrimitive(s, count, FT_AP_Editor_write_req, NVRAM_WIFI_OFFSET, 1, peer_msg_a, 19)
#    print ("local_param:")
#    show_raw_data(read_data)
    print ("over write wifi address done.")

if serial_number or bluetooth_addr or wifi_addr:
    count,peer_msg = read_nvram(s, count, NVRAM_ALL_ADDR_OFFSET)
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
    show_raw_data(peer_msg_a)
    read_data,count = SendPrimitive(s, count, FT_AP_Editor_write_req, NVRAM_ALL_ADDR_OFFSET, 1, peer_msg_a, 19)
    print ("write all addr done")
    
if read_only:
    count = get_version(s,count)
    count = set_modem(s, count)
    print ("Current address data is")
    count,peer_msg = read_nvram(s, count, NVRAM_BLUETOOTH_OFFSET)
    count,peer_msg = read_nvram(s, count, NVRAM_WIFI_OFFSET)
    count,peer_msg = read_nvram(s, count, NVRAM_ALL_ADDR_OFFSET)#barcode serial number
    
if sn_write:
    print ("over write nvram done.")
    shutdown_meta_mode(s)
if dump_area:
    s = connect()
    boot_da2(s)
    print("Reading flash...")
    f_read = open("nvram.bin", "wb")
    start = nvram_address
    size = 0x500000 - 1
#    size = 4096 #1024 * 1024 * 1024
    read_flash(s, start, size, f_read)
    f_read.close()
    print("Done....")


if flash_file:
    s = connect()
    boot_da2(s)
    Flash_Image(s, flash_file)

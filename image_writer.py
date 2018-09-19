import sys
import struct
from serial import Serial
from binascii import hexlify
import time
import numpy as np

CMD_READ16           = b"\xa2"
CMD_PWR_INIT         = b"\xc4"
CMD_PWR_DEINIT       = b"\xc5"
CMD_PWR_READ16       = b"\xc6"
CMD_PWR_WRITE16      = b"\xc7"
CMD_READ32           = b"\xd1"
CMD_WRITE16          = b"\xd2"
CMD_WRITE32          = b"\xd4"
CMD_JUMP_DA          = b"\xd5"
CMD_SEND_DA          = b"\xd7"
CMD_GET_TARGE_CONFIG = b"\xd8"
CMD_GET_HW_VER       = b"\xfc"
CMD_GET_HW_CODE      = b"\xfd"
CMD_GET_BL_VER       = b"\xfe"
CMD_GET_VERSION      = b"\xff" # this returns echo if security is off

nvram_address   = 0x00380000
logo_address    = 0x03da0000
boot_address    = 0x01d20000
system_address  = 0x0a800000
cache_address   = 0x46000000
userdata_address= 0x56000000
recovery_address= 0x02d20000
secro_address   = 0x09a00000

def get_da_part1_params():
    # addr, size, size_of_xxx?
    params = (0x00200000, 0x00011320, 0x00000100)
    with open("MTK_AllInOne_DA.bin", "rb") as f:
        f.seek(0x3cad54)
        data = f.read(params[1])
    return (params, data)

def get_da_part2_params():
    # addr, size, block_size
    params = (0x80000000, 0x000395b8, 0x00001000)
    with open("MTK_AllInOne_DA.bin", "rb") as f:
        f.seek(0x3dc074)
        data = f.read(params[1])
    return (params, data)

def show_percent(now, total):
    percent = (now*100/total)
    if (percent > 100):
        percent = 100
    sys.stdout.write("\rWrote percent %2.0d%%" % percent)
    sys.stdout.flush()

def cmd_echo(serial_port, cmd, resp_sz):
#    print(">", hexs(cmd))
    serial_port.write(cmd)
    echo = serial_port.read(len(cmd))
    assert echo == cmd, echo
    resp = serial_port.read(resp_sz)
#    print("<", hexs(resp))
    return resp

def cmd_noecho(serial_port, cmd, resp_sz, show=True):
    """
    if show:
        print(">", hexs(cmd))
    else:
        print("> ...")
    """
    serial_port.write(cmd)
    resp = serial_port.read(resp_sz)
#    print("<", hexs(resp))
    return resp

def write32(serial_port, addr, cnt, vals):
    resp = cmd_echo(serial_port, CMD_WRITE32 + struct.pack(">II", addr, cnt), 2)
    assert resp == b"\0\0"
    for v in vals:
        cmd_echo(serial_port, struct.pack(">I", v), 0)
    resp = cmd_echo(serial_port, b"", 2)
    assert resp == b"\0\0"

def boot_da2(serial_port):
    resp = cmd_echo(serial_port, CMD_GET_HW_CODE, 4)
    soc_id, soc_step = struct.unpack(">HH", resp)
    print("Chip: %x, stepping?: %x" % (soc_id, soc_step))

    resp = cmd_echo(serial_port, CMD_GET_HW_VER, 8)
    subver, ver, extra = struct.unpack(">HHI", resp)
    print("Hardware version: %#x, subversion: %#x, extra: %#x" % (ver, subver, extra))

    write32(serial_port, 0x10007000, 1, [0x22000064])

    cmd_noecho(serial_port, CMD_GET_BL_VER, 1)
    assert cmd_noecho(serial_port, CMD_GET_VERSION, 1) == b"\xff"
    cmd_noecho(serial_port, CMD_GET_BL_VER, 1)

    print("Downloading DA part 1")
    params, data = get_da_part1_params()
    resp = cmd_echo(serial_port, CMD_SEND_DA + struct.pack(">III", *params), 2)
    assert resp == b"\0\0"
    count = 0
    while data:
        serial_port.write(data[:1024])
        count += 1
        show_percent(count*1024,params[1])
        data = data[1024:]
    sys.stdout.write("\r\n")

    resp = cmd_echo(serial_port, b"", 2)
    resp = cmd_echo(serial_port, b"", 2)
    assert resp == b"\0\0"

    print("Starting DA part 1...")
    resp = cmd_echo(serial_port, CMD_JUMP_DA + struct.pack(">I", params[0]), 2)

    resp = cmd_echo(serial_port, b"", 41)
#    print("DA part 1 startup response:", resp)

    resp = cmd_noecho(serial_port, b"Z", 3)
    assert resp == b"\x04\x02\x9c"
#    assert resp == b"\x04\x02\x94"

    cmd_noecho(serial_port, b"\xff\x01\x00\x08\x00\x70\x07\xff\xff\x01\x00\x00\x00\x00\x00\x01\x02\x00\x00\x00\x00\x01",0)
    resp = cmd_noecho(serial_port, b"\x46\x46\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00", 4)
    assert resp == b"\0\0\0\0"

    print("Downloading DA part 2")

    params, data = get_da_part2_params()

    resp = cmd_noecho(serial_port, struct.pack(">III", *params), 1)
    assert resp == b"Z"

    BLK_SZ = 4096
    count = 0
    while data:
        serial_port.write(data[:BLK_SZ])
        assert serial_port.read(1) == b"Z"
        count += 1
        show_percent(count*BLK_SZ,params[1])
        data = data[BLK_SZ:]
    sys.stdout.write("\r\n")

    assert serial_port.read(1) == b"Z"
    resp = cmd_noecho(serial_port, b"Z", 236)
#    print(resp)
    # In this response: EMMC partition sizes, etc.
    assert resp[-1] == 0xc1

    resp = cmd_noecho(serial_port, b"r", 2)
    assert resp == b"Z\x01"
    resp = cmd_noecho(serial_port, b"r", 2)
    assert resp == b"Z\x01"

def formating(serial_port, addr, lenth):
    print("formatting: %#x-%#x" % (addr,addr+lenth))
    assert cmd_noecho(serial_port, b"`", 1) == b"Z"
    assert cmd_noecho(serial_port, b"\x08", 1) == b"Z"
    assert cmd_noecho(serial_port, b"\xa3", 2) == b"Z\x00"
    cmd_noecho(serial_port, b"Z\xd4\x02\x00\x00\x00", 0)
    resp = cmd_noecho(serial_port, struct.pack(">QQ", addr, lenth), 1)
    assert resp == b"Z"
    assert serial_port.read(1) == b"Z"
    assert serial_port.read(4) == b"\x00\x00\x00\x00"
    assert serial_port.read(1) == b"d"
    resp = cmd_noecho(serial_port, b"Z", 2)
    assert resp == b"ZZ"
    resp = cmd_noecho(serial_port, b"\xa3", 2)
    assert resp == b"Z\x00"
    cmd_noecho(serial_port, b"Z", 0)
    print("format success")

def reboot(serial_port):
    cmd_noecho(serial_port, b"\xdb\x00\xc0", 0)
    resp = cmd_noecho(serial_port, b"\x00\x00\x00\x00", 1)
    assert resp == b"Z"

def send_file(serial_port, name,address):
    with open(name, "rb") as f:
        data = f.read()
    total_len = len(data)
    cmd_noecho(serial_port, b"a\x00\x08", 0)
    cmd_noecho(serial_port, struct.pack(">QQ", address, len(data)), 0)
    resp = cmd_noecho(serial_port, b"\v\x03", 4)
    assert resp == b"\x00\x10\x00\x00"
#    resp = cmd_noecho(serial_port, b"", 1)
    assert serial_port.read(1) == b"Z"
    BLK_SZ = 1048576
    total_sum = 0
    count = 0
    start_time = time.time()
    while data:
        serial_port.write(b"Z")
        serial_port.write(data[:BLK_SZ])
        checksum = np.sum(bytearray(data[:BLK_SZ]),dtype='uint16')
        chk = struct.pack(">H",checksum)
        serial_port.write(chk)
        count += 1
        show_percent(count*BLK_SZ,total_len)
        data = data[BLK_SZ:]
        total_sum += checksum
        assert serial_port.read(1) == b"i"
    end_time = time.time()
    sys.stdout.write("\r\n")
    f.close()
    chk = struct.pack(">I",total_sum)
    serial_port.write(chk[2:])
    assert serial_port.read(1) == b"Z"
    reboot(serial_port)
#    cmd_noecho(serial_port, b"\xdb\x00\xc0", 0)
#    resp = cmd_noecho(serial_port, b"\x00\x00\x00\x00", 1)
#    assert resp == b"Z"
    print ("Download Succeeded and cost %f second" % (end_time - start_time))

def read_flash(serial_port, start, size, outf):
    sth = 2  # ??
    resp = cmd_noecho(serial_port, b"\xd6\x0c" + struct.pack(">BQQ", sth, start, size), 1)
    assert resp == b"Z"

    # After so many transferred bytes, there will be 2-byte checksum
    chksum_blk_size = 0x10000
    cmd_noecho(serial_port, struct.pack(">I", chksum_blk_size), 0)

    while size > 0:
        chunk = serial_port.read(min(size, chksum_blk_size))
        #data += chunk
        size -= len(chunk)
        chksum = struct.unpack(">H", serial_port.read(2))[0]
        chksum_my = 0
        for b in chunk:
            chksum_my += b
        assert chksum_my & 0xffff == chksum
        #print(hex(ck_my), hexs(chksum), chunk)
        outf.write(chunk)
        sys.stdout.write("."); sys.stdout.flush()
        serial_port.write(b"Z")
    print()
    print("read binary finished")
    reboot(serial_port)

def Flash_Image(serial_port, flash_file):
    resp = cmd_noecho(serial_port, b"\xa5", 1)
    assert resp == b"\x06"
    resp = cmd_noecho(serial_port, b"", 4)
    assert resp == b"\x00\x00\x07\x38"
    resp = cmd_noecho(serial_port, b"Z", 1024)
    resp = cmd_noecho(serial_port, b"", 824)
    cmd_noecho(serial_port, b"Z", 0)
    if ((flash_file != "system.img") and (flash_file != "secro.img")):
        formating(serial_port, 0x0a000000, 0x00800000)#SYS18 keystore 
   
    if ((flash_file != "logo.bin") and (flash_file != "secro.img")):
        formating(serial_port, 0x045a0000, 0x05460000)#SYS12 expdb
    
    file_address=0
    if (flash_file == "logo.bin"):
        formating(serial_port, 0x03d20000, 0x05ce0000)#SYS10 para
        file_address = logo_address
    elif (flash_file == "boot.img"):
        formating(serial_port, 0x03d20000, 0x00080000)#SYS10 para
        formating(serial_port, boot_address, 0x01000000)#SYS8 boot.img
        file_address = boot_address
    elif (flash_file == "system.img"):
        formating(serial_port, 0x0a000000, 0x3c000000)#SYS18,19 keystore and system
        formating(serial_port, 0x03d20000, 0x00080000)#SYS10 para
        file_address = system_address
    elif (flash_file == "cache.img"):
        formating(serial_port, 0x03d20000, 0x00080000)#SYS10 para
        formating(serial_port, cache_address, 0x10000000)#SYS20 cache
        file_address = cache_address
    elif (flash_file == "userdata.img"):
        formating(serial_port, 0x03d20000, 0x00080000)#SYS10 para
        formating(serial_port, userdata_address, 0x93380000)#SYS21 userdata
        file_address = userdata_address
    elif (flash_file == "recovery.img"):
        formating(serial_port, recovery_address, 0x01080000)#SYS9 recovery
        file_address = recovery_address
    elif (flash_file == "secro.img"):
        formating(serial_port, 0x045a0000, 0x06260000)#SYS12~SYS17 expdb to secro
        formating(serial_port, 0x03d20000, 0x00080000)#SYS10 para
        file_address = secro_address
    
    cmd_noecho(serial_port, b"\xe0", 0)
    resp = cmd_noecho(serial_port, b"\x00\x00\x00\x00", 1)
    assert resp == b"Z"
    resp = cmd_noecho(serial_port, b"\xa5", 1)
    assert resp == b"\x06"
    resp = cmd_noecho(serial_port, b"", 4)
    read_len = int(hexlify(resp),16)
    cmd_noecho(serial_port, b"Z", read_len)
    cmd_noecho(serial_port, b"Z", 0)
#    print (hex(file_address))
    send_file(serial_port, flash_file, file_address)


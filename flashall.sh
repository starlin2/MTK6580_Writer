#!/bin/bash
wifi_addr_start=0xaaaaaabbbbbb
bt_addr_start=0x111111333333
serial_start='som0000123456'
count=100
success=0
do_fail=0
i=0
sn_head=$(echo $serial_start | cut -c1-3)
sn_number=$(echo $serial_start | cut -c4-13)
sn_number=`echo "ibase=10;obase=10;$sn_number" | bc`
while [ i>count ];
do
    let "wifi_addr=wifi_addr_start+i"
    let "bt_addr=bt_addr_start+i"
    let "serial_number=sn_number+i"
    wifi_addr=`echo "obase=16; ${wifi_addr}" | bc`
    bt_addr=`echo "obase=16; ${bt_addr}" | bc`
    serial_number=$sn_head$(printf "%010d" $serial_number)
    echo "****************************************"
    echo "**                                    **"
    echo "**  start to flash image              **"
    echo "**  blue tooth address : $bt_addr **"
    echo "**  wifi address :       $wifi_addr **"
    echo "**  serial number :     $serial_number **"
    echo "**  count : $count                       **"
    echo "**  success : $success                       **"
    echo "**   fail   : $do_fail                       **"
    echo "**                                    **"
    echo "****************************************"
    read -p "Press any key to start..."
    sudo ./flash_tool -s ota_scatter.txt -d MTK_AllInOne_DA.bin -c firmware-upgrade
    sleep 5
    python3 blockwriter.py -w $wifi_addr -b $bt_addr -s $serial_number
    if [ $? -ne 0 ] ; then
        echo "********************************"
        echo "**                            **"
        echo "**    update fail,try again   **"
        echo "**                            **"
        echo "********************************"
        let "do_fail++"
    else
        echo "******************************"
        echo "**                          **"
        echo "**    update   success      **"
        echo "**                          **"
        echo "******************************"
        let "i++"
        let "success++"
    fi
done

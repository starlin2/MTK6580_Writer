#!/bin/bash
# Program:                                                    #
#   This program can flash MTK6580 Serial Number ,            #
#   BT and wifi address.                                      #
# History:                                                    #
# 2017/11/7     Neo Lin(starlin2@gmail.com)     Version:0.2   #
###############################################################
wifi_addr_start=0x741ae067a184
bt_addr_start=0x741ae0600064
serial_start=100
sn_head='SOMB'
#sn_head='som'
count=500
#if [ -f "current.tmp" ] ; then
#    file=current.tmp
#    seq=0
#    while read line
#    do
#        lines[$seq]=$line
#        ((seq++))
#    done < $file
#    success=${lines[0]}
#    do_fail=${lines[1]}
#else
success=0
do_fail=0
#fi
while [ $success -le $((count-1)) ];
do
    let "wifi_addr=wifi_addr_start+success"
    let "bt_addr=bt_addr_start+success"
    let "serial_number=serial_start+success"
    wifi_addr=`echo "obase=16; ${wifi_addr}" | bc`
    bt_addr=`echo "obase=16; ${bt_addr}" | bc`
    serial_number=$sn_head$(printf "%07d" $serial_number)
#    serial_number=$sn_head$(printf "%08d" $serial_number)
    show_c=$(printf "%04d" $count)
    show_s=$(printf "%04d" $success)
    show_f=$(printf "%04d" $do_fail)
    echo "*****************************************"
    echo "**                                     **"
    echo "**       start to flash image          **"
    echo "**     wifi address    : $wifi_addr  **"
    echo "**  blue tooth address : $bt_addr  **"
    echo "**    serial number    :  $serial_number  **"
    echo "**         count  : $show_c               **"
    echo "**        success : $show_s               **"
    echo "**         fail   : $show_f               **"
    echo "**                                     **"
    echo "*****************************************"
    read -p "Press any key to start..."
    ./blockwriter -w $wifi_addr -b $bt_addr -s $serial_number
#    python3 blockwriter.py -w $wifi_addr -b $bt_addr -s $serial_number
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
        let "success++"
    fi
    echo $success > current.tmp
    echo $do_fail >> current.tmp
done
success=$(printf "%04d" $success)
echo "******************************"
echo "**                          **"
echo "**       all finished       **"
echo "**  totaly flash $success pics  **"
echo "**                          **"
echo "******************************"
rm current.tmp

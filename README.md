Blocks Writer version : 0.7
Usage:  BlocksWriter [-h] [-m] [-r] [-f image_file] [-b address] [-w address] [-s numbers]

Example:
        BlocksWriter -b 741AE0600001 -w 741AE0600002 -s SOM00000111
        BlocksWriter -f boot.img -b 741AE0600001 -w 741AE0600002 -s SOM00000111

optional arguments:
        -h            show this help message and exit.
        -m            only reboot to meta mode.
        -f image_file flash image file.
        -b address    change BlueTooth address.
        -w address    change Wifi Mac address.
        -s number     change Serial number.
        -r            read All data.
engineer arguments:
        -a            already in meta mode, don't connect to preloader and reboot.
        -d            shut down at meta mode, muse use with -a together.
        -m            just connect to preloader and reboot to meta mode.

========================================================================

Flash SN and increase number automatic:

edit produce.sh to change start address of wifi,bt and serial
serial number will add header "som", write to watch data will be like
"som00000100"

and set "count" for how many pics do you want produce.

ues "./produce.sh" to execute.

===================================================================
Flash image and serial number on one key:

Step1: pre-paid sp_flash_tool.

Step2: copy BlocksWriter and flashall.sh to sp_flash_tool folder.

Step3: copy all img file to sp_flash_tool folder.

Step4: modify serial number and wifi/BT address at flashall.sh

Step5: ./flashall.sh

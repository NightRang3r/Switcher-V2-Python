# Description

This script is a result of an extensive reasearch of the Switcher V2 Protocol which was performed by Aviad Golan ([@AviadGolan](https://twitter.com/AviadGolan)) and Shai rod ([@NightRang3r](https://twitter.com/NightRang3r))

**Features:**

* Turn Device ON/OFF
* Turn Device ON/OFF using a timer
* Get Device State and Information
* Create and Delete Schedules 
* Enable/Disable a Schedule 
* Change Device name
* Change Auto shutdown configuration
* Auto discover device IP Address and State
* Configure Switcher in Access Point Mode


![alt text](https://raw.githubusercontent.com/NightRang3r/Switcher-V2-Python/master/.Screenshots/ScreenShot.png)


Product homepage: [https://www.switcher.co.il/](https://www.switcher.co.il/)

### Home Asssistant Component

Home assistant users can use this script as a command line [switch](https://home-assistant.io/components/switch.command_line/) or use the following component created by [@TomerFI](https://github.com/TomerFi/) based on this script:

[https://github.com/TomerFi/home-assistant-custom-components/tree/master/switcher_aio](https://github.com/TomerFi/home-assistant-custom-components/tree/master/switcher_aio)

### Requirements

This script requires Python 2.7 


In order to use the script you will need to extract the following parameters from a rooted android device, from a packet capture or using the "extract" feature and adjust the script parameters accordingly:

* switcherIP
* phone_id
* device_id
* device_pass

[i] The **"extract"**, **"Auto Discover"** and **"Configure Switcher in AP Mode"** features **DOES NOT require** the **switcherIP, phone_id, device_id, device_pass** parameters in order to operate


There are 3 ways to extract the required values:

1. Manually from a rooted Android Device from the switcher app sqlite db
2. Manually an unrooted Android device using a packet capture application
3. Automatically using **THIS script**

**To extract the values using this script please look at the [usage example in the usage section](https://github.com/NightRang3r/Switcher-V2-Python#extract-required-values)**

#### switcherIP = "0.0.0.0"

Change IP Address to your switcher IP

#### phone_id = "0000"

Can be found in the sqlite db on a rooted android device (/data/data/com.ogemary.smarthome/databases/myDB) in "phone" table **"uid"** column, value needs to be converted into hex and turn hex value to Little Endian
or from packet capture of an "on/off" command (a record with 147 length in wireshark, 93 bytes data (186 chars)) copy 4 chars value from 89-93 or bytes 44-46

#### device_id = "000000"

Can be found in the sqlite db on a rooted android device  (/data/data/com.ogemary.smarthome/databases/myDB) in "device" table **"did"** column needs to be converted into hex and turn hex value to Little Endian
or from packet capture of an "on/off" command (a record with 147 length in wireshark, 93 bytes data (186 chars)) copy 6 chars value from 81-87 or bytes 40-43

#### device_pass = "00000000"

Can be found in the sqlite db on a rooted android device  (/data/data/com.ogemary.smarthome/databases/myDB) in "device" table **"devicepass"** column needs to be viewd in binary mode, copy the 8 digits password
 or from packet capture of an "on/off" command (a record with 147 length in wireshark, 93 bytes data (186 chars)) copy 8 chars value from 97-105 or bytes 48-52

**Example of captured ON/OFF Packet from local lan connection to switcher device (Required values are highlighted):**
                                                                                    
 fef05d0002320102c49d8448340001000000000000000000bccbb05a00000000000000000000f0fe**44bc1e**00**711a**0000**36373731**0000000000000000000000000000000000000000000000000000000001060001000000000073290d1d


You can use this tool to convert the values into HEX:

[https://www.binaryhexconverter.com/decimal-to-hex-converter](https://www.binaryhexconverter.com/decimal-to-hex-converter)

Use this tool to convert to little endian:

[https://www.scadacore.com/tools/programming-calculators/online-hex-converter/](https://www.scadacore.com/tools/programming-calculators/online-hex-converter/)


 **Example conversion of "did" to little endian :**
 <pre>
 did from db = 2004123
 Converted to hex = 1E949B
 Little endian =  9B941E
 </pre>


# Usage:

### Extract Required Values

This feature will attempt to extract the required parameters for the operation of this script or the home assistant component

How it works ?

1. The script will listen and wait for a broadcast message from your switcher device and will extract the **device_id** paramter from the broadcast message.
2. The script will send a "magic" packet which will retrun the **phone_id** parameter
3. The script will Perform a Brute Force attack in order to find the **device_password**
4. A file with the extracted information will be created in the same directory of the script.

**Please notice the process can take between 10 seconds to 10 minutes!**

This is a guided process, which requires user intervention, **You will need to click the "Update" button in the "Auto close" screen or turn ON your switcher device in the Switcher App when prompted**.

<pre> ~# python switcher.py extract</pre>

![alt text](https://raw.githubusercontent.com/NightRang3r/Switcher-V2-Python/master/.Screenshots/extract.png)

### Discover Switcher IP Address and State


This is a "passive" feature that will **listen** to broadcasts sent by your switcher device which contains the following information:

* Device IP Address
* Device MAC Address
* Device Name
* Device ID
* Device state (ON/OFF)
* Electric Current
* Power Consumption
* Auto shutdown value as configured in the switcher app
* Auto shutdown counter

**[i]** This feature **DOES NOT** require the **switcherIP**, **phone_id**, **device_id**, **device_pass** parameters in order to operate

<pre> ~# python switcher.py discover</pre>

![alt text](https://raw.githubusercontent.com/NightRang3r/Switcher-V2-Python/master/.Screenshots/discover.png)


### Configure Switcher in Access Point Mode

**[i]** This feature **DOES NOT** require the **switcherIP**, **phone_id**, **device_id**, **device_pass** parameters in order to operate

This feature will allow you to configure your switcher device without the official application directly from this script!
This is a guided process that allowes you to associate you device to your WiFi network.

Please make sure the switcher device is in **ACCESS POINT MODE** by holding the WiFi configuration button on the switcher device for 10 seconds (until you see the blue led blinking fast) and that you are connected to the WiFi network **"Switcher Boiler XXXX"**

**WARNING::: You will not be able to control your switcher from your mobile device anymore**, But, You can always reconfigure your switcher using the official app in order to gain back control via the app but, in order to use with this script/home assistant as well you will need to extract the  **switcherIP**, **phone_id**, **device_id**, **device_pass** and configure them in the script/home assistant component as described in this readme file.

__Why and when use this feature ?__

1. You don't own a smart phone / tablet or you want to control your device using this script or Home Assistant **ONLY!**
2. The switcher app or service are not available anymore.

You don't need to configure anything in the script in order to use this feature, It will produce the necessary parameters required by this script or the home assistant component for controling the device.

<pre> ~# python switcher.py configure</pre>

![alt text](https://raw.githubusercontent.com/NightRang3r/Switcher-V2-Python/master/.Screenshots/configure.png)




### Turn off Switcher

<pre> ~# python switcher.py 0</pre>

### Turn on Switcher

<pre> ~# python switcher.py 1</pre>

### Turn on Switcher for X minutes

Value can be 1-60 minutes

<pre> ~# python switcher.py t10</pre>
<pre> ~# python switcher.py t30</pre>
<pre> ~# python switcher.py t60</pre>

### Get Switcher State

Get state will disaply the following information:

* Device Name
* Device state (ON/OFF)
* Electric Current
* Power Consumption
* Auto shutdown value as configured in the switcher app
* Auto shutdown counter

Example:

<pre> ~# python switcher.py 2</pre>


### Set Auto shutdown 

This will change the Auto shutdown value for your switcher device and will override the app setting, the change will reflect in the switcher app.

Value can be 01:00 - 23:59

Format:

<pre> ~# python switcher.py mHH:MM</pre>

Here are some examples:

3 hours example:
<pre> ~# python switcher.py m03:00</pre>

3 hours and 30 minutes example:
<pre> ~# python switcher.py m03:30 </pre>

### Schedules Information

The schedules time zone is set based on the time configured in the computer that is running this script, In case of clock/time zone changes (SUMMER/WINTER) you will need to delete the existing schedules and create them again!

### Schedule retrieval

<pre> ~# python switcher.py list </pre>

![alt text](https://raw.githubusercontent.com/NightRang3r/Switcher-V2-Python/master/.Screenshots/schedule.png)

### Create Schedule

<pre> ~# python switcher.py create </pre>

Step 1: When prompted enter a day you would like to schedule and type "exit" or press the enter key when finished
Available options: sun, mon, tue, wed, thu, fri, sat
Or use: "all" to select all days or "once" for one time only schedule

Step 2: When prompted enter start time in the following format: HH:MM

Step 3: When prompted enter end time in the following format: HH:MM

![alt text](https://raw.githubusercontent.com/NightRang3r/Switcher-V2-Python/master/.Screenshots/create_sch.png)



### Delete Schedule

This will show a all the schedule entries with the ID's, You will be prompted to enter a valid ID

<pre> ~# python switcher.py del </pre>

![alt text](https://raw.githubusercontent.com/NightRang3r/Switcher-V2-Python/master/.Screenshots/delete.png)


### Enable Schedule

This will show a all the schedule entries with the ID's, You will be prompted to enter a valid ID

<pre> ~# python switcher.py enable </pre>


### Disable Schedule

This will show a all the schedule entries with the ID's, You will be prompted to enter a valid ID

<pre> ~# python switcher.py disable </pre>



### Change device name

This will allow you to change your switcher device name

<pre> ~# python switcher.py nNAME </pre>

<pre> ~# python switcher.py nBoiler </pre>

<pre> ~# python switcher.py nSwitcher </pre>

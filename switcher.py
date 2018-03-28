# Reverse Engineering and coding by Aviad Golan @AviadGolan and Shai Rod @NightRang3r

#!/usr/bin/env python

import binascii as ba
import time
import struct
import socket
import sys
import os
import datetime
import re
import signal

########## CHANGE TO YOUR PARAMS ##########
switcherIP = "0.0.0.0" 
phone_id = "0000"  
device_id = "000000"
device_pass = "00000000"
########## DO NOT CHANGE BYOND THIS LINE  ##########


UDP_IP = "0.0.0.0"
UDP_PORT = 20002

id_list = []
data_list = []


def banner():
	print """
		=========================================================
	   	+ Switcher V2 Python                                    +
	 	+ Reverse Engineering and Coding By:                    +
	 	+ Aviad Golan (@AviadGolan) and Shai Rod (@NightRang3r) +
	 	=========================================================	 
"""
	print "Usage:\r"
	print "======\r"
	print "Off command:" + " ./" + sys.argv[0] + " 0\r"
	print "On command:" + " ./" + sys.argv[0] + " 1\r"
	print "On command duration in minutes:" + " ./" + sys.argv[0] + " t30\r"
	print "Get State:" + " ./" + sys.argv[0] + " 2\r"
	print "Set Auto shutdown setting (in hours):" + " ./" + sys.argv[0] + " m03:00\r"
	print "Retrieve Schedule from device:"  + " ./" + sys.argv[0] + " list\r"
	print "Create a Schedule:" +  " ./" + sys.argv[0] + " create\r"
	print "Delete Schedule from device:" + " ./" + sys.argv[0] + " del\r"
	print "Enable Schedule:" + " ./" + sys.argv[0] + " enable\r"
	print "Disable Schedule:" + " ./" + sys.argv[0] + " disable\r"
	print "Change switcher name:" " ./" + sys.argv[0] + " nNAME\r"
	print "Auto detect Switcher IP Address and state:" + " ./" + sys.argv[0] + " discover\r"
	print "Configure Switcher in AP Mode:" + " ./" + sys.argv[0] + " configure\r"
	print "Auto Extract the needed values for this script (device_id, phone_id and device_pass):" + " ./" + sys.argv[0] + " extract\r\n"
	sys.exit (1)

if len (sys.argv) != 2:
	banner()
elif sys.argv[1] == "0":
	sCommand = "0"
elif sys.argv[1] == "1":
	sCommand = "1"
elif sys.argv[1] == "2":
	sCommand = "2"
elif sys.argv[1].startswith('t'):
	sCommand = "1"
elif sys.argv[1].startswith('m'):
	sCommand = "2"
elif sys.argv[1].startswith('n'):
	sCommand = "2"
elif  sys.argv[1] == "list":
	sCommand = "3"
elif  sys.argv[1] == "del":
	sCommand = "3"
elif  sys.argv[1] == "create":
	sCommand = "3"
elif  sys.argv[1] == "enable":
	sCommand = "3"
elif  sys.argv[1] == "disable":
	sCommand = "3"
elif  sys.argv[1] == "discover":
	sCommand = "3"
elif sys.argv[1] == "configure":
	sCommand = "3"
elif sys.argv[1] == "extract":
	sCommand = "3"
else:
	banner()

# CRC 
def crcSignFullPacketComKey(pData, pKey):
	crc = ba.hexlify(struct.pack('>I', ba.crc_hqx(ba.unhexlify(pData), 0x1021)))
	pData = pData + crc[6:8] + crc[4:6]
	crc = crc[6:8] + crc[4:6] + ba.hexlify( pKey )
	crc = ba.hexlify(struct.pack('>I', ba.crc_hqx(ba.unhexlify(crc), 0x1021)))
	pData = pData + crc[6:8] + crc[4:6]
	return pData

# Generate Time Stamp
def getTS():
	return ba.hexlify(struct.pack('<I', int(round(time.time())))) 
# Generate Timer value
def sTimer(sMinutes):
    sSeconds = int(sMinutes) * 60
    sDelay = struct.pack('<I', sSeconds)
    return ba.hexlify(sDelay)

# Get Power consumption and Elctrical current
def getPower(res):
	b = ba.hexlify(res)[154:162]
	i = int(b[2:4]+b[0:2], 16)
	return "[+] Electric Current is: %.1f" % (i/float(220)) + "(A)\r\n" + "[+] Power consumption is: " + str(i) + "(W)"

# Auto shutdown countdown
def sTime(res):
	b = ba.hexlify(res)[178:186]
	open_time = int(b[6:8] + b[4:6] + b[2:4] + b[0:2] , 16)
	m, s = divmod(open_time, 60)
	h, m = divmod(m, 60)
	print "[*] Auto shutdown device in: %d:%02d:%02d" % (h, m, s)

#  Generate auto shutdown time 
def setAutoClose(hours):
	h, m = hours.split(':')
	mSeconds = int(h) * 3600 + int(m) * 60 
	if mSeconds < 3600:
		print "[!] Value Can't be less than 1 hour!"
		sys.exit()
	elif mSeconds > 86340:
		print "[!] Value can't be more than 23 hours and 59 minutes!"
		sys.exit()
	else:
		print "[+] Auto shutdown was set to " + str(hours) + " Hour(s)"
		return ba.hexlify(struct.pack('<I', mSeconds))

def getAutoClose(res):
	b = ba.hexlify(res)[194:202]
	open_time = int(b[6:8] + b[4:6] + b[2:4] + b[0:2] , 16)
	m, s = divmod(open_time, 60)
	h, m = divmod(m, 60)
	print "[+] Device is configured to auto shutdown in: %d:%02d" % (h, m)  + " hour(s)"
	

days = { 0x80:"Sun", 0x02:"Mon", 0x04:"Tue", 0x08:"Wed", 0x10:"Thu", 0x20:"Fri", 0x40:"Sat"}
hourRe = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')


def getDays(byteVal):
	retVal = ""
	for day in days:
		if ( day & byteVal  != 0x00):
			retVal = retVal + days[day] + " "
	return retVal

def reverseInd(data):
	b = data
	timeStamp = int(b[6:8] + b[4:6] + b[2:4] + b[0:2] , 16)
	return time.strftime("%H:%M", time.localtime(timeStamp))


def GetSch(buffer, phone_id):
	split_string = lambda x, n: [x[i:i+n] for i in range(0, len(x), n)]
	s = buffer[90:-8]
	split = split_string(s,32)
	if len(split) == 0:
		print "[+] There are no entries on your Schedule"
		sys.exit()
	else:
		for i in range(len(split)):
			print "\r"
			print "[+] Schedule ID : " + str(int(split[i][0:2], 16))
			id_list.append(str(int(split[i][0:2], 16)))
			if int(split[i][2:4], 16) == 0:
				print "[+] Enabled: False"
			elif int(split[i][2:4], 16) == 1:
				print "[+] Enabled: True"
			if split[i][4:6] == "00":
				print "[+] Occurs: Once"
			elif split[i][4:6] == "fe":
				print "[+] Occurs: Every Day"
			else:
				print "[+] Days: " + getDays(bytearray(ba.unhexlify((split[i][4:6])))[0])
			print "[+] Start time: " + reverseInd(split[i][8:16])
			print "[+] End time: " + reverseInd(split[i][16:24])
			time_id = split[i][0:2]
			on_off = split[i][2:4]
			week = split[i][4:6]
			timstate = split[i][6:8]
			start_time = reverseInd(split[i][8:16])
			end_time = reverseInd(split[i][16:24])
			total_time=(datetime.datetime.strptime(end_time,'%H:%M') - datetime.datetime.strptime(start_time,'%H:%M'))
			print "[+] Duration: " + str(total_time) + "\n"
			start_time = split[i][8:16]
			end_time = split[i][16:24]
			data_list.append(time_id + on_off + week + timstate + start_time + end_time)


def sigint_handler(signum, frame):
	print '[+] Stopped...'
	sys.exit(0)

 
signal.signal(signal.SIGINT, sigint_handler)

############# DO NOT CHANGE ############
pSession = "00000000"
pKey = "00000000000000000000000000000000"
############# DO NOT CHANGE ############


print """
		=========================================================
	   	+ Switcher V2 Python                                    +
	 	+ Reverse Engineering and Coding By:                    +
	 	+ Aviad Golan (@AviadGolan) and Shai Rod (@NightRang3r) +
	 	=========================================================
	 """
if sys.argv[1] == "extract":
	phone_id = "0000"  
	device_pass = "00000000"
	UDP_IP = "0.0.0.0"
	UDP_PORT = 20002
	sCommand = "0"
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
		sock.bind((UDP_IP, UDP_PORT))
		while True:
			print "[*] Waiting for broadcast from Switcher device..."
			data, addr = sock.recvfrom(1024) 
			if ba.hexlify(data)[0:4] != "fef0" and len(data) != 165:
					print "[!] Not a switcher broadcast message!"
			else:
				b = ba.hexlify(data)[152:160]
				ip_addr = int(b[6:8] + b[4:6] + b[2:4] + b[0:2] , 16)
				switcherIP = socket.inet_ntoa(struct.pack("<L", ip_addr))
				device_id = ba.hexlify(data)[36:42]
				break

	except Exception as e:
		print("[!] Something went wrong...")
		print "[!] " + str(e)

	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((switcherIP, 9957)) 
		
		data = "fef052000232a100" + pSession + "340001000000000000000000"  + getTS() + "00000000000000000000f0fe1c00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000"
		data = crcSignFullPacketComKey(data, pKey)
		print ("[*] Sending Login Packet to Switcher...")
		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		pSession2 = ba.hexlify(res)[16:24]
		if not pSession2:
			s.close()
			print ("[!] Operation failed, Could not acquire SessionID, Please try again...")
			sys.exit()
		else:
			data = "fef0300002320103" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00"
			data = crcSignFullPacketComKey(data, pKey)
			s.send(ba.unhexlify(data))
			res = s.recv(1024)
			print ("[+] Received SessionID: " + pSession2)
			print ('\r\nInstructions:\r')
			print ('\r\nOpen your Switcher App, perform one of the following actions and press the "Enter" key immediately:\r\n1. Turn on device, or...\n2. Click the update button in the "Auto Shutdown" screen\r\n')
			message  = raw_input('[+] Press the "Enter" key to continue...')
			print ("[*] Waiting for a valid Phone ID Packet...")
			data = "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
			s.send(ba.unhexlify(data))
			res = s.recv(1024)
			if len(res) != 87:
				print "[!] Failed to get data, Please try again!"
				s.close()
				sys.exit()
			else:
				print "[+] Found Phone ID Packet!"
				brute_start = time.time()			
				phone_id = ba.hexlify(res)[156:160]
				for i in range(0, 9999):
					device_pass = ba.hexlify("%04d"%(i))
					sys.stdout.write("\r[*] Brute forcing Device Password, Please wait:" + device_pass)
					sys.stdout.flush()
					data = "fef05d0002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "000000000000000000000000000000000000000000000000000000000106000" + sCommand + "0000000000"
					data = crcSignFullPacketComKey(data, pKey)
					s.send(ba.unhexlify(data))
					res = s.recv(1024)
					if len(res) > 44 and len(res) < 60:
						brute_end = time.time()
						total_time= time.strftime("%H:%M:%S", time.gmtime(brute_end-brute_start))
						print "\r\n[+] Found password in: " + total_time
						print "[+] Device ID: " + device_id
						print "[+] Phone ID:" + phone_id
						print "[+] Device Password: " + device_pass
						s.close()
						file = open('switcher.txt', 'w') 
						file.write("phone_id = " + '"' +  phone_id + '"\r')
						file.write("device_id = " + '"' + device_id + '"\r')
						file.write("device_pass = " + '"' + device_pass + '"\r')
						file.close() 
						print "[+] Information was written to " + os.getcwd() + "/switcher.txt"
						sys.exit()
	except Exception as e:
		print("[!] Something went wrong...")
		print "[!] " + str(e)


if sys.argv[1] == "discover":
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
		sock.bind((UDP_IP, UDP_PORT))
		while True:
			print "[*] Waiting for broadcast from Switcher device...(Press CTRL+C to abort)"
			data, addr = sock.recvfrom(1024) 
			if ba.hexlify(data)[0:4] != "fef0" and len(data) != 165:
				print "[!] Not a switcher broadcast message!"
			else:
				b = ba.hexlify(data)[152:160]
				ip_addr = int(b[6:8] + b[4:6] + b[2:4] + b[0:2] , 16)
				print "[+] Switcher IP Address: " + socket.inet_ntoa(struct.pack("<L", ip_addr))
				print "[+] Switcher MAC Address: " + ba.hexlify(data)[160:172].upper()
				print "[+] Switcher Name: " + data[42:74]
				print "[+] Device ID: " + ba.hexlify(data)[36:42]
				if ba.hexlify(data)[266:270] == "0000":
					print "[+] Device is OFF"
				else:
					print "[+] Device is ON" 
				b = ba.hexlify(data)[310:318]
				open_time = int(b[6:8] + b[4:6] + b[2:4] + b[0:2] , 16)
				imin = open_time / 60 % 60
				ihour = open_time / 60 / 60
				isec = open_time - ((imin * 60) + (ihour * 3600))
				print "[*] Device is set to auto shutdown in: " + (str(ihour) + " Hour(s) " + str(imin) + " Minute(s) " + str(isec) + " Second(s)")
				
				b = ba.hexlify(data)[294:302]
				open_time = int(b[6:8] + b[4:6] + b[2:4] + b[0:2] , 16)
				m, s = divmod(open_time, 60)
				h, m = divmod(m, 60)
				print "[*] Auto shutdown device in: %d:%02d:%02d" % (h, m, s)
				b = ba.hexlify(data)[270:278]
				i = int(b[2:4]+b[0:2], 16)
				print "[+] Electric Current is: %.1f" % (i/float(220)) + "(A)\r\n" + "[+] Power consumption is: " + str(i) + "(W)\r\n"
				
	except Exception as e:
		print("[!] Something went wrong...")
		print "[!] " + str(e)


if sys.argv[1] == "configure":
	print "\r\n****** WARNING ******\r"
	print "\rUse this option to configure your switcher to work with this script/home assistant component only or if you don't have a smartphone or the switcher app/servers are no longer available, You won't be able to control it using the official switcher app unless you reset your switcher and reconfigure it using the app again!!!\r"
	print "\r****** WARNING ******\r\n"
	phone_id = "00000000"

	completeFlag = False
	while True and not completeFlag:	
		message  = raw_input('Choose a Device Password: ')
		if ((not message and not completeFlag)) or ((len(message)) != 8) or not (message.isdigit()):
			print "[!] Please enter an 8 digit password"
		else:
			device_pass = message + "00000000000000000000000000000000000000000000000000000000"
			admin_pass = device_pass
			break

	completeFlag = False
	while True and not completeFlag:	
		message  = raw_input('Enter WiFi SSID: ')
		if ((not message and not completeFlag)) or ((len(message)) < 1):
			print "[!] Please enter Wifi SSID"
		else:
			ssid = ba.hexlify(message) + (32-len(message))*"00"
			break

	completeFlag = False
	while True and not completeFlag:	
		message  = raw_input('Enter WiFi Password: ')
		if ((not message and not completeFlag)) or ((len(message)) < 8):
			print "[!] Wifi Password needs to be at least 8 chars!"
		else:
			wifi_pass = ba.hexlify(message) + (32-len(message))*"00"
			break

	print '\r\n*** Please make sure the switcher device is in ACCESS POINT MODE by holding the wifi configuration button on the switcher device for 10 seconds (until you see the blue led blinking fast) and that you are connected to the WiFi network "Switcher Boiler XXXX" ***\r\n'
	message  = raw_input('If your switcher is in access point mode press enter to continue...')

	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
		sock.bind((UDP_IP, UDP_PORT))
		print "[*] Waiting for broadcast from Switcher device...(Press CTRL+C to abort)"
		while True:
			data, addr = sock.recvfrom(1024) 
			if (( ba.hexlify(data)[0:4] != "fef0" and len(data) != 165 )) or (( addr[0] != "192.168.1.1" )):
				print "[!] Not a switcher configuration broadcast message!"
			else:
				b = ba.hexlify(data)[152:160]	 
				switcherIP = addr[0]
				device_id = ba.hexlify(data)[36:42] + "000000"
				print "[+] Switcher Access Point Address: " + addr[0]
				print "[+] Device ID: " + ba.hexlify(data)[36:42]
				sock.close()
				break
	except Exception as e:
		print("[!] Something went wrong...")
		print "[!] " + str(e)

	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((switcherIP, 9957)) 
		data = "fef0b1000232a20000000000340001000000" + device_id + getTS() + "00000000000000000000f0fe" + phone_id + device_pass + admin_pass + ssid + wifi_pass + "01"
		data = crcSignFullPacketComKey(data, pKey)
		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		s.close()
		print "[+] Phone ID: " + phone_id[0:4]
		print "[+] Device password: " + device_pass[0:8]
		file = open('switcher.txt', 'w') 
		file.write("phone_id = " + '"' +  phone_id[0:4] + '"\r')
		file.write("device_id = " + '"' + device_id[0:6]  + '"\r')
		file.write("device_pass = " + '"' + device_pass[0:8] + '"\r')
		file.close() 
		print "[+] Information was written to " + os.getcwd() + "/switcher.txt"
		print ("[+] Done!")
		s.close()
		sys.exit()

	except Exception as e:
		print("[!] Something went wrong...")
		print "[!] " + str(e)


try:
	time.sleep(3)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((switcherIP, 9957)) 
	data = "fef052000232a100" + pSession + "340001000000000000000000"  + getTS() + "00000000000000000000f0fe1c00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000"
	data = crcSignFullPacketComKey(data, pKey)
	print ("[*] Sending Login Packet to Switcher...")
	s.send(ba.unhexlify(data))
	res = s.recv(1024)
	pSession2 = ba.hexlify(res)[16:24]
	if not pSession2:
		s.close()
		print ("[!] Operation failed, Could not acquire SessionID, Please try again...")
		sys.exit()
	else:
		print ("[+] Received SessionID: " + pSession2)

	data = "fef0300002320103" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00"
	data = crcSignFullPacketComKey(data, pKey)
	print ("[*] Getting Switcher state...")
	s.send(ba.unhexlify(data))
	res = s.recv(1024)
	print "[+] Device Name: " + res[40:72]
	state = ba.hexlify(res)[150:154]
	if sys.argv[1] == "0" and state == "0000":
		s.close()
		print "[+] Device is already OFF"
		print getPower(res)
		sys.exit()
	elif sys.argv[1] == "1" and state == "0100":
		s.close()
		print "[+] Device is already ON"
		print getPower(res)
		sTime(res)
		sys.exit()
	elif sys.argv[1] == "2" and state == "0100":
		s.close()
		print "[+] Device is ON"
		print getPower(res)
		getAutoClose(res)
		sTime(res)
		sys.exit()
	elif sys.argv[1] == "2" and state == "0000":
		s.close()
		print "[+] Device is OFF"
		print getPower(res)
		getAutoClose(res)
		sys.exit()
	elif sys.argv[1].startswith('t'):
		try:
			sMinutes = int(sys.argv[1][1:])
		except:
			print ("[!] " + sys.argv[1][1:] + " Is not a valid number!")
			sys.exit()
		if sMinutes > 0 and sMinutes <=60:
			print "[+] Turning Switcher ON for " + str(sMinutes) + " minutes..."
			data = "fef05d0002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "000000000000000000000000000000000000000000000000000000000106000" + sCommand + "00"  + sTimer(sMinutes)
			data = crcSignFullPacketComKey(data, pKey)
			s.send(ba.unhexlify(data))
			res = s.recv(1024)
			s.close()
			print ("[+] Done!")
		else:
			print "[!] Enter a value between 1-60 minutes"
			sys.exit()
	elif sys.argv[1].startswith('m'):
		if not hourRe.match(sys.argv[1][1:]):
			print "[!] Please enter a value between 01:00 - 23:59"
			sys.exit()
	
		else:
			auto_close = setAutoClose(sys.argv[1][1:])
			data ="fef05b0002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000040400" + auto_close
			data = crcSignFullPacketComKey(data, pKey)
			s.send(ba.unhexlify(data))
			res = s.recv(1024)
			s.close()
	elif sys.argv[1] == "list":
		print "[*] Retrieving schedule from device..."
		data = "fef0570002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000060000"
		data = crcSignFullPacketComKey(data, pKey)
		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		GetSch(ba.hexlify(res), phone_id + "0000")
		s.close()
	elif sys.argv[1] == "del":
		print "[*] Retrieving schedule from device..."
		data = "fef0570002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000060000"
		data = crcSignFullPacketComKey(data, pKey)
		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		GetSch(ba.hexlify(res), phone_id + "0000")
		
		completeFlag = False
		while True and not completeFlag:	
			message  = raw_input('Enter The Schedule ID you want to Delete: ')
			if not message and not completeFlag:
				print "[!] Please enter a valid ID"
			else:
				if message not in id_list:
					print "[!] ID does not exist"
				else:
					completeFlag = True
					sch_id = "0" + message
					data = "fef0580002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000080100" + sch_id
					data = crcSignFullPacketComKey(data, pKey)
					s.send(ba.unhexlify(data))
					res = s.recv(1024)
					s.close()
					print "[+] Entry " + message + " has been deleted"
					print ("[+] Done!")
	
	elif sys.argv[1] == "create":

		print "[*] Retrieving schedule from device..."
		data = "fef0570002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000060000"
		data = crcSignFullPacketComKey(data, pKey)
		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		if int(ba.hexlify(res[44:45]),16) == 8:
			print "[!] You can't create more than 8 entries"
			s.close()
			sys.exit()

		all_days = []
		
		day_of_week = { "sun":128, "mon":2, "tue":4, "wed":8, "thu":16, "fri":32, "sat":64, "all":254, "once":0 }
		print '\r\nEnter a day you would like to schedule and type "exit" or press the enter key when finished\r'
		print "Available options: sun, mon, tue, wed, thu, fri, sat\r"
		print 'Or use: "all" to select all days or "once" for one time only schedule\r' 
		completeFlag = False
		while True:
			s_days = raw_input('Enter day: ')
			if (((not s_days and completeFlag)) or (s_days == "exit" and completeFlag)):
				break
			elif s_days not in day_of_week:
				print "[!] Please enter a valid value"
			else:
				all_days.append(day_of_week[s_days])
				completeFlag = True

		
		completeFlag = False
		while True and not completeFlag:
			start_time = raw_input('Enter start time (HH:MM): ')
			if (not start_time or not hourRe.match(start_time)):
				print "[!] Please enter a valid value"
			else:
				completeFlag = True
				start_time = time.mktime(time.strptime(time.strftime("%d/%m/%Y") + ' ' + start_time, "%d/%m/%Y %H:%M"))  
				start_time = ba.hexlify(struct.pack('<I', int(start_time)))
			
		completeFlag = False
		while True and not completeFlag:
			end_time = raw_input('Enter end time (HH:MM): ')
			if (not end_time or not hourRe.match(end_time)):
				print "[!] Please enter a valid value"
			else:
				completeFlag = True
				end_time = time.mktime(time.strptime(time.strftime("%d/%m/%Y") + ' ' + end_time, "%d/%m/%Y %H:%M")) 
				end_time = ba.hexlify(struct.pack('<I', int(end_time)))
		print "[+] Schedule request sent to device..."
		on_off = "01" # enabled / disabled
		week = "%02x" % (int(sum(all_days)))
		timstate = "01" 
		start_time = start_time
		end_time = end_time
		data = "fef0630002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000030c00ff" + on_off + week + timstate + start_time + end_time
		data = crcSignFullPacketComKey(data, pKey)
		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		s.close()
		print "[+] Done!"
	
	elif sys.argv[1].startswith('n'):
		if len(sys.argv[1][1:]) > 32 or len(sys.argv[1][1:]) < 1:
			print "[!] You must enter a minimum string of 1 char maximum 64 chars"
			sys.exit()
		else:
			print "[*] Changing device name from " + res[40:72] + " to: " + sys.argv[1][1:]
			switcher_name = ba.hexlify(sys.argv[1][1:]) + (32-len(sys.argv[1][1:]))*"00"
			data = "fef0740002320202" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000" + switcher_name
			data = crcSignFullPacketComKey(data, pKey)
			s.send(ba.unhexlify(data))
			res = s.recv(1024)
			s.close()
			print "[+] Done!"
	elif sys.argv[1] == "enable":
		data = "fef0570002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000060000"
		data = crcSignFullPacketComKey(data, pKey)
		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		GetSch(ba.hexlify(res), phone_id + "0000")
		completeFlag = False
		while True and not completeFlag:	
			message  = raw_input('Enter The Schedule ID you want to enable (type "exit" to exit): ')
			if message == "exit":
				print "[+] Done!"
				break	
			if not message and not completeFlag:
				print "[!] Please enter a valid ID"	
			else:
				if message not in id_list:
					print "[!] ID does not exist"
				else:
					sch_data = data_list[int(message)]
					time_id = data_list[int(message)][0:2]
					on_off = data_list[int(message)][2:4]
					if on_off== "01":
						print "[!] Schedule is already Enabled"
					else:
						on_off = "01"
						week = data_list[int(message)][4:6]
						timstate = data_list[int(message)][6:8]
						start_time = data_list[int(message)][8:16]
						end_time = data_list[int(message)][16:24]
						data = "fef0630002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000070c00" + time_id + on_off + week + timstate + start_time + end_time
						data = crcSignFullPacketComKey(data, pKey)
						s.send(ba.unhexlify(data))
						res = s.recv(1024)
						s.close()
						sys.exit()
						print ("[+] Done!")
	elif sys.argv[1] == "disable":
			data = "fef0570002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000060000"
			data = crcSignFullPacketComKey(data, pKey)
			s.send(ba.unhexlify(data))
			res = s.recv(1024)
			GetSch(ba.hexlify(res), phone_id + "0000")
			completeFlag = False
			while True and not completeFlag:	
				message  = raw_input('Enter The Schedule ID you want to disable (type "exit" to exit): ')
				if message == "exit":
					print "[+] Done!"
					break	
				if not message and not completeFlag:
					print "[!] Please enter a valid ID"	
				else:
					if message not in id_list:
						print "[!] ID does not exist"
					else:
						sch_data = data_list[int(message)]
						time_id = data_list[int(message)][0:2]
						on_off = data_list[int(message)][2:4]
						if on_off== "00":
							print "[!] Schedule is already Disabled"
						else:
							on_off = "00"
							week = data_list[int(message)][4:6]
							timstate = data_list[int(message)][6:8]
							start_time = data_list[int(message)][8:16]
							end_time = data_list[int(message)][16:24]
							data = "fef0630002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "00000000000000000000000000000000000000000000000000000000070c00" + time_id + on_off + week + timstate + start_time + end_time
							data = crcSignFullPacketComKey(data, pKey)
							s.send(ba.unhexlify(data))
							res = s.recv(1024)
							s.close()
							sys.exit()
							print ("[+] Done!")
	else:
		data = "fef05d0002320102" + pSession2 + "340001000000000000000000" + getTS() + "00000000000000000000f0fe" + device_id + "00" + phone_id + "0000" + device_pass + "000000000000000000000000000000000000000000000000000000000106000" + sCommand + "0000000000"
		data = crcSignFullPacketComKey(data, pKey)
		if sCommand == "0":
			print ("[*] Sending OFF Command to Switcher...")
		elif sCommand == "1":
			print ("[*] Sending ON Command to Switcher...")

		s.send(ba.unhexlify(data))
		res = s.recv(1024)
		s.close()
		print ("[+] Done!")

except SystemExit:
    print("[+] Done!\r\n")
except Exception as e:
	print("[!] Something went wrong...")
	print "[!] " + str(e)

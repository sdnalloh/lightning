def getmac(interface):
	try:
		mac = open('/sys/class/net/'+interface+'/address').readline()
	except:
		mac = "00:00:00:00:00:00"
	return mac[0:17]
	
mac = getmac("wlan0").replace(":", "")
print(mac[-4:])

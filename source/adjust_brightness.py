import evdev, asyncio
import paho.mqtt.client as paho
import json

# Create unique_id
def getmac(interface):
	try:
		mac = open('/sys/class/net/'+interface+'/address').readline()
	except:
		mac = "00:00:00:00:00:00"
	return mac[0:17]
	
mac = getmac("wlan0").replace(":", "")
unique_id = f"lightning_{mac[-4:]}"
print(unique_id)

DEVICE_NAME = "Jack_Kester Pikatea Macropad"
MQTT_BROKER = "homeassistant.local"
MQTT_PORT = "1833"
MQTT_TIMEOUT = "60"
MQTT_USERNAME = "mosquito"
MQTT_PASSWORD = "mqtt-client"
CONFIG_TOPIC = f"homeassistant/device/{unique_id}/brightness/config"
AVAIL_TOPIC = "lightning/brightness/available"
STATE_TOPIC = "lightning/brightness/state"
CONFIG_MESSAGE = {
  "name": "Brightness",
  "unique_id": "brightness",
  "platform": "event",
  "availability_topic": AVAIL_TOPIC,
  "state_topic": STATE_TOPIC,
  "event_types": [
    "plus",
	"minus",
	"reset"
  ],
  "device": {
    "name": "Lightning",
	"identifiers": unique_id,
	"manufacturer": "sdnalloh",
	"model": "Raspberry Pi Zero 2 W"
  },
}
AVAIL_MESSAGE = "online"
BRIGHTNESS_PLUS = {"event_type": "plus"}
BRIGHTNESS_MINUS = {"event_type": "minus"}
BRIGHTNESS_RESET = {"event_type": "reset"}


def get_device():
	print("Input device:", DEVICE_NAME)
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for device in devices:
		#print(device.path, device.name)
		if device.name == DEVICE_NAME:
			print("Input device:", device.path)
			return device.path
	print("Input device: not found")

# Connect to macropad
device = False
try:
	device = evdev.InputDevice(get_device())
	if device:
		print("Input device: connected")
except TypeError as err:
	print("Exiting...\n")
	
def on_connect(client, userdata, flags, rc):
	print(f"Connected with result code {rc}")
	client.publish(CONFIG_TOPIC, json.dumps(CONFIG_MESSAGE), qos=1, retain=False)
	print("Sent config message")
	

client = paho.Client()
client.on_connect = on_connect
client.will_set("lightning/brightness/available", payload="offline", qos=1, retain=False)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_up = client.connect("homeassistant.local", 1883, 60)
client.loop_start()

client.publish(AVAIL_TOPIC, json.dumps(AVAIL_MESSAGE), qos=1, retain=False)
print("Sent availability message")


class KeyState:
	def __init__(self, pressed, held, count, flag):
		self.pressed = pressed
		self.held = held
		self.count = count
		self.flag = flag
		
keys = KeyState([], [], 0, False)

keys.primary = [
	"KEY_A",
	"KEY_B",
	"KEY_C",
	"KEY_D",
	"KEY_E",
	"KEY_DOWN",
	"KEY_UP",
	"KEY_R"
]

keys.secondary = [
	"KEY_LEFTCTRL",
	"KEY_LEFTALT",
	"KEY_LEFTMETA",
	"KEY_RIGHTALT",
	"KEY_RIGHTCTRL"
]

def flag_multipress():
	if keys.count > 2:
		keys.flag = True
	elif keys.count <= 2:
		keys.flag = False

def key_up(key):
	if key in keys.pressed:
		keys.pressed.remove(key)
		keys.count -= 1
	if key in keys.held:
		keys.held.remove(key)
		keys.count -= 1

def key_held(key):
	if key not in keys.held:
		keys.held.append(key)
		keys.count += 1
	if key in keys.pressed:			# key is pressed once when being held
		keys.pressed.remove(key)
		keys.count -= 1
	flag_multipress()

def key_pressed(key):
	if key not in keys.pressed:
		keys.pressed.append(key)
		keys.count += 1
	flag_multipress()

def primary_action():
	if keys.pressed[0] == "KEY_UP":
		print("Increase Brightness")
		client.publish(STATE_TOPIC, json.dumps(BRIGHTNESS_PLUS), qos=1, retain=False)
	elif keys.pressed[0] == "KEY_DOWN":
		print("Decrease Brightness")
		client.publish(STATE_TOPIC, json.dumps(BRIGHTNESS_MINUS), qos=1, retain=False)
	print(keys.pressed[0])
	
def secondary_action():
	print(keys.held[0], "+", keys.pressed[0])

def take_action():
	if len(keys.held) == 1 and len(keys.pressed) == 1:
		secondary_action()
	elif len(keys.pressed) == 1:
		primary_action()
	else:
		pass

async def get_input():
	async for event in device.async_read_loop():
		if event.type == evdev.ecodes.EV_KEY:
			key = evdev.ecodes.KEY[event.code]
			if event.value == 0:
				if keys.flag == False:
					take_action()
				key_up(key)
			elif event.value == 2 and key in keys.secondary:
				key_held(key)
			elif event.value == 1 and key in keys.primary:
				key_pressed(key)

asyncio.run(get_input())

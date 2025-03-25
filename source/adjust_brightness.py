import evdev, asyncio
import paho.mqtt.client as paho
import json
import time
import logging

# Create unique_id
def getmac(interface):
	try:
		mac = open('/sys/class/net/'+interface+'/address').readline()
	except:
		mac = "00:00:00:00:00:00"
	return mac[0:17]
	
mac = getmac("wlan0").replace(":", "")
unique_id = f"lightning_{mac[-4:]}"
logging.info("unique_id = %s", unique_id)

DEVICE_NAME = "Jack_Kester Pikatea Macropad"
MQTT_BROKER = "homeassistant.local"
MQTT_PORT = "1833"
MQTT_TIMEOUT = "60"
MQTT_USERNAME = "mosquito"
MQTT_PASSWORD = "mqtt-client"
HA_AVAIL_TOPIC = "homeassistant/status"
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
AVAIL_MESSAGE_ON = "online"
AVAIL_MESSAGE_OFF = "offline"
BRIGHTNESS_PLUS = {"event_type": "plus"}
BRIGHTNESS_MINUS = {"event_type": "minus"}
BRIGHTNESS_RESET = {"event_type": "reset"}


def get_device():
	logging.info("Input device: %s", DEVICE_NAME)
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for device in devices:
		#print(device.path, device.name)
		if device.name == DEVICE_NAME:
			logging.info("Input device: %s", device.path)
			return device.path
	logging.warning("Input device: not found")

# Connect to macropad
device = False
try:
	device = evdev.InputDevice(get_device())
	if device:
		logging.info("Input device: connected")
except TypeError as err:
	logging.critical("Exiting...\n%s", err)
	
def on_connect(client, userdata, flags, rc, properties):
	if rc == 0:
		logging.info("Connected to MQTT Broker")
		client.publish(CONFIG_TOPIC, json.dumps(CONFIG_MESSAGE), qos=1, retain=False)
		logging.info("Sent config message")
		client.subscribe(HA_AVAIL_TOPIC)
	else:
		logging.warning("Failed to connect, result code %d", rc)

def on_message(client, userdata, msg):
	logging.info("Received message on %s\n %s", msg.topic, msg.payload.decode())
	if msg.payload.decode() == "online":
		client.publish(CONFIG_TOPIC, json.dumps(CONFIG_MESSAGE), qos=1, retain=False)
		logging.info("Sent config message")

first_reconnect_delay = 1
reconnect_rate = 2
max_reconnect_count = 12
max_reconnect_delay = 60

def on_disconnect(client, userdata, rc):
	logging.info("Disconnected with result code %d", rc)
	reconnect_count, reconnect_delay = 0, first_reconnect_delay
	while reconnect_count < max_reconnect_count:
		logging.info("Reconnecting in %d seconds...", reconnect_delay)
		time.sleep(reconnect_delay)
		try:
			client.reconnect()
			logging.info("Reconnected successfully")
			return
		except Exception as err:
			logging.error("%s. Reconnect failed.", err)
		reconnect_delay *= reconnect_rate
		reconnect_delay = min(reconnect_delay, max_reconnect_delay)
		reconnect_count += 1
	logging.info("Reconnect failed after %d attempts. Exiting...\n", reconnect_count)
	
# Connect to MQTT broker
client = paho.Client(client_id=unique_id, callback_api_version=paho.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.will_set(AVAIL_TOPIC, AVAIL_MESSAGE_OFF, qos=1, retain=False)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_up = client.connect("homeassistant.local", 1883, 60)
client.loop_start()

# Senda availability message
client.publish(AVAIL_TOPIC, json.dumps(AVAIL_MESSAGE_ON), qos=1, retain=True)
logging.info("Sent availability message")


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
	match keys.pressed[0]:
		case "KEY_UP":
			logging.info("%s: Increase Brightness", keys.pressed[0])
			client.publish(STATE_TOPIC, json.dumps(BRIGHTNESS_PLUS), qos=0, retain=False)
		case "KEY_DOWN":
			logging.info("%s: Decrease Brightness", keys.pressed[0])
			client.publish(STATE_TOPIC, json.dumps(BRIGHTNESS_MINUS), qos=0, retain=False)
		case "KEY_R":
			logging.info("%s: Reset Brightness", keys.pressed[0])
			client.publish(STATE_TOPIC, json.dumps(BRIGHTNESS_RESET), qos=0, retain=False)
		case _:
			logging.info("%s: No action taken", keys.pressed[0])
	
def secondary_action():
	logging.info("%s + %s", keys.held[0], keys.pressed[0])

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

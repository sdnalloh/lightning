import paho.mqtt.client as mqtt
import time
import json

def on_connect(client, userdata, flags, rc):
	print(f"Connected with result code {rc}")

	topic = "homeautomation/device/lighting/config"

	payload = {
		"name": "Lightning",
		"uniq_id": "lightning-01",
		"state_topic": "homeautomation/device/lighting/state",
		"qos": 1,
		"device": {
			"name": "Lightning",
			"ids": ["lightning"],
			"mf": "Raspberry Pi Foundation",
			"mdl": "Raspberry Pi Zero 2 W",
		},
		"origin": {
			"name": "Pikatea Macropad GB3",
			"sw": "v1",
			"url": "https://www.pikatea.com/products/pikatea-macropad-gb3"
		},
		"cmps": {
			"key_a": {
				"platform": "button",
				"enabled_by_default": "true",
				"name": "KEY_A",
				"unique_id": "KEY_A",
				"command_topic": "homeassistant/device/lighting/set",
				"payload_press": "KEY_A",
				"availability_topic": "homeassistant/device/lightning/state",
				"qos": 0
			}
		}
	}

	# The four parameters are topic, sending content, QoS and whether retaining the message respectively
	client.publish(topic, payload=json.dumps(payload), qos=0, retain=False)

client = mqtt.Client()
client.on_connect = on_connect
client.username_pw_set("mosquito", "mqtt-client")
client.connect("homeassistant.local", 1883, 60)

client.loop_forever()

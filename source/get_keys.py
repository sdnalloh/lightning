import evdev, asyncio

DEVICE_NAME = "Jack_Kester Pikatea Macropad"

BULBS = 4

def get_device():
	print("Input device:", DEVICE_NAME)
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for device in devices:
		#print(device.path, device.name)
		if device.name == DEVICE_NAME:
			print("Input device:", device.path)
			return device.path
	print("Input device: not found")

device = False
try:
	device = evdev.InputDevice(get_device())
	if device:
		print("Input device: connected")
except TypeError as err:
	print("Exiting...\n")

#prev_event

def get_key(key):
	match key:
		case "KEY_A":
			return "yellow"
		case "KEY_B":
			return "orange"
		case "KEY_C":
			return "red"
		case "KEY_D":
			return "purple"
		case "KEY_E":
			return "blue"
		case "KEY_DOWN":
			return "left"
		case "KEY_UP":
			return "right"
		case "KEY_R":
			return "knob"
		case default:
			return key

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

def flag_multipress():
	if keys.count > 2:
		keys.flag = True
	elif keys.count <= 2:
		keys.flag = False

class Bulbs:
	def __init__(self, total, active):
		self.total = total
		self.active = active

	def add(self):
		if self.active < self.total:
			self.active += 1
		elif self.active == self.total:
			self.active = 0
		else:
			print("ERROR: Active bulbs out of range")
			print("Active bulbs: ", self.active)

bulbs = Bulbs(4, 0)

def printstate():
	print("")
	print("keys pressed: ", keys.pressed)
	print("keys held: ", keys.held)
	print("count: ", keys.count)
	print("flag: ", keys.flag)

def primary_action():
	print(keys.pressed[0])
	bulbs.add()
	print("Bulbs ON: ", bulbs.active)
	
def secondary_action():
	print(keys.held[0], "+", keys.pressed[0])

def take_action():
	if len(keys.held) == 1 and len(keys.pressed) == 1:
		secondary_action()
	elif len(keys.pressed) == 1:
		primary_action(bulbs_on)
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




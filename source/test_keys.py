import evdev

device = evdev.InputDevice('/dev/input/event0')

for event in device.read_loop():
    if event.type == evdev.ecodes.EV_KEY:
        print(evdev.ecodes.KEY[event.code], " ", event.code, " ", event.value)


from pynput import keyboard
import time

def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(key.char))
    except AttributeError:
            print('special key {0} pressed'.format(key))

def on_release(key):
    print('{0} released'.format(key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False

#keyboard_listener = keyboard.Listener(
#    on_press=on_press,
#    on_release=on_release)

#print("starting the keyboard listener")
#keyboard_listener.start()

#let the main thread sleep and then kill the listener
#time.sleep(25)
#print("Time's up. Stopping the keyboard listener")
#keyboard_listener.stop()
#keyboard_listener.join()

# Collect events until released
with keyboard.Listener(on_press = on_press, on_release = on_release) as listener:
    listener.join()

# ...or, in a non-blocking fashion:
listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)
listener.start()

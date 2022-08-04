import random
import tkinter as tk
import pyautogui
import os
import json
import random
from time import sleep
from PIL import Image, ImageTk, ImageOps
from win32api import GetMonitorInfo, MonitorFromPoint
import zipfile as zip


dir_path = os.getcwd()
wh = pyautogui.size()
with open(dir_path + "/config.json", 'r') as j:
    configs = json.loads(j.read())
default_pet = configs["default"]["pet"]
default_path = dir_path + '/pets/' + default_pet

path = default_path
monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
work_area = monitor_info.get("Work")
max_x, max_y = work_area[2], work_area[3]

cycle = 0


def create_animation_window():
    window = tk.Tk()
    window.geometry('200x200')
    window.overrideredirect(True)
    window.config(highlightbackground='blue')
    window.wm_attributes("-transparentcolor", "Blue")
    return window


def create_animation_canvas(Window):
    canvas = tk.Canvas(Window, bd=0, highlightthickness=0, relief='ridge')
    canvas.configure(bg="Blue")
    canvas.pack(fill="both", expand=True)
    return canvas


def animate_pet(window, canvas, animation, counter, position=[0, 0], direction=True):
    frames = animation["frames"]
    size = animation["size"]
    folder = False
    if type(frames) == str:
        if ".gif" in frames:
            pass
        elif "/" in frames:
            folder = frames
            frames = os.listdir(path + frames)
        else:
            raise TypeError
    elif type(frames) != list:
        raise TypeError
    frame = frames[int(counter/animation["speed"]) % len(frames)]
    if folder:
        image = Image.open(path + folder + frame)
    else:
        image = Image.open(path + frame)
    crop = animation.get("crop", False)
    if crop:
        image = image.crop((crop[0], crop[1], crop[2], crop[3]))
    image = image.resize((size[0], size[1]))
    reversed = animation.get("reversed", False)
    if reversed:
        image = ImageOps.mirror(image)
    if direction:
        image = ImageOps.mirror(image)
    img = ImageTk.PhotoImage(image)
    if "movement" in animation.keys():
        position = movement(animation, position, direction, counter)
    window.geometry(
        '{}x{}+{}+{}'.format(
            size[0], size[1],
            position[0]-size[0], position[1]-size[1])
    )
    canvas.create_image(0, 0, anchor=tk.NW, image=img)
    window.update()
    return position


def movement(animation, position, direction, counter):
    size = animation["size"]
    x = animation["movement"].get("x", False)
    y = animation["movement"].get("y", False)
    rotate = animation["movement"].get("rotate", False)
    if x and (counter % x["speed"] == 0):
        if animation["movement"].get("reversed", False) != bool(direction):
            if position[0] > size[0]:
                position[0] -= x["distance"]
            else:
                position[0] = size[0]
        elif position[0] < max_x:
            position[0] += x["distance"]
        else:
            position[0] = max_x
    if y and (counter % y["speed"] == 0):
        if animation["movement"].get("reversed"):
            if position[1] > size[1]:
                position[1] -= y["distance"]
            else:
                position[1] = size[1]
        elif position[1] < max_y:
            position[1] += y["distance"]
        else:
            position[1] = max_y
    if rotate and (counter % rotate["speed"] == 0):
        pass
    return position


def do_popup(event):
    try:
        m.tk_popup(event.x_root, event.y_root)
    finally:
        m.grab_release()


def get_animations(path=default_path):
    animations = {}
    with open(path + "animations.json", 'r') as j:
        animations = json.loads(j.read())
    weights = []
    animation_list = []
    defaults = animations.pop("defaults", {})
    refresh = 0.01
    if "refresh" in defaults:
        refresh = defaults.pop("refresh", 0.01)
    for item in animations.keys():
        weight = 0
        try:
            weight = animations[item]["weight"]
        except KeyError:
            pass
        weights.append(weight)
        for key in defaults.keys():
            if key not in animations[item].keys():
                animations[item][key] = defaults[key]
        animation_list.append(item)
    return weights, animation_list, animations, refresh


def get_pets():
    pets = os.listdir(dir_path + "/pets/")
    return pets


if __name__ == "__main__":
    path = default_path
    weights, animation_list, animations, refresh = get_animations(path)

    animation = ""

    animation_window = create_animation_window()
    animation_canvas = create_animation_canvas(animation_window)
    pets = get_pets()

    m = tk.Menu(animation_window, tearoff=0)
    animation_menu = tk.Menu()
    for a in animation_list:
        animation_menu.add_command(label=a, command=lambda anim = a: reset_animation(anim))
    pet_menu = tk.Menu()
    for p in pets:
        pet_menu.add_command(label=p, command=lambda pet = p: change_pet(pet))
    m.add_cascade(label="pets", menu=pet_menu)
    m.add_cascade(label="animations", menu=animation_menu)
    m.add_command(label="exit", command=animation_window.destroy)

    def reset_animation(anim):
        global animation, counter
        animation = anim
        counter = 0

    def change_pet(pet):
        global weights, animation_list, animations, refresh, path, m
        weights, animation_list, animations, refresh = get_animations(dir_path + '/pets/' + pet + "/")
        path = dir_path + '/pets/' + pet + "/"
        animation_menu = tk.Menu()
        for a in animation_list:
            animation_menu.add_command(label=a, command=lambda anim = a: reset_animation(anim))
        m.entryconfigure("animations", menu=animation_menu)

    looping = True
    counter = 0

    animation_canvas.bind("<Button-3>", do_popup)
    x, y = max_x, max_y
    position = [int(x/2), y]
    direction = 1

    try:
        while looping:
            if counter == 0:
                direction = bool(random.getrandbits(1))
                animation = random.choices(
                    population=animation_list,
                    weights=weights
                )[0]
            try:
                if counter >= animations[animation]["length"]:
                    counter = counter % animations[animation]["length"]
                else:
                    counter += 1
            except KeyError:
                weights, animation_list, animations, refresh = get_animations(path)
                animation = animation_list[0]
                counter = 0
            position = animate_pet(
                animation_window,
                animation_canvas,
                animations[animation],
                counter,
                position,
                direction
            )
            animation_window.attributes("-topmost", True)
            sleep(refresh)
    except tk.TclError as e:
        print(e)

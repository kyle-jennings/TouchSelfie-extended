"""
Constants for the TouchSelfie program

.. py:data:: SCREEN_H,SCREEN_W
    Dimensions in pixels of the screen attached (will be used to compute layout)
.. py:data:: EFFECT_PARAMETERS
    A dict of dict data structure to tune acquisition parameters for each snap effct
.. py:data:: SOFTWARE_BUTTONS
    A dict of dict data structure to tune software buttons (in case of no hardware buttons)
.. py:data:: HARDWARE_BUTTONS
    configuration of the hardware buttons' GPIO pins, pull_up_down state and active state
.. py:data:: EMAIL_BUTTON_IMG  
    'send_email' button icon
.. py:data:: OAUTH2_REFRESH_PERIOD
    interval between two OAuth2 token refresh (ms)
.. py:data:: HARDWARE_POLL_PERIOD = 100
    polling interval to detect hardware buttons change (ms)

.. py:data:: CONFIGURATION_FILE
    name of the configuration file (relative to scripts/ directory)
.. py:data:: APP_ID_FILE
    name of the 'application_secret' file downloaded from console.developers.google.com (relative to scripts/ directory)
.. py:data:: CREDENTIALS_STORE_FILE
    name of the automaticaly generated credentials store (relative to scripts/ directory)

"""
import os

TIMER = 3

BG_COLOR = "black";
FG_COLOR = "white";

# Obsolete: This will be autodetected at runtime
SCREEN_W = 800 ## raspi touch
SCREEN_H = 480 ## raspi touch

# Parameters for the three main effects
# None: simple shot
# Four: Collage of four shots
full_size = (1640,1232)#(2592,1944)
half_size = (820,616)

MODE_PARAMETERS = {
    "single": {
        'snap_size' : full_size, #(width, height) => preferably use integer division of camera resolution
    },
    "collage": { 
        'snap_size' : half_size,                       #(width, height) of each shots of the 2x2 collage
        'foreground_image' : os.path.join("assets", "collage_four_square.png") # Overlay image on top of the collage
    },
}

ICON_DIR = os.path.join("assets", "icons");
# piCamera Builtin effects selection list
# @see https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.image_effect
# this constant maps a subset of picamera builtin effects 
# and (optional) parameters to a thumbnail
#
# needed keys: 
# - "effect_name": the name of the piCamera image_effect
# - "effect_icon": path to the thumbnail that represents this effect (MUST be square)
# - "effect_params": (opt) parameters for the effect (see image_effect_parameter)
EFFECTS_THUMB_DIR = os.path.join("assets", "effects")

# ordered list of IMAGE_EFFECTS keys (only these will be displayed)
IMAGE_EFFECTS_LIST = [
    "none",
    "colorswap1",
    "colorswap0",
    "negative",

    "oilpaint",
    "pastel",
    "gpen",
    "sketch",

    "cartoon",
    "posterise",
    "watercolor1",
    "colorpoint1",
]

# dict of effects and parameters
IMAGE_EFFECTS = {
    "none": {
        "effect_name":"none",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "none.png")
    },
    # solarize would require some image analysis in order to set the right parameters
    "solarize": { 
        "effect_name":"solarize",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "solarize.png")
    },
    "oilpaint": {
        "effect_name":"oilpaint",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "oilpaint.png")
    },
    "cartoon": {
        "effect_name":"cartoon",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "cartoon.png")
    },
    "colorswap0": {
        "effect_name":"colorswap",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "colorswap.png"),
        "effect_params" : 0 # green faces
    },
    "colorswap1": {
        "effect_name":"colorswap",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "colorswap1.png"),
        "effect_params" : 1  # purple faces
    },
    "negative": {
        "effect_name":"negative",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "negative.png")
    },
    "pastel": {
        "effect_name":"pastel",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "pastel.png")
    },
    "posterise": {
        "effect_name":"posterise",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "posterise.png"),
        "effect_params" : 8
    },
    "gpen": {
        "effect_name":"gpen",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "gpen.png")
    },
    "sketch": {
        "effect_name":"sketch",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "sketch.png")
    },
    "watercolor1": {
        "effect_name" : "watercolor",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "watercolor_170_25.png"),
        "effect_params" : (170,25) # cyan
    },
    "colorpoint1": {
        "effect_name" : "colorpoint",
        "effect_icon": os.path.join(EFFECTS_THUMB_DIR, "colorpoint1.png"),
        "effect_params" : 1 # keep red/yellow, desaturate everything else
    }
}

# GPIO pin / Snapshots modes mapping
# 'button_pins' are matched in this order ["No effect", "Four images"]
# 'pull_up_down' activates a pull_up or a pull_down on the GPIO pin itself (no external resistor needed)
# 'active_state' should be 1 or 0: this is the value returned by the GPIO when switch is activated
HARDWARE_BUTTONS = {
    "button_pins": [10,8,12], # Change this and the following to reflect your hardware buttons
    "pull_up_down": "pull_down",        # pull_up or pull_down
    "active_state": 1         # active 1 GPIO (pull_down with switch to VDD)
}

#Keyboard shorcuts for actions
#shortcut list must be valid tkinter events
#See : http://effbot.org/tkinterbook/tkinter-events-and-bindings.htm
ACTIONS_KEYS_MAPPING = {
    "snap_single": ["s", "S", "<F1>"],
    "snap_collage": ["c", "C", "<F2>"],
    "send_email":["e", "@"],
    "send_print":["p", "P"],
    "configure":["q", "Q"],
    "quit":["<Escape>"],
    #, "send_print":["p", "P"] #Uncomment if you want to a keyboard shortcut for printing
}

#Image list for in-preview countdown
#Use as many as you want
# COUNTDOWN_OVERLAY_IMAGES[0] will be used during the last second of countdown
# COUNTDOWN_OVERLAY_IMAGES[1] will be used during 1s to 2s
# ...
# last image of the list will be used for greater counts
# (e.g. during the first 5 secs of a 10 secs countdown in this case)
COUNTDOWN_OVERLAY_IMAGES = [
    os.path.join("assets", "countdown", "1.png"),
    os.path.join("assets", "countdown", "2.png"),
    os.path.join("assets", "countdown", "3.png"),
    os.path.join("assets", "countdown", "4.png"),
    os.path.join("assets", "countdown", "5.png"),
    os.path.join("assets", "countdown", "ready.png")]

# this defines the height ratio of the countdown images wrt. the preview size
COUNTDOWN_IMAGE_MAX_HEIGHT_RATIO = 0.2 #[0. - 1.] range

# Path to button icon assets
EMAIL_BUTTON_IMG   = os.path.join(ICON_DIR, "email-icon.png")
PRINT_BUTTON_IMG   = os.path.join(ICON_DIR, "print-icon-3.png")
EFFECTS_BUTTON_IMG = os.path.join(ICON_DIR, "effects-icon.png")

# Path to icons for the software buttons (no hardware buttons setup)
SOFTWARE_BUTTONS = {
    "single": {
        "image" : os.path.join(ICON_DIR, "single-icon-3.png")
    },
    "collage": {
        "image" : os.path.join(ICON_DIR, "collage-icon-2.png")
    },
}

# audio clips
MP3S = {
    "shutter":   os.path.join("assets", "noises", "shutter-click-3.mp3"),
    "countdown": os.path.join("assets", "noises", "beep2.mp3")
}

# Interval in ms between two authentication tokens refreshing
OAUTH2_REFRESH_PERIOD = 1800000 # interval between two OAuth2 token refresh (ms)

# Polling interval for hardware buttons (ms)
HARDWARE_POLL_PERIOD = 100

# Path of various log and configuration files
CONFIGURATION_FILE     = os.path.join("..", "configuration.json")
APP_ID_FILE            = os.path.join("..", "google_client_id.json")
CREDENTIALS_STORE_FILE = os.path.join("..", "google_credentials.dat")
EMAILS_LOG_FILE        = os.path.join("..", "sendmail.log") # you should activate 'enable_mail_logging' key in configuration.json

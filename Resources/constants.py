from enum import Enum

#Callback handler types
class callback(Enum):
    VELOCITY = int(1)
    ACTIVATE = int(2)
    TOUCH = int(3)
    ID = int(4)
    IS_CLOSE = int(5)
    HOLE = int(6)
    RING = int(7)

DEBUG = False
LINE_LIMIT = 15

VERSION = "2.6.4-TESTING"

UI_HEADER_TEMPLATE = (
    "FerreTech Auto-Arousal system v{0}\n" +
    "Listening on {1}:{2}\n"
)

TEMPLATE = (
    "#Avatar file template\n\n" +
    "avtr_abc12345-1234-5678-abcd-abcdef1234567\n\n"
    "name=TEMPLATE\n\n" +
    "#Sets the value all multipliers start at\n" +
    "base_arousal_increase=0.2\n" +
    "#How quickly arousal goes down after not being touched\n" +
    "arousal_decay=0.001\n" +
    "#How long since the last touch before arousal decay begins. First value is below 1.0, second is after 1.0. Separate values with a comma\n" +
    "touch_timeout=45,90\n\n" +
    "#Supports up to 2 arousal parameters separated by commas. start value of the first is always 0 - 1.0, start value of the second will be configurable in future\n" +
    "split_arousal=False\n" +
    "split_param_start=1.0\n" +
    "arousal_parameters=erect, aroused\n\n" +
    "#VRC parameter name, sometimes needs to be the VRCFury active parameter name (Available from OSCGB in avatar debug)\n" +
    "Parameters:\n" + 
    "pre=example_param\n" +
    "pre_start=1.5\n" +
    "sps=example_param\n" +
    "sps_start=0.8\n" +
    "erect=example_param\n" +
    "aroused=example_param\n" +
    "throb=example_param\n" +
    "throb_start=1.5\n\n" +
    "#If you want different increases of arousal per plug/socket/touch zone then add its name below with its multiplier (0.0-1.0)\n" +
    "#The name below must match the name used in the OSC listener message\n\n" +
    "Balls_Touched=0.1\n" +
    "Knot=1\n\n" +
    "#OSC listener messages - One per line, separate the ID from the message with a comma\n" +
    "#These can be retrieved from the OSCGB debug menu. These are the touch zones or penetrators you want this system to watch\n" +
    "#OSC Message types: 1 - Velocity/Plugs, 3 - Touchzones, 6 - Holes/Sockets, 7 - Rings\n\n" +
    "/avatar/parameters/VFH/Zone/Touch/Balls_Touched, 3\n" +
    "/avatar/parameters/OGB/Pen/Knot, 1\n\n"
    )
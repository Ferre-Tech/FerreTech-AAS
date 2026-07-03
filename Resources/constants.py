from enum import Enum

#Callback handler types
class callback(Enum):
    VELOCITY = int(1)
    ACTIVATE = int(2)
    TOUCH = int(3)
    BIT = int(4)
    IS_CLOSE = int(5)
    HOLE = int(6)

DEBUG = False
LINE_LIMIT = 25

VERSION = "2.3.4-TESTING"

TEMPLATE = (
    "#Do not remove this template. All user configs should be numbered 1 and higher\n" +
    "0 {\n" +
    "name=template\n\n" +
    "#Sets the value all multipliers start at\n" +
    "base_arousal_increase=0.2\n" +
    "#How quickly arousal goes down after not being touched\n" +
    "arousal_decay=0.001\n" +
    "#How long since the last touch before arousal decay begins\n" +
    "touch_timeout=45\n\n" +
    "#Supports up to 2 arousal parameters separated by commas. start value of the first is always 0 - 1.0, start value of the second will be configurable in future\n" +
    "split_arousal=False\n" +
    "split_param_start=1.0\n" +
    "arousal_parameters=example1, example2\n\n" +
    "#VRC parameter name, sometimes needs to be the VRCFury active parameter name (Available from OSCGB in avatar debug)\n" +
    "Parameters:\n" + 
    "pre=example_parameter\n" +
    "sps=example_parameter\n" +
    "erect=example_parameter\n" +
    "throb=example_parameter\n\n" +
    "#If you want different increases of arousal per plug/socket/touch zone then add its name below with its multiplier (0.0-1.0)\n" +
    "#The name below must match the name used in the OSC listener message\n" +
    "Balls_Touched=0.1\n" +
    "Knot=1\n\n" +
    "#OSC listener messages - One per line, separate the ID from the message with a comma\n" +
    "#These can be retrieved from the OSCGB debug menu. These are the touch zones or penetrators you want this system to watch\n" +
    "#OSC Message types: 1 - Velocity, 3 - Touchzones, 6 - Holes/Sockets\n" +
    "/avatar/parameters/VFH/Zone/Touch/Balls_Touched, 3\n" +
    "/avatar/parameters/OGB/Pen/Knot, 1\n\n" +
    "}"
    )
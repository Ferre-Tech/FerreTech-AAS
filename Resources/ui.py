import os
from Resources.constants import LINE_LIMIT

line_limit = LINE_LIMIT
ui_header = ""
messages = []
current_arousal = 0

#Checks length of console messages list and removes the oldest entry if above the line limit
def line_check() -> bool:
    if(len(messages) > line_limit):
        messages.pop(0)
        return True
    return False

def set_ui_header(header:str) -> None:
    global ui_header
    ui_header = header

#Command line UI redraw
def redraw_ui() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    print(ui_header)
    print("Arousal: " + make_ui_meter() + "\n")

    for msg in messages:
        print(msg)

def make_ui_meter() -> str:

    ui_bar = "\033[31m~{"
    tmp = round(current_arousal, 0)
    for i in range(21):
        if i == 0:
            continue
        if tmp % 10.0 == 0 and tmp > 0:
            ui_bar += "\033[37m" + "■" + "\033[31m"
            tmp -= 10
        else:
            ui_bar += "-"
        if i == 10:
            ui_bar += "|"
    ui_bar += "}~" + "\033[37m"
    return ui_bar

def clear_ui() -> None:
    global messages
    global current_arousal
    messages = []
    current_arousal = 0.0
    redraw_ui()

#Use instead of standard print to save each previous entry
def print_to_ui(msg) -> None:
    messages.append(msg)
    if line_check():
        redraw_ui()
        return
    else:
        print(msg)
        return

def update_current_arousal(val: float) -> None:
    global current_arousal
    current_arousal = val * 100.0
    if current_arousal % 10.0 == 0:
        #updates the specific UI line within console for the arousal bar and returns the cursor back to the bottom of the list. Should update dynamically with message list length.
        lines = len(messages) + 2
        print("\r" + "\033[" + str(lines) + "A" + "\033[K" + "Arousal: " + make_ui_meter() + "\033[" + str(lines) + "B" + "\033[G", end="", flush=True)
        #redraw_ui()
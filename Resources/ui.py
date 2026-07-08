import os
from Resources.constants import LINE_LIMIT

line_limit = LINE_LIMIT

#Checks current lines against limit and redraws UI if over limit. Current unneeded as little prints to the UI.
#TODO: Remake the UI; track UI lines with a list and FIFO
def line_check(ui_lines):
    ui_lines += 1
    if(ui_lines > line_limit):
        redraw_ui()
        ui_lines = 0
    return ui_lines

#Command line UI redraw
def redraw_ui(version, serverIp, serverPort) -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Auto-Arousal system v{version}")
    print(f"Listening on {serverIp, serverPort}")
    print("")
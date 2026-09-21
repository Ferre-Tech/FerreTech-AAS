import json
import os
import re
from pathlib import Path
from Resources.constants import callback, DEBUG
from Resources.loadfile import check_for_config

#Template used for making a new file. information filled into applicable locations via str.format()
TEMPLATE = (
    "name={0}\n\n" +
    "#Sets the value all multipliers start at\n" +
    "base_arousal_increase=0.2\n" +
    "#How quickly arousal goes down after not being touched\n" +
    "arousal_decay=0.001\n" +
    "#How long since the last touch before arousal decay begins. First value is below 1.0, second is after 1.0. separate values with a comma\n" +
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
    "{1}\n\n" +
    "#OSC listener messages - One per line, separate the ID from the message with a comma\n" +
    "#These can be retrieved from the OSCGB debug menu. These are the touch zones or penetrators you want this system to watch\n" +
    "#OSC Message types: 1 - Velocity/Plugs, 3 - Touchzones, 6 - Holes/Sockets, 7 - Rings\n\n" +
    "{2}\n"
    )

#Check folder for OSC data
def get_vrc_osc(filepath):
    avatar_osc_configs = []

    try:
        os.chdir(filepath)
    except:
        print("No OSC folder for VRChat exists")
        return None

    #Since it doesn't appear there is a way to check user ID, just load all the configs from all the folders
    for folder in os.listdir(filepath):
        avatar_osc_configs += os.listdir(os.path.join(filepath, folder, "Avatars"))

    return filepath, avatar_osc_configs

#Try to load the OSC file for the supplied avatar ID
def load_osc_config(filepath: str, configs: list, avatar_id: str) -> json:
    for folder in os.listdir(filepath):
        for file in os.listdir(os.path.join(filepath, folder, "Avatars")):
            if f"{avatar_id}.json" in file:
                f = open(os.path.join(filepath, folder, "Avatars", file), "r", encoding="utf-8-sig").read()
                open(os.path.join(filepath, folder, "Avatars", file), "w", encoding="utf-8").write(f)
                
                return json.load(open(os.path.join(filepath, folder, "Avatars", file), "r"))
    else:
        print("Avatar not found in OSC configs.")
        return None

#Check and see if a config for this avatar already exists
def check_for_avatar_config (filepath: str, avatar_id: str) -> object:
    os.chdir(filepath)
    for file in os.listdir():
        with open(file, "r") as f:
            for line in f:
                if avatar_id in line:
                    return file
    return None

#Check and see if the filepath is valid. If not, make it
def filepath_is_valid(filepath):
    try:
        os.chdir(filepath)
    except FileNotFoundError:
        os.makedirs(filepath)
        return True
    except PermissionError:
        print("No permission to access this folder")
        return False
    except NotADirectoryError:
        print("Filepath is not a directory")
        return False

#Update user assigned parameters, as updating objects and order may change prefix. Don't change any further assignments
def update_user_config (params_list: list, user_config: list):
    new_conf = []
    for line in user_config:
        updated = False
        for name in params_list:
            if name == None:
                continue
            if re.split('_', name)[1] in line:
                new_conf.append(re.sub("VF[\\d0-9]*", re.split("_\\w*", name)[0], line))
                updated = True
                break
        if updated is False:
            new_conf.append(line)
    return new_conf


#Parse the OSC config and spit out a named, formatted config in the appdata folder (separate files for now)
def parse_config_file(avatar_config:dict, id:str, filepath:str) -> bool:

    if filepath_is_valid(filepath) is False: #Fail if unable to make directory
        print("Failed to write file")
        return False
    if "avtr_" not in id:
        raise OSError("Invalid avatar ID")

    parameters = avatar_config["parameters"]
    osc_msg = {}
    osc_msg["namelist"] = []
    av_name = avatar_config["name"]

    for param in parameters: #Search for OSCGB specific nomenclature in order to pull just the values we need
        msg = re.search("VF\\d+[0-9]_\\w+", param["name"])
        if msg != None:
            osc_msg["namelist"].append(msg.string)
        if ("OGB" in param["name"] or "VFH" in param["name"]) and "version" not in param["name"]:
            if param["name"] not in osc_msg:
                osc_msg[param["name"]] = param["input"]["address"]

    if len(osc_msg) == 0:
        raise ValueError("No OSCGB parameters found. Not making file")

    print(f"Attempting to export config to {os.path.join(filepath, av_name)}")

    updated_conf = ""
    try: #Try to open and update any changed prefix on parameters if a config has data
        with open(os.path.join(filepath, av_name), "r") as f:
            conf_old = []

            for line in f:
                conf_old.append(line)

            #if config exists and is not empty, try to re-write the parameter names for user set variables and write to file
            if conf_old != []:
                conf = update_user_config(osc_msg["namelist"], conf_old)
                if "avtr_" in conf[0]:
                    for line in conf:
                        updated_conf += line
            
            f.close()
    except OSError as e:
        print(e)

    try:
        with open(os.path.join(filepath, av_name), "w") as f: #Presently will simply overwrite the existing file if the ID changes but the name does not
            
            #if config was updated, write it and return
            if updated_conf != "":
                f.write(updated_conf)
                f.close()
                return True

            msg_dict = {}

            #Take dict of messages and prune it to only the root (SPS item) we need 
            for name in osc_msg:
                if name == "namelist":
                    continue
                msg = osc_msg[name]
                msg = msg.split("/")
                msg_name = msg[-2]

                if msg_name not in msg_dict and msg_name != "Version": #If parameter not yet in the dict, add it
                    msg = osc_msg[name]
                    msg = msg.split("/")
                    name = msg[-2]
                    sps_type = -1
                    for item in msg: #Set SPS type
                        match item:
                            case 'Orf':
                                sps_type = callback.HOLE.value
                            case 'Pen':
                                sps_type = callback.VELOCITY.value
                            case 'Zone':
                                sps_type = callback.TOUCH.value
                    if sps_type != -1: #Prevents empty final line being written, potentially from the version tag from OSCGB
                        msg_dict[name] = "/".join(msg[:-1]) + f", {sps_type}"
            name_str = ""
            msg_str = ""
            for name in msg_dict:
                name_str += f"{name} = 1.0\n"
                msg_str += f"{msg_dict[name]}\n"

            if len(msg_dict) < 1:
                f.close()
                os.remove(os.path.join(filepath, av_name))
                return False
            else:
                f.write(f"{id}\n\n") #Add VRC Avatar ID to reference
                f.write(TEMPLATE.format(av_name, name_str, msg_str)) #TEMPLATE takes (avatar name, list of SPS objects, list of OSC Addresses)
                f.close()
    except OSError as e:
        print("Failed to write file")
        print(e)
        return False
    return True

#Will call during runtime to build avatars if enabled (per avatar toggle) or when ran separately
def config_tool(avatar_id = "") -> None:
    if avatar_id == "":
        return False
    
    data_folder = Path.home()
    vrc_osc = Path.home()

    if os.name == 'nt':
        data_folder = os.path.join(data_folder, 'AppData\\Roaming\\FerreTech\\Avatars')
        vrc_osc = os.path.join(Path.home(), 'AppData\\LocalLow\\VRChat\\VRChat\\OSC')
    else:
        data_folder = os.path.join(data_folder, 'Documents/FerreTech')
        #Add VRC OSC folder for unix systems; Presently unknown file location

    
    check_for_config() #Makes template file, checks that the folder structure exists
    avatar = check_for_avatar_config(data_folder, avatar_id) #Look for the loaded avatar in existing configs
    filepath = ""
    
    filepath, osc_config = get_vrc_osc(vrc_osc)
    try:
        av_config = load_osc_config(filepath, osc_config, avatar_id)
    except OSError as e:
        print(e)
        return False
    try:
        if parse_config_file(av_config, avatar_id, data_folder):
            print(f"Config file written to {data_folder}.\n")
    except OSError as e:
        print(e)
        return False
    except ValueError as e:
        if DEBUG is True:
            print(e)
        return False

    return True
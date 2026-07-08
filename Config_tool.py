import json
import os
from pathlib import Path
from Resources.constants import VERSION

#Check folder for OSC data
def get_vrc_osc():
    filepath = ""
    avatar_osc_configs = []

    if os.name == 'nt':
        filepath = os.path.join(Path.home(), 'AppData\\LocalLow\\VRChat\\VRChat\\OSC\\')
    else:
        pass #Unknown filepath for linux/Mac

    try:
        os.chdir(filepath)
    except:
        print("No OSC folder for VRChat exists")
        return None

    #Since it doesn't appear there is a way to check user ID, just load all the configs from all the folders
    for folder in os.listdir(filepath):
        avatar_osc_configs += os.listdir(os.path.join(filepath, folder))

    return filepath, avatar_osc_configs

#Try to load the OSC file for the supplied avatar ID
def load_osc_config(filepath: str, configs: list, avatar_id: str) -> json:
    workingdir = filepath
    avatar_config = None
    for folder in os.listdir(workingdir):
        for file in os.listdir(os.path.join(workingdir, folder)):
            if avatar_id in str(file):
                avatar_config = json.loads(os.path.join(workingdir, folder, file))
    return avatar_config

#Parse the OSC config and spit out an AS config in the appdata folder (separate files for now)
def parse_config_file(avatar_config:dict) -> bool:
    parameters = avatar_config[parameters]
    osc_msg = {}
    av_name = avatar_config["name"]
    for param in parameters:
        if "OGB" in param["output"]["address"] or "VFH" in param["output"]["address"]:
            if param["name"] not in osc_msg:
                osc_msg += param

    filepath = "~\\"
    if os.name == 'nt':
        filepath = os.path.join(Path.home(), 'AppData\Roaming\FerretTech')
    else:
        filepath = os.path.join(Path.home(), 'Documents\FerretTech')

    print(f"Attempting to export config to {os.path.join(filepath, av_name)}")

    try:
        with open(os.path.join(filepath, av_name), "w") as f:
            f.write(osc_msg)
    except:
        print("Failed to write file")
        return False
    return True

def main():
    print(f"FerretTech Auto-Arousal system config tool v{VERSION}")
    filepath, osc_config = get_vrc_osc()
    avatar_id = ""
    av_config = load_osc_config(filepath, osc_config, avatar_id)
    if parse_config_file(av_config):
        print(f"Config file written to {filepath}. Exiting")
        raise SystemExit(0)
    else:
        print(f"Exiting")
        raise SystemExit(1)


try:
    main()
except KeyboardInterrupt:
    print("Exiting...")
    raise SystemExit(0)
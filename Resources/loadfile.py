from pathlib import Path
import os
from Resources.constants import VERSION, DEBUG, TEMPLATE

header = (
    "serverIp = 127.0.0.1\n" +
    "serverPort = 9010\n" +
    "vrcIp = 127.0.0.1\n" +
    "vrcPort = 9000\n\n" +
    f"FerreTech Arousal System {VERSION}\n\n"
    )
debug = DEBUG
version = VERSION
template = TEMPLATE

#Only checks for config containing template data, server IPs, and server ports. later to be unecessary with OSCQuery
def check_for_config() -> bool:
    filepath = ""
    
    if os.name == 'nt':
        filepath = os.path.join(Path.home(), 'AppData\\Roaming\\FerreTech')
    else:
        filepath = os.path.join(Path.home(), 'Documents/FerreTech')
        
    if debug is True:
        print(filepath)

    #Check if filepath is valid
    try:
        os.chdir(filepath)
    except FileNotFoundError:
        os.mkdir(filepath)
    except PermissionError:
        print("No permission to access this folder")
        return False
    except NotADirectoryError:
        print("Filepath is not a directory")
        return False
    
    try:
        os.chdir(os.path.join(filepath, "Avatars"))
    except FileNotFoundError:
        os.mkdir(os.path.join(filepath, "Avatars"))
    except PermissionError:
        print("No permission to access this folder")
        return False
    except NotADirectoryError:
        print("Filepath is not a directory")
        return False
    
    if debug is True:
        print("Current working directory: " + os.getcwd())

    os.chdir(filepath)

    #Check and see if the config exists; If so, open it and return to main
    if os.access(filepath + "/ASConfig.cfg",os.W_OK):
        try:
            config = open("ASConfig.cfg")
        except PermissionError:
            print("Unable to access config file")
            config.close()
            return False
        #Check if config is up to date
        current_ver = False
        for line in config:
            if version in line:
                current_ver = True
                break
        if current_ver is False:
            #Try to update the config with the updated setup
            #Attempt to keep user configs
            serverIp = "serverIp = 127.0.0.1\n"
            serverPort = "serverPort = 9010\n"
            vrcIp = "vrcIp = 127.0.0.1\n"
            vrcPort = "vrcPort = 9000\n"

            user_config = []
            config = open("ASConfig.cfg")
            for line in config:
                if "serverIp" in line:
                    serverIp = line
                elif "serverPort" in line:
                    serverPort = line
                elif "vrcIp" in line:
                    vrcIp = line
                elif "vrcPort" in line:
                    vrcPort = line
                
            config.close()
            
            global header
            global template
            header = (
                serverIp +
                serverPort +
                vrcIp +
                f"{vrcPort}\n" +
                f"FerreTech Arousal System {VERSION}\n\n"
            )
            
            #Now that the file is read and the user config is saved, try to rewrite the file if the file is writable
            if os.access("ASConfig.cfg", os.W_OK):
                try:
                    with open("ASConfig.cfg", "w") as config:

                        filedata = header

                        for line in user_config:
                            filedata += line

                        config.write(filedata)
                        config.close()
                except OSError as e:
                    print (e)
                    print ("Unable to write new config")
                    return False
                try:
                    with open(os.path.join("Avatars","#TEMPLATE#"), "w") as f:
                        f.write(TEMPLATE)
                    f.close()
                except OSError as e:
                    print(e)
                    return False
        return True
    #if it doesn't exist, try to make a new one with the template data
    print(f"Config file doesn't exist. Attempting to create file at {filepath}" + "/ASConfig.cfg")
    try:
        f = open("ASConfig.cfg", "x")
        #time.sleep(3)
    except:
        print(f"Unable to create file 'ASConfig.cfg' at {filepath}. Does this file already exist?")
        return False
    print("Created new config file")

    if debug is True:
        print(template)
    try:
        config = header
        f.write(config)
    except OSError as e:
        print(e)
        print("Unable to write template data")
        f.close()
        return False
    f.close()
    try:
        with open(os.join("Avatars","#TEMPLATE#"), "w") as f:
            f.write(TEMPLATE)
    except OSError as e:
        print(e)
        return False
    f.close()
    print(f"New config file created at {filepath}" + "/ASConfig.cfg")
    return True

def load_config(config) -> dict:
    av_config = {}
    with open(config, "r") as conf:
        for line in conf:
            data = line.rstrip("\n")
            
            data = data.strip(" ")
            data = data.strip("\t")
            #Parameters
            if "=" in data:
                tags = data.split("=")
                tags[0] = tags[0].strip()
                if len(tags) == 1:
                    tags.append("")
                else:
                    tags[1]=tags[1].strip()
                av_config[tags[0]] = tags[1]
                #OSC messages
            if "/avatar/parameters/" in data:
                msg = data.split(",")
                msg[1] = int(msg[1].strip())
                av_config[msg[0]] = msg[1]
    #We're done with the opened config file. close it and return the dict
    if debug is True:
        print(config)
    return av_config

#Output a list of available configs
#Presently prints -all- configs that exist in the configs folder
def list_configs(filepath) -> None:
    i = 1
    avail_configs = os.listdir(os.path.join(filepath))

    valid_configs = []
    for config in avail_configs:
        if "#TEMPLATE#" in config: #Ignore the template file
            continue
        with open(os.path.join(filepath, config)) as f:
            if "avtr_" in f.readline():
                valid_configs.append(config)
    msg = ""
    for item in valid_configs:
        msg += f"{i}) {item}  "
        if (i % 7) == 0:
            print(msg)
            msg = ""
        i += 1
    print(msg + "\n")
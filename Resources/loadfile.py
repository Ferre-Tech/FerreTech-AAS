from pathlib import Path
import os
from Resources.constants import VERSION, DEBUG, TEMPLATE

header = (
    "serverIp = 127.0.0.1\n" +
    "serverPort = 9010\n" +
    "vrcIp = 127.0.0.1\n" +
    "vrcPort = 9001\n\n" +
    f"JadeTech Arousal System {VERSION}\n\n"
    )
debug = DEBUG
version = VERSION
template = TEMPLATE

def check_for_config() -> bool:
    filepath = ""
    
    if os.name == 'nt':
        filepath = os.path.join(Path.home(), 'AppData\\Roaming\\JadeTech')
    else:
        filepath = os.path.join(Path.home(), 'Documents/JadeTech')
        
    if debug is True:
        print(filepath)

    #Check if filepath is valid
    exists = 1
    try:
        os.chdir(filepath)
    except FileNotFoundError:
        print("Folder does not exist")
        exists = 0
    except PermissionError:
        print("No permission to access this folder")
        exists = -1
        return False
    except NotADirectoryError:
        print("Filepath is not a directory")
        exists = -1
        return False

    if debug is True:
        print(f"Does the folder exist? {exists}")
    #If the folder doesn't exist, try to make it
    if exists == 0:
        try:
            Path(filepath).mkdir() 
        except:
            print("Unable to make new directory")
            return False
        print(f"Created new directory at {filepath}")
        try:
            os.chdir(filepath)
        except FileNotFoundError:
            print("Folder does not exist")
            return False
        except PermissionError:
            print("No permission to write to this folder")
            return False
        except NotADirectoryError:
            print("Filepath is not a directory")
            return False
    
    if debug is True:
        print("Current working directory: " + os.getcwd())

    #Check and see if the config exists; If so, open it and return the file to main
    if exists == 1:
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
            serverIp = "127.0.0.1"
            serverPort = 9010
            vrcIp = "127.0.0.1"
            vrcPort = 9000

            user_config = []
            config = open("ASConfig.cfg")
            try:
                config_start = -1
                template_start = -1
                config_end = -1
                i = 0

                for line in config:
                    if config_end != -1:
                        user_config.append(line)
                    elif "serverIp" in line:
                        serverIp = line
                    elif "serverPort" in line:
                        serverPort = line
                    elif "vrcIp" in line:
                        vrcIp = line
                    elif "vrcPort" in line:
                        serverPort = line
                    elif "JadeTech" in line:
                        config_start = i
                    elif "0 {" in line:
                        template_start = i
                    elif template_start != -1 and "}" in line:
                        config_end = i
                    i += 1
                
                config.close()
            except OSError as e:
                print(e)
                return False
            
            #Now that the file is read and the user config is saved, try to rewrite the file if the file is writable
            if os.access("ASConfig.cfg", os.W_OK):
                try:
                    with open("ASConfig.cfg", "w") as config:
                        header = (
                            f"{serverIp}" +
                            f"{serverPort}" +
                            f"{vrcIp}" +
                            f"{vrcPort}" +
                            f"JadeTech Arousal System {VERSION}\n\n"
                            )
                        template = TEMPLATE
                        filedata = header + template + "\n\n"

                        for line in user_config:
                            filedata += line

                        config.write(filedata)
                        config.close()
                except:
                    print ("Unable to write new config")
                    return False
                
                #Once the new file is written, open it again as read only and pass it back to main
                config = open("ASConfig.cfg", "r")

        return config
    #if it doesn't exist, try to make a new one with the template data
    print(f"Config file doesn't exist. Attempting to create file at {filepath}" + "\\ASConfig.cfg")
    try:
        f = open("ASConfig.cfg", "x")
        #time.sleep(3)
    except:
        print(f"Unable to create file 'ASConfig.cfg' at {filepath}. Does this file already exist?")
        f.close()
        return False
    print("Created new config file")
    
    
    #Template data written to new file:
    #serverIp = 127.0.0.1
    #serverPort = 9010
    #vrcIp = 127.0.0.1
    #vrcPort = 9001
    #
    #JadeTech Arousal System {version}\n\n
    ##Do not remove this template. All user configs should be numbered 1 and higher\n
    #0 {\n
    #name=template\n\n
    #
    ##Supports up to 2 arousal messages separated by commas. start value of the first is always 0 - 1.0, start value of the second will be configurable in future\n
    #arousal_messages=example1, example2\n\n
    #
    ##VRC parameter name, sometimes needs to be the VRCFury active parameter name (Available from OSCGB in avatar debug)\n
    #Parameters:\n
    #pre=example_parameter\n
    #sps=example_parameter\n
    #aroused=example_parameter\n
    #erect=example_parameter\n
    #throb=example_parameter\n\n
    #
    ##OSC listener messages - One per line, separate the ID from the message with a comma\n
    ##These can be retrieved from the OSCGB debug menu. These are the touch zones or penetrators you want this system to watch\n
    ##OSC Message types: 1 - Velocity, 3 - Touchzones\n
    #/avatar/parameters/VFH/Zone/Touch/Balls_Touched, 3\n
    #/avatar/parameters/OGB/Pen/Knot, 1\n\n
    #}
    #

    if debug is True:
        print(template)
    try:
        template = header + template
        f.write(template)
    except:
        print("Unable to write template data")
        f.close()
        return False
    f.close()
    print(f"New config file created at {filepath}" + "\\ASConfig.cfg")
    return True
    
def load_configs(config) -> list:
    configs = []
    i = 0
    record = False
    av_config = {}
    for line in config:
        data = line.rstrip("\n")
        
        if (f"{i} " + "{") in data:
            record = True
        elif data == "}":
            record = False
            configs.append(av_config)
            av_config = {}
            i += 1
        else:
            data = data.strip(" ")
            data = data.strip("\t")
            if "=" in data:
                tags = data.split("=")
                tags[0] = tags[0].strip()
                if len(tags) == 1:
                    tags.append("")
                else:
                    tags[1]=tags[1].strip()
                av_config[tags[0]] = tags[1]
            if "/avatar/parameters/" in data:
                msg = data.split(",")
                msg[1] = int(msg[1].strip())
                av_config[msg[0]] = msg[1]
    config.close()
    if debug is True:
        print(configs)
    return configs

#Output a list of available configs 
def list_configs(configs) -> None:
    i = 0
    for item in configs:
        if debug is True:
            print(item)
        if i == 0:
            i += 1
            continue
        print(f"{i}) {item['name']}")
        i += 1
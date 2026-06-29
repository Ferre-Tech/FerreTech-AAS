import argparse
import random
import time
import asyncio
import math
import os
from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
from pythonosc.osc_server import AsyncIOOSCUDPServer
from typing import List, Any
from pathlib import Path


#OSC Server and client details
serverIp = "127.0.0.1"
serverPort = 9010

vrcIp = "127.0.0.1"
vrcPort = 9001

#Enable to see error output on some functions
debug = False
line_limit = 15
version = "2.0.0"
filepath = ""

#Global functions

#Command line UI redraw
def redraw_ui() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Auto-Arousal system v{version}")
    print(f"Listening on {serverIp, serverPort}")
    print("")

#Checks for a change in depth of 5% or more.
#Returns an int
def depth_changed(currentPos, lastPos) -> int:
    if currentPos >= (lastPos + (lastPos * 0.1)) or currentPos <= (lastPos - (lastPos * 0.1)):
        return 1
    elif currentPos >= (lastPos + (lastPos * 0.2)) or currentPos <= (lastPos - (lastPos * 0.2)):
        return 2
    return 0

#Increases the value only when there is a detected change
def stroking(arousal, change) -> float:
    if change != 0 and arousal < 2: #increase the amount if the change is greater
        if change == 2:
            arousal += 0.025
        else:
            arousal += 0.02
    elif arousal > 2:
        arousal = 2

    print(f"arousal up {arousal}")
    return arousal, time.time()
        
#Touch timeout for flagging function
def timeout(last_touch, timeout) -> bool:
    if time.time() > last_touch + timeout:
        return True
    return False
            
def check_for_config():
    global filepath
    
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
    if os.access("ASConfig.cfg", os.R_OK):
        try:
            config = open("ASConfig.cfg")
        except PermissionError:
            print("Unable to access config file")
            config.close()
            return False
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
    
    template = ("serverIp = 127.0.0.1\n" +
                "serverPort = 9010\n" +
                "vrcIp = 127.0.0.1\n" +
                "vrcPort = 9001\n\n" +
                f"JadeTech Arousal System {version}\n\n" + 
                "#Do not remove this template. All user configs should be numbered 1 and higher\n" +
                "0 {\n" +
                "name=template\n\n" +
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
                "#OSC listener messages - One per line, separate the ID from the message with a comma\n" +
                "#These can be retrieved from the OSCGB debug menu. These are the touch zones or penetrators you want this system to watch\n" +
                "#OSC Message types: 1 - Velocity, 3 - Touchzones\n" +
                "/avatar/parameters/VFH/Zone/Touch/Balls_Touched, 3\n" +
                "/avatar/parameters/OGB/Pen/Knot, 1\n\n" +
                "}"
               )

    if debug is True:
        print(template)
    try:
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
                msg[1] = msg[1].strip()
                av_config[msg[0] + "/TouchSelf"] = msg[1]
                av_config[msg[0] + "/TouchOthers"] = msg[1]
                av_config[msg[0] + "/FrotOthers"] = msg[1]
                #in order to not have to parse each input, just make a TouchClose listener filter for each OSC message
                av_config[msg[0] + "/TouchOthersClose"] = 5
                av_config[msg[0] + "/TouchSelfClose"] = 5
                av_config[msg[0] + "/FrotOthersClose"] = 5
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
    
#Configuration for each specific set of bits. TODO: Make a config file that is read and holds this data. Possbly store in JSON format
def config_bits(bits_select, config) -> object:
    
    if debug is True:
        print(config)
    
    name = config['name']
    arousal_messages = config['arousal_parameters']
    multi_message = config['split_arousal']
    if "true" in multi_message.lower():
        multi_message = True
    else:
        multi_message = False
        
    split_param_start = float(config['split_param_start'])
    
    if ", " in arousal_messages:
        arousal_messages = arousal_messages.split(", ")
    elif "," in arousal_messages:
        arousal_messages = arousal_messages.split(",")
    else:
        arousal_messages = [arousal_messages]
    
    if debug is True:
        print(f"Arousal messages: {arousal_messages}")
    
    new_bits = Bits(name, bits_select.dispatcher, arousal_messages, split_param_start, multi_message)
    
    new_bits.add_parameter("pre", config['pre'])
    new_bits.add_parameter("sps", config['sps'])
    new_bits.add_parameter("aroused", config['aroused'])
    new_bits.add_parameter("erect", config['erect'])
    new_bits.add_parameter("throb", config['throb'])
    
    for item in config:
        if "/avatar/parameters/" in item:
            if debug is True:
                print(f"{item} : {config[item]}")
            new_bits.dispatch_add(str(item), int(config[item]))
           

    new_bits.bit = bits_select.bit
    new_bits.active = bits_select.active

    bits_select.clear_mapping()
    bits_select = None
    return new_bits

        
#Class defines and holds most functions and OSC messaging in order to communicate with a connected VRC avatar as defined in a supplied config, selected via the class value *.bit
#Classes presently are built semi-immutable in order to maintain cleaner OSC messaging and to remove unecessary OSC listeners when a new one is made
class Bits:
    def __init__(self, name, dispatcher, arousal_messages = [], split_param_start = 1.0, split_arousal_vals = False, message_preamble = "/avatar/parameters/"):
        self.name = name
        self.bit = 0
        self.__parameters = {}
        self.__arousal_messages = arousal_messages
        self.__message_preamble = message_preamble
        self.last_pos = 0.0
        self.__balls_touched = 0.0
        self.active = False
        self.__start_val = split_param_start
        self.arousal = 0.0
        self.pre = False
        self.sps = False
        self.__last_time = float("-inf")
        self.__map_list = [] #Holds OSC Message mappings for use with the server unmap function
        self.dispatcher = dispatcher
        self.dispatch_init_config()
        self.__split_arousal_val = split_arousal_vals
        self._client = udp_client.SimpleUDPClient(vrcIp, vrcPort)
        self.change = 0
        self.changed = False
        self.is_close = False
        self.__ui_lines = 0

    def __repr__(self):
        return f"Bits({self.name=}, {self.dispatcher=}, {self.__map_list=}"

    #Checks current lines against limit and redraws UI if over limit
    def line_check(self):
        self.__ui_lines += 1
        if(self.__ui_lines > line_limit):
            redraw_ui()
            self.__ui_lines = 0

    #Callbacks section for OSC Messaging and cleaning up handlers
    
    #Checks for the close bool from OSCGB
    def is_close_callback(self, address: str, is_close) -> None:
        #print(f"Close: {is_close}")
        self.is_close = bool(is_close)
    
    #Grabs the OSC float value of the reciever for depth
    def velocity_callback(self, address: str, *args: List[Any]) -> None:
        current_pos = round(args[0], 3) #Round to 3 decimal places to avoid messy numbers
        self.change = depth_changed(current_pos, self.last_pos)
        self.last_pos = current_pos

    #Enable and disable the system
    def activate_callback(self, address: str, activate) -> None:
        self.line_check()
        if activate:
            print("Arousal System activated")
        if activate is not True:
            print("Arousal System deactivated")
        self.active = activate

    #Touch zone callback
    def jangledJewels_callback(self, address: str, x) -> None:
        self.__balls_touched = x
    
    #Bit config select callback
    def bit_select_callback(self, address: str, x) -> None:
        if self.bit != 0:
            self.changed = True
        self.line_check()
        print(f"Bit set: {x}")
        self.bit = x

    #Add dispatcher OSC message mapping
    def dispatch_add(self, oscmsg, callback_id):
        if debug is True:
            print(f"{oscmsg}:{callback_id}")
        if callback_id == 0:
            raise Exception("No valid callback supplied")
            return
        self.line_check()
        print(f"Adding OSC listener for {oscmsg}")
        self.__map_list.append(oscmsg)
        self.dispatcher.map(oscmsg, self.get_handler(callback_id))
        
    #Default callbacks all configs will use
    def dispatch_init_config(self):
        self.dispatcher.map("/avatar/parameters/arousalsys/activate", self.get_handler(2))
        self.dispatcher.map("/avatar/parameters/arousalsys/bit", self.get_handler(4))
        self.__map_list.append("/avatar/parameters/arousalsys/activate")
        self.__map_list.append("/avatar/parameters/arousalsys/bit")

    #OSC Helper functions

    #Because OSC handlers aren't hashable, make a get for each for use within unmap function
    def get_handler(self, handler_id):
        match handler_id:
            case 1:
                return self.velocity_callback
            case 2:
                return self.activate_callback
            case 3:
                return self.jangledJewels_callback
            case 4:
                return self.bit_select_callback
            case 5:
                return self.is_close_callback
            case _:
                raise Exception("No valid handler ID supplied")
    
    def clear_mapping(self):
        #Since no nice methods exist for handling specific dynamic handler unmapping, do them all and only throw errors if debug is enabled
        for mapping in self.__map_list:
            try:
                self.dispatcher.unmap(mapping, self.get_handler(1))
            except ValueError:
                if debug == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(1)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(2))
            except ValueError:
                if debug == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(1)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(3))
            except ValueError:
                if debug == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(1)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(4))
            except ValueError:
                if debug == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(1)}")
    
    def add_parameter(self, param_key, param):
        self.__parameters[param_key] = param

    def get_message(self, parameter):
        if debug is True:
            print(f"Param: {parameter}, {self.__message_preamble}{self.__parameters[parameter]}")
        return f"{self.__message_preamble}{self.__parameters[parameter]}"

    def flagging(self):
        if self.arousal > 0.005:
            self.arousal -= 0.001
        
        if self.arousal < 0.005 and self.arousal >= 0.0: #reset everything
            self.__pre = False
            self.__sps = False
            self.arousal = 0.0

    def send_message(self, msg, val):
        self._client.send_message(msg, val)
        #print(f"Message sent: {msg}, {val}")

    def send_arousal(self):
        if self.__split_arousal_val is True:
            if debug is True:
                print(f"{self.get_message(self.arousal_messages[0])}, {self.arousal}")
            if self.arousal < self.__start_val:
                self.send_message(self.get_message(self.__arousal_messages[0]), self.arousal)
            elif self.arousal > self.__start_val:
                self.send_message(self.get_message(self.__arousal_messages[0]), self.arousal)
                sec_val = float(self.arousal) - float(self.__start_val)
                self.send_message(self.get_message(self.__arousal_messages[1]), sec_val)
        else:
            for message in self.__arousal_messages:
                self.send_message(self.get_message(message), self.arousal)

#Main async loop
async def arousalloop(dispatcher):
    
    #Make a default class to track the change of bit state
    vr_bits = Bits("None", dispatcher)
    start_time = time.time()

    #Check and see if the config exists. If not, make a new one. If it does, return the file and continue
    result = False
    try:
        result = check_for_config()
    except OSError as e:
        print(e)
    if result is False:
        print("Unable to create or load config file. Exiting.")
        input("Press enter to continue...")
        return
    if result is True:
        #If no previous config existed, a file was created, and the user needs to add their config to the file
        print("Please add your config using the template provided and restart this program")
        input("Press enter to continue...")
        return
    #Try to load all configs from the file. There should always be a 0 config, making every further config 1 based
    loaded_configs = {}
    try:
        loaded_configs = load_configs(result)
    except OSError as e:
        print(e)
        print("Failed to get configs from file")
        input("Press enter to continue...")
        return
    num_configs = len(loaded_configs)

    if loaded_configs[0]["name"] == "template" and num_configs == 1:
        print("No configs loaded. Please update the config file")
        
        input("Press enter to continue...")
        return
    else:
        num_configs = num_configs - 1
        
    print(f"Load complete. Loaded {num_configs} configs.")
    
    #List the IDs for each specific config
    list_configs(loaded_configs)
    
    print("\nAwaiting connection")
    
    #Hold in loop until bit value assigned
    while vr_bits.bit == 0:
        await asyncio.sleep(1.0)
        
    #Make a new object with specific configs.
    vr_bits = config_bits(vr_bits, loaded_configs[vr_bits.bit])
    
    while True: #Program Async Main
        if vr_bits.active is True:
            
            if vr_bits.change > 0 and vr_bits.is_close == True:
                vr_bits.line_check()
                vr_bits.arousal, vr_bits.last_touch = stroking(vr_bits.arousal, vr_bits.change)
                vr_bits.change = 0
            if vr_bits.arousal > 0.001 and vr_bits.arousal < 1.0 and timeout(vr_bits.last_touch, 45):
                vr_bits.flagging()
            elif vr_bits.arousal > 1 and timeout(vr_bits.last_touch, 90):
                vr_bits.flagging()
            if vr_bits.pre is True:
                vr_bits.send_message(vr_bits.get_message("pre"), True)
                vr_bits.send_message(vr_bits.get_message("throb"), True)
            elif vr_bits.pre is False:
                vr_bits.send_message(vr_bits.get_message("pre"), False)
                vr_bits.send_message(vr_bits.get_message("throb"), False)
            if vr_bits.sps is True:
                vr_bits.send_message(vr_bits.get_message("sps"), True)
            elif vr_bits.sps is False:
                vr_bits.send_message(vr_bits.get_message("sps"), False)
                
            vr_bits.send_arousal()
        
        #Watch for bit value change (avatar change generally)
        if vr_bits.changed == True:
            
            if vr_bits.bit == 0:
                redraw_ui()
                list_configs(loaded_configs)
                
            else:
                #Make a new class with updated messaging
                vr_bits = config_bits(vr_bits, loaded_configs[vr_bits.bit])
            
        await asyncio.sleep(0.2) #Sleep to allow OSC to listen for updates
        
#Main OSC Async loop - Listens in between main loop runs
#Create the dispatcher for OSC messages and hand it off to the async loop
async def main(): 
    dispatcher = Dispatcher()

    #Whether the config file exists or not, look for the file to try and read the server config
    try:
        filepath = ""
        global serverIp
        global serverPort
        global vrcIp
        global vrcPort
        
        if os.name == 'nt':
            filepath = os.path.join(Path.home(), 'AppData\\Roaming\\JadeTech\\ASConfig.cfg')
        else:
            filepath = os.path.join(Path.home(), 'Documents/JadeTech/ASConfig.cfg')
        with open(filepath) as f:
            for line in f:
                x = line.rstrip("\n")
                if "serverIp" in line:
                    x = x.split("= ")
                    serverIp = x[1]
                if "serverPort" in line:
                    x = x.split("= ")
                    serverPort = int(x[1])
                if "vrcIp" in line:
                    x = x.split("= ")
                    vrcIp = x[1]
                if "vrcPort" in line:
                    x = x.split("= ")
                    vrcPort = int(x[1])
        f.close()
    except OSError as e:
        if debug is True:
            print(e)
            print("We tried, no file exists or something went wrong")

    server = AsyncIOOSCUDPServer((serverIp, serverPort), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()
    redraw_ui()
    
    await arousalloop(dispatcher) #start main loop
    
asyncio.run(main())

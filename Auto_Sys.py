import argparse
import time
import asyncio
import math
import os
from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
from pythonosc.osc_server import AsyncIOOSCUDPServer
from typing import List, Any
from pathlib import Path
from Resources.as_config import AS_Config, AS_Object
from Resources.constants import DEBUG, callback, VERSION

from Resources.loadfile import load_configs, check_for_config, list_configs
from Resources.ui import redraw_ui


#OSC Server and client details
serverIp = "127.0.0.1"
serverPort = 9010

vrcIp = "127.0.0.1"
vrcPort = 9000

line_limit = 25
version = VERSION
filepath = ""

#Global functions

#Increases the value only when there is a detected change
def stroking(arousal, change) -> float:
    if change != 0 and arousal < 2: #increase the amount if the change is greater
        if change == 2:
            arousal += 0.025
        elif change == 3:
            arousal += 0.005
        else:
            arousal += 0.02
    elif arousal > 2:
        arousal = 2

    print(f"arousal up {arousal}")
    return arousal, time.time()
        
#Touch timeout for flagging function
def timeout(last_touch: float, timeout: float) -> bool:
    end_time = last_touch + timeout
    if time.time() > end_time:
        return True
    return False
    
#Configuration for each specific set of bits.
def config_bits(bits_select, config) -> object:
    
    if DEBUG is True:
        print(config)
    
    name = config['name']
    arousal_messages = config['arousal_parameters']
    multi_message = config['split_arousal']
    try:
        decay = config['arousal_decay']
    except:
        decay = 0.001
    try:
        base_gain = config['base_arousal_increase']
    except:
        base_gain = 0.2
    try:
        timeout = config['touch_timeout']
    except:
        timeout = 45



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
    
    if DEBUG is True:
        print(f"Arousal messages: {arousal_messages}")
    
    new_bits = AS_Config(
        name, 
        bits_select.dispatcher, 
        arousal_messages, 
        split_param_start, 
        multi_message,
        vrcIp=vrcIp,
        vrcPort=vrcPort,
        base_arousal_increase=base_gain, 
        arousal_decay=decay, 
        arousal_timeout=timeout,
        )
    
    new_bits.add_parameter("pre", config['pre'])
    new_bits.add_parameter("sps", config['sps'])
    new_bits.add_parameter("aroused", config['aroused'])
    new_bits.add_parameter("erect", config['erect'])
    new_bits.add_parameter("throb", config['throb'])
    
    for item in config:
        if "/avatar/parameters/" in item:
            if DEBUG is True:
                print(f"{item} : {config[item]}")

            msg_list = item.split("/")
            name = msg_list[-1]

            new_touch = None

            if name not in new_bits.zone_dict:
                new_bits.zone_dict[name] = new_touch

            else:
                new_touch = new_bits.zone_dict[name]
            msg_end = len(item) - len(name)
            preamble = item[0:msg_end]

            new_touch = AS_Object(name, new_bits.dispatcher, None, preamble)
            match config[item]:
                case callback.VELOCITY.value: #Default plug setup
                    new_touch.type = "Plug"
                    new_touch.dispatch_add(f"{item}/TouchOthers", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/TouchSelf", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/FrotOthers", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenOthers", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenSelf", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/TouchSelfClose", callback.IS_CLOSE)
                    new_touch.dispatch_add(f"{item}/TouchOthersClose", callback.IS_CLOSE)
                    new_touch.dispatch_add(f"{item}/FrotOthersClose", callback.IS_CLOSE)
                    new_touch.dispatch_add(f"{item}/PenOthersClose", callback.IS_CLOSE)
                case callback.TOUCH.value: #For now, touch zones are always on
                    new_touch.type = "Touchzone"
                    new_touch.dispatch_add(f"{item}/Others", callback.HOLE)
                    new_touch.dispatch_add(f"{item}/Self", callback.HOLE)
                    #new_touch.set_is_close()
                case callback.HOLE.value: #Default socket setup
                    new_touch.type = "Hole"
                    new_touch.dispatch_add(f"{item}/PenOthersNewRoot", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenOthersNewTip", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenOthers", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenSelfNewRoot", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenSelfNewTip", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/TouchOthers", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/TouchSelf", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/FrotOthers", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/TouchSelfClose", callback.IS_CLOSE)
                    new_touch.dispatch_add(f"{item}/TouchOthersClose", callback.IS_CLOSE)
                    new_touch.dispatch_add(f"{item}/FrotOthersClose", callback.IS_CLOSE)
                    new_touch.dispatch_add(f"{item}/PenOthersClose", callback.IS_CLOSE)
                case callback.RING.value: #For now, rings are always on
                    new_touch.type = "Ring"
                    new_touch.dispatch_add(f"{item}/PenOthersNewRoot", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenOthersNewTip", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenSelfNewRoot", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/PenSelfNewTip", callback.VELOCITY)
                    #new_touch.set_is_close()

            #print(new_touch)

            new_bits.zone_dict[name] = new_touch

    new_bits.bit = bits_select.bit
    new_bits.active = bits_select.active
    new_bits.changed = False

    bits_select.clear_mapping()
    bits_select = None
    return new_bits

def first_load() -> dict:
    #Check and see if the config exists. If not, make a new one. If it does, return the file and continue
    result = False
    try:
        result = check_for_config()
    except OSError as e:
        print(e)
    if result is False:
        print("Unable to create or load config file. Exiting.")
        input("Press enter to continue...")
        return None
    if result is True:
        #If no previous config existed, a file was created, and the user needs to add their config to the file
        print("Please add your config using the template provided and restart this program")
        input("Press enter to continue...")
        return None
    #Try to load all configs from the file. There should always be a 0 config, making every further config 1 based
    loaded_configs = {}
    try:
        loaded_configs = load_configs(result)
    except OSError as e:
        print(e)
        print("Failed to get configs from file")
        input("Press enter to continue...")
        return None
    num_configs = len(loaded_configs)

    if loaded_configs[0]["name"] == "template" and num_configs == 1:
        print("No configs loaded. Please update the config file")
        
        input("Press enter to continue...")
        return None
    else:
        num_configs = num_configs - 1
        
    print(f"Load complete. Loaded {num_configs} configs.")
    
    #List the IDs for each specific config
    list_configs(loaded_configs)
    
    print("\nAwaiting connection")

    return loaded_configs

def change_arousal(zone: AS_Object, base_arousal_gain: float):
    #if zone.is_touched():
    return float(base_arousal_gain) * float(zone.get_arousal_val())


#Main async loop
async def arousalloop(dispatcher):
    
    #Make a default class to track the change of bit state
    vr_bits = AS_Config("None", dispatcher)
    start_time = time.time()

    loaded_configs = first_load()

    if loaded_configs is None:
        return 1
    
    #Hold in loop until bit value assigned
    while vr_bits.bit == 0:
        await asyncio.sleep(1.0)
        
    #Make a new object with specific configs.
    vr_bits = config_bits(vr_bits, loaded_configs[vr_bits.bit])

    #HERE FOR DEBUG ONLY
    #vr_bits.is_close = True
    
    while True: #Program Async Main
        if vr_bits.active is True and vr_bits.changed is False:

            #For each defined plug/socket/touchzone check its delta change and return its multiplier
            # Tested with time smoothing and the await seems to be good enough for smooth changes
            for zone in vr_bits.zone_dict:
                zone_obj = vr_bits.zone_dict[zone]
                if zone_obj.is_touched() and (zone_obj.type != "Ring" or zone_obj.type != "Touchzone"):
                    vr_bits.arousal += change_arousal(zone_obj, vr_bits.arousal_increase)
                    vr_bits.last_touch = time.time()
                elif zone_obj.type == "Ring" or zone_obj.type == "Touchzone":
                    change = change_arousal(zone_obj, vr_bits.arousal_increase)
                    if change > 0.0005:
                        vr_bits.arousal += change
                        vr_bits.last_touch = time.time()
                #If not touched, remove stale values (to better track the change since last check)
                if zone_obj.get_pos_list_len() > 0:
                    zone_obj.decay_pos_list()
            
            if vr_bits.arousal > 1.5 and vr_bits.pre is False: #enable dripping after a certain threshold
                vr_bits.pre = True
            if vr_bits.arousal > 1.5 and vr_bits.throb is False: #enable dripping after a certain threshold
                vr_bits.throb = True
            if vr_bits.arousal > 0.8 and vr_bits.sps is False:
                vr_bits.sps = True
            if vr_bits.arousal > 0.001 and vr_bits.arousal < 1.0 and timeout(float(vr_bits.last_touch), float(vr_bits.timeout)) and time.time() > start_time + 0.1:
                vr_bits.flagging()
                start_time = time.time()
            elif vr_bits.arousal > 1 and timeout(float(vr_bits.last_touch), float(vr_bits.timeout) * 2) and time.time() > start_time + 0.1:
                vr_bits.flagging()
                start_time = time.time()
                
            vr_bits.send_arousal()
        
        #Watch for bit value change (avatar change generally)
        if vr_bits.changed is True:
            
            redraw_ui(version, serverIp, serverPort)
            list_configs(loaded_configs)

            while vr_bits.bit == 0:
                await asyncio.sleep(1)
            
            #Make a new class with updated messaging
            vr_bits = config_bits(vr_bits, loaded_configs[vr_bits.bit])
            
        await asyncio.sleep(0.05) #Sleep to allow OSC to listen for updates
        
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
        if DEBUG is True:
            print(e)
            print("We tried, no file exists or something went wrong")

    server = AsyncIOOSCUDPServer((serverIp, serverPort), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()
    redraw_ui(version, serverIp, serverPort)
    
    await arousalloop(dispatcher) #start main loop


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Exiting...")
    raise SystemExit(0)

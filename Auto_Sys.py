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

from Resources.loadfile import load_config, check_for_config, list_configs
from Resources.ui import redraw_ui
from Resources.config_tool import config_tool

#from pythonoscquery.shared.osc_address_space import OSCAddressSpace
#from pythonoscquery.shared.osc_path_node import OSCPathNode
#from pythonoscquery.shared.osc_access import OSCAccess


#OSC Server and client details
serverIp = "127.0.0.1"
serverPort = 9010

vrcIp = "127.0.0.1"
vrcPort = 9000

line_limit = 25
version = VERSION
filepath = ""

#Global functions

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
        tmp = config['touch_timeout']
        timeout = tmp.split(",")
        timeout[0] = timeout[0].strip()
        timeout[1] = timeout[1].strip()
    except:
        timeout = 45



    multi_message = ("true" in multi_message.lower())
        
    split_param_start = float(config['split_param_start'])
    if "," in arousal_messages:
        tmp = []
        for msg in arousal_messages.split(","):
            tmp.append(msg.strip())
        arousal_messages = float(tmp)
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
    try:
        new_bits.pre[0] = float(config['pre_start'])
    except:
        new_bits.pre[0] = 1.5
    try:
        new_bits.throb[0] = float(config['throb_start'])
    except:
        new_bits.throb[0] = 1.5
    try:
        new_bits.sps[0] = float(config['sps_start'])
    except:
        new_bits.sps[0] = 0.8

    i = 0 #int for plug id association to enable per-zone toggling
    
    print("Toggle zones in the Toggles menu with the following IDs:")
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

            new_touch = AS_Object(name, new_bits.dispatcher, None, preamble, i)
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
                    new_touch.dispatch_add(f"{item}/Others", callback.VELOCITY)
                    new_touch.dispatch_add(f"{item}/Self", callback.VELOCITY)
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
            print(f"Added {new_touch.name} as {new_touch.type} with toggle ID: {i}")
            new_touch.dispatch_add(f"/avatar/parameters/arousalsys/toggle/{i}", 99) #Add the toggle listener

            new_bits.zone_dict[name] = new_touch
            i += 1

    new_bits.id = bits_select.id
    new_bits.active = bits_select.active
    new_bits.changed = False

    for item in bits_select.zone_dict:
        bits_select.zone_dict[item].clear_mapping()
        bits_select.zone_dict[item] = None
    bits_select.clear_mapping()
    del bits_select
    return new_bits

def first_load() -> bool:
    
    #Check and see if any configs exist, if not, return false and wait for a new config to be created
    avail_configs = os.listdir(os.path.join(filepath, "Avatars"))

    if len(avail_configs) == 0:
        return False
    
    #List the IDs for each specific config
    list_configs(os.path.join(filepath, "Avatars"))
    
    print("\nAwaiting connection")

    return True

def change_arousal(zone: AS_Object, base_arousal_gain: float):
    return float(base_arousal_gain) * float(zone.get_arousal_val())


#Main async loop
async def arousalloop(dispatcher):
    
    #Make a default class to track the change of bit state
    vr_bits = AS_Config("None", dispatcher)
    start_time = time.time()

    first_load()
    
    #Hold in loop until bit value assigned
    
    while vr_bits.id == "":
        await asyncio.sleep(1.0)
        if config_tool(vr_bits.id) is False:
            vr_bits.id = ""

    #Make a new object with specific configs.
    av_config = None
    for config in os.listdir(os.path.join(filepath,"Avatars")):
        with open(config, "r") as file:
            if str(vr_bits.id) in file.readline():
                av_config = config
                break
    vr_bits = config_bits(vr_bits, load_config(av_config))
    
    while True: #Program Async Main
        if vr_bits.active is True and vr_bits.changed is False:

            #For each defined plug/socket/touchzone check its delta change and return its multiplier
            # Tested with time smoothing and the await seems to be good enough for smooth changes
            for zone in vr_bits.zone_dict:
                zone_obj = vr_bits.zone_dict[zone]
                if zone_obj.enabled is False: #If disabled by user, skip!
                    continue
                if zone_obj.is_touched() and (zone_obj.type != "Ring" or zone_obj.type != "Touchzone") and time.time() > start_time + 0.1:
                    vr_bits.arousal += change_arousal(zone_obj, vr_bits.arousal_increase)
                    vr_bits.last_touch = time.time()
                elif zone_obj.type == "Ring" or zone_obj.type == "Touchzone" and time.time() > start_time + 0.1:
                    change = change_arousal(zone_obj, vr_bits.arousal_increase)
                    if change > 0.0005:
                        vr_bits.arousal += change
                        vr_bits.last_touch = time.time()
                #If not touched, remove stale values (to better track the change since last check)
                if zone_obj.get_pos_list_len() > 0:
                    zone_obj.decay_pos_list()
            
            if vr_bits.arousal > vr_bits.pre[0] and vr_bits.pre[1] is False: #enable dripping after a certain threshold
                vr_bits.pre[1] = True
                vr_bits.send_message(vr_bits.get_message("pre"), True)
            if vr_bits.arousal > vr_bits.throb[0] and vr_bits.throb[1] is False: #enable throbbing after a certain threshold
                vr_bits.throb[1] = True
                vr_bits.send_message(vr_bits.get_message("throb"), True)
            if vr_bits.arousal > vr_bits.sps[0] and vr_bits.sps[1] is False:
                vr_bits.sps[1] = True
                vr_bits.send_message(vr_bits.get_message("sps"), True)
            if vr_bits.arousal > 0.001 and vr_bits.arousal < 1.0 and timeout(float(vr_bits.last_touch), float(vr_bits.timeout[0])) and time.time() > start_time + 0.1:
                vr_bits.flagging()
                start_time = time.time()
            elif vr_bits.arousal > 1 and timeout(float(vr_bits.last_touch), float(vr_bits.timeout[1]) * 2) and time.time() > start_time + 0.1:
                vr_bits.flagging()
                start_time = time.time()

            if vr_bits.arousal > 2.0:
                vr_bits.arousal = 2.0
                
            vr_bits.send_arousal()
        
        #Watch for bit value change (avatar change generally)
        if vr_bits.changed is True:
            
            redraw_ui(version, serverIp, serverPort)
            list_configs(os.path.join(filepath, "Avatars"))

            while vr_bits.id == "":
                await asyncio.sleep(1)
            
            #Make a new class with updated messaging if the file exists and has OSCGB messages
            if config_tool(vr_bits.id):
                av_config = None
                for config in os.listdir(os.path.join(filepath,"Avatars")):
                    with open(config, "r") as file:
                        if vr_bits.id in file.readline():
                            av_config = config
                            file.close
                            break
                vr_bits = config_bits(vr_bits, load_config(av_config))
            else: #No file exists or file would have no messages. Ignoring and looping until next change
                vr_bits.changed = False
                vr_bits = AS_Config("None", dispatcher)

            
        await asyncio.sleep(0.05) #Sleep to allow OSC to listen for updates
        
#Main OSC Async loop - Listens in between main loop runs
#Create the dispatcher for OSC messages and hand it off to the async loop
async def main(): 
    dispatcher = Dispatcher()

    global filepath
    if os.name == 'nt':
        filepath = os.path.join(Path.home(), 'AppData\\Roaming\\FerreTech')
    else:
        filepath = os.path.join(Path.home(), 'Documents/FerreTech')

    #Whether the config file exists or not, look for the file to try and read the server config
    try:
        global serverIp
        global serverPort
        global vrcIp
        global vrcPort
        
        check_for_config()

        with open(os.path.join(filepath, 'ASConfig.cfg')) as f:
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
except OSError as e:
    print(e)
    print("Exiting due to error. Press enter to continue...")
    input()
    raise SystemExit(1)
except KeyboardInterrupt:
    print("Exiting...")
    raise SystemExit(0)

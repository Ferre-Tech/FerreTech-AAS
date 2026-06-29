import argparse
import random
import time
import asyncio
import math
from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
from pythonosc.osc_server import AsyncIOOSCUDPServer
from typing import List, Any
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder


#Global Variables

serverIp = "127.0.0.1"
serverPort = 9010

vrcIp = "127.0.0.1"
vrcPort = 9000

currentPos = 0.0
lasttouch = 0.0
ballsTouched = 0.0
active = False
lastPos = 0.0
arousal = 0.01
bit = 2
pre = 0
sps = False
last_time = float("-inf")

#grabs the OSC float value of the reciever for depth
def velocity_callback(address: str, *args: List[Any]) -> None:
    #print(*args)
    global currentPos
    currentPos = round(args[0], 3) #round to 3 decimal places to avoid messy numbers

def activate_callback(address: str, activate) -> None:
    if activate:
        print("Arousal System activated")
    if activate is not True:
        print("Arousal System deactivated")
    
    global active
    active = activate

def jangledJewels_callback(address: str, x) -> None:
    #print(activate)
    global ballsTouched
    ballsTouched = x

def bit_select_callback(address: str, x) -> None:
    global bit
    bit = x

#increases the value only when there is a detected change
def stroking(arousal):
    global pre
    global sps
    global lastPos
    global currentPos
    global last_time
    
    change = lastPos - currentPos
    #print(change)
    if change == 0:
        return arousal
    elif change < 0: #ensure the value of change is always positive when comparing
        change = change * -1
    elif change > 0.01 and arousal < 2: #increase the amount if the change is greater
        if change > 0.15:
            arousal += 0.0075
        else:
            arousal += 0.005
        last_time = time.time()
    elif arousal > 2:
        arousal = 2
    if arousal > 1.5 and pre is False: #enable dripping after a certain threshold
        pre = True
    if arousal > 0.8 and sps is False:
        sps = True
    print(f"arousal up {arousal}")
    lastPos = currentPos
    #print (f"Lastpos: {lastPos}")
    return arousal

#reduces the value per tick after a supplied timeout
def flagging(timeout):
    global pre
    global sps
    global arousal
    
    #print(timeout)
    if time.time() > timeout: #after timeout since last touch start decreasing
        arousal -= 0.001
    
    if arousal < 0.001: #reset everything
        pre = False
        sps = False
        arousal = 0.001

def makeBundle():
    global arousal
    
    bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
    msg = osc_message_builder.OscMessageBuilder(address="/AAP_Arousal_Smoothed")
    msg.add_arg(arousal)
    bundle.add_content(msg.build())
        
class Bits:
    def __init__(self, name, message_preamble = "/avatar/parameters/"):
        self.name = name
        self.__parameters = {}
        self.message_preamble = message_preamble
    
    def add_parameter(self, param_key, param):
        self.__parameters[param_key] = param

    def get_message(self, parameter):
        return f"{self.message_preamble}{self.__parameters[parameter]}"
 
def config_bits (bits_select):
    match bits_select:
        case 0:
            raise Exception("No object supplied")
        case 1:
            fara_penis = Bits("Fara Penis")
            fara_penis.add_parameter("pre", "Fara_TW_Drip")
            fara_penis.add_parameter("sps", "ModPenis_T_SPS")
            fara_penis.add_parameter("aroused", "ModPenis_Arousal")
            fara_penis.add_parameter("erect", "ModPenis_Erect")
            fara_penis.add_parameter("throb", "ModPenis_Throb")
            
            return fara_penis
            
        case 2:
            keva_penis = Bits("Keva Feline")
            keva_penis.add_parameter("throb", "VF110_felinethrob")
            keva_penis.add_parameter("sps", "VF110_dicktps")
            keva_penis.add_parameter("aroused", "VF110_dickout")
            keva_penis.add_parameter("pre", "")
            keva_penis.add_parameter("erect", None)
            
            return keva_penis
            
        case 3:
            keva_canine_penis = Bits("Keva Canine")
            keva_canine_penis.add_parameter("throb", "VF118_DickThrob")
            keva_canine_penis.add_parameter("sps", "VF118_KnotSPS")
            keva_canine_penis.add_parameter("aroused", "VF118_DickOut")
            keva_canine_penis.add_parameter("pre", "")
            keva_canine_penis.add_parameter("erect", None)
            
            return keva_canine_penis

#main async loop
async def arousalloop():
    bit = 2
    client = udp_client.SimpleUDPClient(vrcIp, vrcPort)
    bit_obj = config_bits(bit)
    global arousal
    
    while True: #program Async Main
        if active is True:
            arousal = stroking(arousal)
            if ballsTouched > 0.05:
                arousal += 0.0075
            if arousal < 1 and arousal > 0.001:
                flagging((last_time + 30.0))
            elif arousal > 1:
                flagging((last_time + 90.0))
            if pre is True:
                client.send_message(bit_obj.get_message("pre"), True)
                client.send_message(bit_obj.get_message("throb"), True)
            elif pre is False:
                client.send_message(bit_obj.get_message("pre"), False)
                client.send_message(bit_obj.get_message("throb"), False)
            if sps is True:
                client.send_message(bit_obj.get_message("sps"), True)
            elif sps is False:
                client.send_message(bit_obj.get_message("sps"), False)
            #print(f"Arousal: {arousal}")
            client.send_message(bit_obj.get_message("aroused"), arousal)
            if bit_obj.get_message("erect") != None:
                client.send_message(bit_obj.get_message("erect"), arousal)
        await asyncio.sleep(0.1) #sleep to allow OSC to listen for updates
        
#Main OSC Async loop - Listens in between main loop runs
async def main(): 
    dispatcher = Dispatcher()

    #OSC Avatar parameters recieve mapping. Default route is /avatar/parameters/
    #dispatcher.map("/avatar/parameters/OGB/Orf/Sheathed_Touch/TouchOthers", velocity_callback)
    #dispatcher.map("/avatar/parameters/OGB/Orf/Sheathed_Touch/TouchSelf", velocity_callback)
    dispatcher.map("/avatar/parameters/OGB/Orf/*", velocity_callback)
    dispatcher.map("/avatar/parameters/OGB/Pen/CatDick/*", velocity_callback)
    dispatcher.map("/avatar/parameters/OGB/Pen/Knot/*", velocity_callback)
    #dispatcher.map("/avatar/parameters/ModPenis_T_ContactArousal", activate_callback)
    dispatcher.map("/avatar/parameters/arousalsys/activate", activate_callback)
    dispatcher.map("/avatar/parameters/VFH/Zone/Touch/Balls_Touched/*", jangledJewels_callback)
    dispatcher.map("/avatar/parameters/VFH/Zone/Touch/Sheathed_Touch/*", jangledJewels_callback)
    dispatcher.map("/avatar/parameters/VFH/Zone/Touch/Shaft Touch/*", jangledJewels_callback)
    dispatcher.map("/avatar/parameters/OGB/Pen/Shaft_Touch/*", jangledJewels_callback)
    dispatcher.map("/avatar/parameters/arousalsys/bit", bit_select_callback)

    server = AsyncIOOSCUDPServer((serverIp, serverPort), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()
    print(f"Listening on {serverIp, serverPort}")
    
    await arousalloop() #start main loop
    
asyncio.run(main())

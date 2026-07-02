import time
import math
from pythonosc import udp_client


#OSC Server and client details
vrcIp = "127.0.0.1"
vrcPort = 9010

preamble = "/avatar/parameters/"



def main():
        client = udp_client.SimpleUDPClient(vrcIp, vrcPort)
        print("Starting testing loop")
    
        print("Enable Arousal System")
        client.send_message(f"{preamble}arousalsys/activate",True)
        time.sleep(3)

        print("Change bit to 2")
        client.send_message(f"{preamble}arousalsys/bit",2)	
        time.sleep(3)
        print("Starting loop for 15 seconds of changing position data")
        run_time = time.time() + 15
        client.send_message(f"{preamble}OGB/Pen/CatDick/TouchSelfClose", True)
        while(time.time() < run_time):
                client.send_message(f"{preamble}OGB/Pen/CatDick/TouchSelf", 0.0)
                time.sleep(1)
                client.send_message(f"{preamble}OGB/Pen/CatDick/TouchSelf", 0.5)
                time.sleep(1)
                
        print("Loop complete.")

        time.sleep(2)

        print("Testing profile swap; Bit to 2")
        client.send_message(f"{preamble}arousalsys/bit",1)

main()

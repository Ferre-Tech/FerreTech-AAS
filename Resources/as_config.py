from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
from enum import Enum
from Resources.ui import print_to_ui, redraw_ui, clear_ui
from Resources.constants import callback, DEBUG

#Checks for a change in depth of 5% or more.
#Returns an int
def depth_changed(currentPos, lastPos) -> int:
    if currentPos >= (lastPos + (lastPos * 0.1)) or currentPos <= (lastPos - (lastPos * 0.1)):
        return 1
    elif currentPos >= (lastPos + (lastPos * 0.2)) or currentPos <= (lastPos - (lastPos * 0.2)):
        return 2
    return 0

def get_lowest_val(val_list: list, low_val: float):
    if val_list == []:
        return low_val
    val = val_list.pop()
    if val > low_val:
        get_lowest_val(val_list, low_val)
    elif val < low_val:
        get_lowest_val(val_list, val)
    get_lowest_val(val_list, low_val)

def get_highest_val(val_list: list, high_val: float):
    if val_list == []:
        return high_val
    val = val_list.pop()
    if val > high_val:
        get_highest_val(val_list, high_val)
    elif val < high_val:
        get_highest_val(val_list, val)
    get_highest_val(val_list, high_val)

#Class defines and holds most functions and OSC messaging in order to communicate with a connected VRC avatar as defined in a supplied config, selected via the class value *.bit
#Classes presently are built semi-immutable in order to maintain cleaner OSC messaging and to remove unecessary OSC listeners when a new one is made
class AS_Config:
    def __init__(self, 
                name: str, 
                dispatcher: Dispatcher, 
                arousal_messages: list = [], 
                split_param_start: float = 1.0, 
                split_arousal_vals: bool = False, 
                message_preamble: str = "/avatar/parameters/", 
                vrcIp: str = "127.0.0.1", 
                vrcPort: int = 9000,
                base_arousal_increase: float = 0.05,
                arousal_decay: float = 0.001,
                arousal_timeout: list = [45,90],
                ):
        self.name = name
        self.id = ""
        self.__parameters = {}
        self.__arousal_messages = arousal_messages
        self.__message_preamble = message_preamble
        self.active = False
        self.__start_val = split_param_start
        self.arousal = 0.0
        self.arousal_increase: float = float(base_arousal_increase)
        self.arousal_decay: float = float(arousal_decay)
        self.timeout:list = arousal_timeout
        self.pre: list = [1.5, False]
        self.sps: list = [0.8, False]
        self.throb: list = [1.5, False]
        self.last_touch = float("-inf")
        self.__map_dict: dict = {} #Holds OSC Message mappings for use with the server unmap function
        self.dispatcher: Dispatcher = dispatcher
        self.dispatch_init_config()
        self.__split_arousal_val = split_arousal_vals
        self._client = udp_client.SimpleUDPClient(vrcIp, vrcPort)
        self.change = 0
        self.changed = False
        self.is_close = False
        self.zone_dict: dict = {}
        self.min_val = 0

    def __repr__(self):
        return f"Bits({self.name=}, {self.dispatcher=}, {self.__map_dict=}"


    #Callbacks section for OSC Messaging and cleaning up handlers

    #Enable and disable the system
    def activate_callback(self, address: str, activate: bool) -> None:
        if activate:
            print_to_ui("Arousal System activated")
        if activate is not True:
            print_to_ui("Arousal System deactivated")
        self.active = activate
    
    #Bit config select callback
    def id_select_callback(self, address: str, x: str) -> None:
        self.id = x
        self.changed = True

    #Reset arousal and all toggles
    def reset_callback(self, address: str, x: bool) -> None:
        self.arousal = 0.0
        self.pre[1] = False
        self.throb[1] = False
        self.sps[1] = False
        self.send_message(self.get_message("pre"), False)
        self.send_message(self.get_message("sps"), False)
        self.send_message(self.get_message("throb"), False)

    #Minimum arousal value
    def set_min_val(self, address: str, x: float) -> None:
        self.min_val = x
        if (self.arousal < self.min_val):
            self.arousal = self.min_val

    #Add dispatcher OSC message mapping
    def dispatch_add(self, oscmsg: str, callback_id: int):
        if DEBUG is True:
            print(f"{oscmsg}:{callback_id}")
        if callback_id == 0:
            raise Exception("No valid callback supplied")
        
        print_to_ui(f"Adding OSC listener for {oscmsg}")
        self.__map_dict[oscmsg] = self.dispatcher.map(oscmsg, self.get_handler(callback_id))
    
    #Default callbacks all configs will use
    def dispatch_init_config(self):
        self.dispatch_add("/avatar/parameters/arousalsys/activate", callback.ACTIVATE)
        self.dispatch_add("/avatar/change", callback.ID)
        self.dispatch_add("/avatar/parameters/arousalsys/reset", 98)
        self.dispatch_add("/avatar/parameters/arousalsys/min_val", 99)
        clear_ui()

    #OSC Helper functions

    #Because OSC handlers aren't hashable, make a get for each for use within unmap function
    def get_handler(self, handler_id:int):
        match handler_id:
            case callback.ACTIVATE:
                return self.activate_callback
            case callback.ID:
                return self.id_select_callback
            case 98:
                return self.reset_callback
            case 99:
                return self.set_min_val
            case _:
                raise Exception("No valid handler ID supplied")
    
    def clear_mapping(self):
        #Clears all mappings on the dispatcher for this object. Handlers are associated in __map_dict
        for mapping in self.__map_dict:
            try:
                self.dispatcher.unmap(mapping, self.__map_dict[mapping])
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.__map_dict[mapping]}")
    
    def add_parameter(self, param_key: int, param: str):
        self.__parameters[param_key] = param

    def get_message(self, parameter: str):
        if DEBUG is True:
            print(f"Param: {parameter}, {self.__message_preamble}{self.__parameters[parameter]}")
        return f"{self.__message_preamble}{self.__parameters[parameter]}"

    def flagging(self):
        if self.arousal > 0.005:
            self.arousal -= self.arousal_decay
        
        if self.arousal < 1.5 and self.pre[1] is True:
            self.pre[1] = False
            self.send_message(self.get_message("pre"), False)
        if self.arousal < 1.5 and self.throb[1] is True:
            self.throb[1] = False
            self.send_message(self.get_message("throb"), False)
        if self.arousal < 0.8 and self.sps[1] is True:
            self.sps[1] = False
            self.send_message(self.get_message("sps"), False)

        if self.arousal < 0.005 and self.arousal >= 0.0: #reset everything
            self.pre[1] = False
            self.throb[1] = False
            self.sps[1] = False
            self.arousal = 0.0
            redraw_ui()

    def send_message(self, msg: str, val: any):
        self._client.send_message(msg, val)

    def send_arousal(self):
        arsl = self.arousal
        if arsl > 1.0: #To prevent value overrun on some menus, just set the value to 1 and use it for some messages
            arsl = 1.0
        if self.__split_arousal_val is True:
            if DEBUG is True:
                print(f"{self.get_message(self.__arousal_messages[0])}, {self.arousal}")
            if self.arousal < self.__start_val:
                self.send_message(self.get_message(self.__arousal_messages[0]), arsl)
            elif self.arousal > self.__start_val:
                self.send_message(self.get_message(self.__arousal_messages[0]), arsl)
                sec_val = float(self.arousal) - float(self.__start_val)
                self.send_message(self.get_message(self.__arousal_messages[1]), sec_val)
        else:
            for message in self.__arousal_messages:
                self.send_message(self.get_message(message), arsl)

#Object to hold each Touch zone, plug, or socket defined in the config file
class AS_Object():
    def __init__(self, name: str, dispatcher: Dispatcher, message_preamble: str, type: callback = None, multiplier = 0.1, id = -1):
        self.enabled: bool = True
        self.id: int = int(id)
        self.name: str = name
        self.type: str = type
        self.last_pos: float = float("-inf")
        self.__is_close: bool = False
        self.__pos_list: list = []
        self.dispatcher: Dispatcher = dispatcher
        self.multiplier: float = multiplier
        self.__map_dict: dict = {}
        self.__message_preamble: str = message_preamble

    def __repr__(self):
        return f"{self.name}: {self.type=}, {self.dispatcher=}, {self.__map_dict=}, {self.__is_close=}"
    
    #Filters for all messages from OSCGB relevant to this specific SPS component. Further filtering and handling will be done from object functions per response
    def filter_callback(self, address: str, *args: any) -> None:
        if len(args) < 1:
            return
        
        if f"{self.__message_preamble}{self.name}/" not in address:
            return
        
        if "Close" in address and args[0] is not type(bool):
            self.__is_close = args[0]

        elif ("TouchSelf" in address or 
            "TouchOthers" in address or
            "PenOthers" in address or
            "PenSelf" in address or
            "PenOthersNewRoot" in address or
            "PenOthersNewTip" in address or
            "FrotOthers" in address
            ) and (
            self.__is_close is True and
            args[0] is type(float)  
            ):
            current_pos = round(args[0], 3)
            if current_pos is not self.last_pos:
                self.__pos_list.append(current_pos)
            if len(self.__pos_list) > 25:
                self.__pos_list.pop(0)

        elif ("Others" in address or 
            "Self" in address or
            "PenSelfNewRoot" in address or
            "PenSelfNewTip" in address
            ):
            current_pos = round(args[0], 3)
            if current_pos is not self.last_pos:
                self.__pos_list.append(current_pos)
            if len(self.__pos_list) > 25:
                self.__pos_list.pop(0)
        print(end="")
        return

    #Allows enabling and disabling specific SPS items via some extra setup in the avatar menu
    def toggle_callback(self, address:str, x:bool) -> None:
        self.enabled = x
        if x is True:
            print_to_ui(f"Enabled {self.name}")
        else:
            print_to_ui(f"Disabled {self.name}")

    def get_handler(self, handler_id: callback):
        match handler_id:
            case 15:
                return self.filter_callback
            case 99:
                return self.toggle_callback
            case _:
                raise Exception("No valid handler ID supplied")

    #returns the delta change between the largest change in the list
    def __get_delta_vel(self) -> float:
        if self.__pos_list == []:
            return 0.0
        
        val_list = self.__pos_list.copy()
        val_list.sort(reverse=True)
        high_val = val_list[0]
        low_val = val_list[-1]
        delta = high_val - low_val
        self.__pos_list = [self.__pos_list.pop()]
        return round(delta, 3)
    
    def get_arousal_val(self) -> float:
        return self.__get_delta_vel() * self.multiplier
    
    def is_touched(self) -> bool:
        return self.__is_close
    
    def clear_mapping(self):
        #Clears all mappings on the dispatcher for this object. Handlers are associated in __map_dict
        for mapping in self.__map_dict:
            try:
                self.dispatcher.unmap(mapping, self.__map_dict[mapping])
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.__map_dict[mapping]}")

    #Add dispatcher OSC message mapping
    def dispatch_add(self, oscmsg: str, callback_id: int):
        if DEBUG is True:
            print(f"{oscmsg}:{callback_id}")
        if callback_id == 0:
            raise Exception("No valid callback supplied")

        if DEBUG is True:
            print(f"Adding OSC listener for {oscmsg}")
        self.__map_dict[oscmsg] = self.dispatcher.map(oscmsg, self.get_handler(callback_id))

    def get_pos_list_len(self) -> int:
        return len(self.__pos_list)
    
    def decay_pos_list(self) -> None:
        self.__pos_list.pop()

    def set_is_close(self) -> None:
        self.__is_close = True
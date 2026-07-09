from pythonosc.dispatcher import Dispatcher
from pythonosc import udp_client
from enum import Enum
from Resources.ui import line_check
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
        self.timeout:list = [arousal_timeout]
        self.pre: list = [1.5, False]
        self.sps: list = [0.8, False]
        self.throb: list = [1.5, False]
        self.last_touch = float("-inf")
        self.__map_list = [] #Holds OSC Message mappings for use with the server unmap function
        self.dispatcher = dispatcher
        self.dispatch_init_config()
        self.__split_arousal_val = split_arousal_vals
        self._client = udp_client.SimpleUDPClient(vrcIp, vrcPort)
        self.change = 0
        self.changed = False
        self.is_close = False
        self.__ui_lines = 0
        self.zone_dict: dict = {}

    def __repr__(self):
        return f"Bits({self.name=}, {self.dispatcher=}, {self.__map_list=}"


    #Callbacks section for OSC Messaging and cleaning up handlers
    
    #Checks for the close bool from OSCGB
    def is_close_callback(self, address: str, is_close: bool) -> None:
        #Must override
        pass
    
    #Grabs the OSC float value of the reciever for depth
    def velocity_callback(self, address: str, depth: float) -> None:
        #Must override
        pass

    #Enable and disable the system
    def activate_callback(self, address: str, activate: bool) -> None:
        line_check(self.__ui_lines)
        if activate:
            print("Arousal System activated")
        if activate is not True:
            print("Arousal System deactivated")
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


    #Add dispatcher OSC message mapping
    def dispatch_add(self, oscmsg: str, callback_id: int):
        if DEBUG is True:
            print(f"{oscmsg}:{callback_id}")
        if callback_id == 0:
            raise Exception("No valid callback supplied")
        #line_check(self.__ui_lines)
        print(f"Adding OSC listener for {oscmsg}")
        self.__map_list.append(oscmsg)
        self.dispatcher.map(oscmsg, self.get_handler(callback_id))
    
    #Default callbacks all configs will use
    def dispatch_init_config(self):
        self.dispatcher.map("/avatar/parameters/arousalsys/activate", self.get_handler(callback.ACTIVATE))
        self.dispatcher.map("/avatar/change", self.get_handler(callback.ID))
        self.dispatcher.map("/avatar/parameters/arousalsys/reset", self.get_handler(98))
        self.__map_list.append("/avatar/parameters/arousalsys/activate")
        self.__map_list.append("/avatar/change")
        self.__map_list.append("/avatar/parameters/arousalsys/reset")

    #OSC Helper functions

    #Because OSC handlers aren't hashable, make a get for each for use within unmap function
    def get_handler(self, handler_id: int):
        match handler_id:
            case callback.ACTIVATE:
                return self.activate_callback
            case callback.ID:
                return self.id_select_callback
            case 98:
                return self.reset_callback
            case _:
                raise Exception("No valid handler ID supplied")
    
    def clear_mapping(self):
        #Since no nice methods exist for handling specific dynamic handler unmapping, do them all and only throw errors if DEBUG is enabled
        for mapping in self.__map_list:
            try:
                self.dispatcher.unmap(mapping, self.get_handler(callback.ACTIVATE))
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(callback.ACTIVATE)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(callback.ID))
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(callback.ID)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(98))
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(98)}")
    
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

    def send_message(self, msg: str, val: any):
        self._client.send_message(msg, val)

    def send_arousal(self):
        arsl = self.arousal
        if arsl > 1.0: #To prevent value overrun on some menus, just set the value to 1 and use it for some messages
            arsl = 1.0
        if self.__split_arousal_val is True:
            if DEBUG is True:
                print(f"{self.get_message(self.arousal_messages[0])}, {self.arousal}")
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
class AS_Object(AS_Config):
    def __init__(self, name: str, dispatcher: Dispatcher, message_preamble: str, type: callback = None, multiplier = 0.1, id = -1):
        self.enabled = True
        self.id = int(id)
        self.name = name
        self.type = type
        self.last_pos = float("-inf")
        self.__is_close = False
        self.__pos_list = []
        self.dispatcher = dispatcher
        self.multiplier = multiplier
        self.__map_list = []
        self.__message_preamble = message_preamble

    def __repr__(self):
        return f"{self.name}: {self.type=}, {self.dispatcher=}, {self.__map_list=}, {self.__is_close=}"

    def is_close_callback(self, address: str, is_close: bool) -> None:
        self.__is_close = is_close
        print(end="")
    
    #Creates a list of position changes. Will average the output over a delta time
    def velocity_callback(self, address:str , depth: float) -> None:
        current_pos = round(depth, 3)
        if current_pos is not self.last_pos:
            self.__pos_list.append(depth)
            if len(self.__pos_list) > 25:
                self.__pos_list.pop(0)
        print(end="")

    #Allows enabling and disabling specific SPS items via some extra setup in the avatar menu
    def toggle_callback(self, address:str, x:bool) -> None:
        self.enabled = x

    def get_handler(self, handler_id: callback):
        match handler_id:
            case callback.VELOCITY:
                return self.velocity_callback
            case callback.ACTIVATE:
                return self.activate_callback
            case callback.TOUCH:
                return self.velocity_callback
            case callback.IS_CLOSE:
                return self.is_close_callback
            case callback.HOLE:
                return self.velocity_callback
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
        #Since no nice methods exist for handling specific dynamic OSC handler unmapping, do them all and only throw errors if DEBUG is enabled
        for mapping in self.__map_list:
            try:
                self.dispatcher.unmap(mapping, self.get_handler(callback.VELOCITY))
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(callback.VELOCITY)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(callback.ACTIVATE))
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(callback.ACTIVATE)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(callback.TOUCH))
            except ValueError:
                if DEBUG == True:
                    print(f"No mapping found for {mapping}, {self.get_handler(callback.TOUCH)}")
            try:
                self.dispatcher.unmap(mapping, self.get_handler(callback.IS_CLOSE))
            except ValueError:
                if DEBUG is True:
                    print(f"No mapping found for {mapping}, {self.get_handler(callback.IS_CLOSE)}")
            try:
                self.dispatcher.unmap(f"/avatar/parameters/arousalsys/toggle/{self.id}", self.get_handler(99))
            except ValueError:
                if DEBUG is True:
                    print(f"No mapping found for /avatar/parameters/arousalsys/toggle/{self.id}, {self.get_handler(99)}")

    #Add dispatcher OSC message mapping
    def dispatch_add(self, oscmsg: str, callback_id: int):
        if DEBUG is True:
            print(f"{oscmsg}:{callback_id}")
        if callback_id == 0:
            raise Exception("No valid callback supplied")
        #line_check(self.__ui_lines)
        if DEBUG is True:
            print(f"Adding OSC listener for {oscmsg}")
        self.__map_list.append(oscmsg)
        self.dispatcher.map(oscmsg, self.get_handler(callback_id))

    def get_pos_list_len(self) -> int:
        return len(self.__pos_list)
    
    def decay_pos_list(self) -> None:
        self.__pos_list.pop()

    def set_is_close(self) -> None:
        self.__is_close = True
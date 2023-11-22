# from Button import *
# from common import CacheHelper, inference
from edgeplusv2_config.common_utils import CacheHelper
from .plc_module import PLC,Button

class Conveyor:
    redis_obj = CacheHelper()

    def __init__(self, configuration):
        '''
        
        Description:
        Creates connection to conveyor and it's button. Gets trigger from conveyor and write output to it.

        Input:
        configuration - Dictionary containing the configuration of the conveyor
        
        '''
        self.configuration = configuration
        self.input_dict = {}
        self.output_dict = {}
        self.plc_obj_dict = {}
        self.input_button = None
        self.output_button = None
        self.trigger = False
        self.valid_schema = True
        self.plc_connection_established = True
    
    def validate_schema(self):
        '''
        
        Description:
        Checks if the schema of the conveyor is as expected and if all keys are present.
        
        '''
        all_keys_present = True
        button_config_keys = ["ip", "register", "idle_value", "active_value"]

        self.input_dict = self.configuration["input"]
        self.output_dict = self.configuration["output"]

        for key in button_config_keys:
            if key not in list(self.input_dict ) or key not in list(self.output_dict):
                all_keys_present = False
        
        self.valid_schema = all_keys_present
    
    def connect_to_plc(self, ip, button_names):
        '''
        
        Description:
        Connects to the PLC using the PLC class.
        Creates a dictionary (plc_obj_dict) with button name (input/output) as the key and the object of PLC class as value.

        Input:
        ip - IP address of PLC.
        button_names - Name of button Ex: input, output
        
        '''
        plc_obj = PLC(ip)  
        for button_name in button_names:
            self.plc_connection_established = self.plc_connection_established and plc_obj.connection_established
            if self.plc_connection_established:
                self.plc_obj_dict[button_name] = plc_obj.plc

    def configure_conveyor(self):
        '''
        
        Description:
        Configures conveyor if schema is correct.
        Connects to the plc and then configures the buttons.        
        
        '''
        if self.valid_schema:
            
            if self.input_dict["ip"] == self.output_dict["ip"]:
                self.connect_to_plc(self.input_dict["ip"], ["input", "output"])
            else:
                self.connect_to_plc(self.input_dict["ip"], ["input"])
                self.connect_to_plc(self.output_dict["ip"], ["output"])  
            
            self.configure_buttons()
        else:
            print("Invalid schema for Conveyor") 
        
    def configure_buttons(self):
        '''
        
        Description:
        Connects to indiviual buttons using the Button class and sets the type of trigger.
        Uses the PLC object created earlier.        
        
        '''
            
        if self.plc_connection_established:
        
            self.input_button = Button(self.plc_obj_dict["input"], int(self.input_dict["register"]), int(self.input_dict["idle_value"]), int(self.input_dict["active_value"]))
            self.output_button = Button(self.plc_obj_dict["output"], int(self.output_dict["register"]), int(self.output_dict["idle_value"]), int(self.output_dict["active_value"]))  
            if ws_type=='conveyor':
                self.trigger="trigger_capture"
            else:    
                self.trigger = "start_data_capture_cycle"
        
    
    def check_plc_trigger(self):
        '''
        
        Description:
        Check the input button for trigger.
        Sets value in redis if trigger is received.     
        If PLC connection was not established then retries to establish connection.
        
        '''
        input_flag = False

        # while True:  
        # customize for stop_conveyor
        while not CacheHelper().get_json("is_stop_conveyor"):   
            if self.plc_connection_established:
                            
                    input = self.input_button.get_value()
                    # print('PLC INPUT----------->',input,input_flag)
                    # print(self.trigger)
                    if input == 1 and not input_flag:
                        print("Received trigger")
                        input_flag = True
                        Conveyor.redis_obj.set_json({self.trigger:True})
                        Conveyor.redis_obj.set_json({"callInspectionTrigger":True})
                        self.write_result_to_plc()

                    if input == 0 and input_flag:
                        input_flag = False
            else:
                self.configure_conveyor()

    
    def write_result_to_plc(self):
        '''

        Descripiton:
        Checks redis for result and writes value to PLC accordingly.        
        
        '''
        while True:
            # print("Waiting for result")
            is_accepted = Conveyor.redis_obj.get_json("isAccepted")

            if is_accepted is not None:
                Conveyor.redis_obj.set_json({"isAccepted":None})
                self.output_button.set_value(is_accepted)
                break


def conveyor_main(configuration=None,workstation_type="conveyor"):
    global ws_type
    ws_type = workstation_type
    print(ws_type)
    obj = Conveyor(configuration)
    obj.validate_schema()
    obj.configure_conveyor()
    obj.check_plc_trigger()

# configuration = {
#             "input": {
#                 "ip": "192.168.1.50",
#                 "register": "2",
#                 "idle_value": "0",
#                 "active_value": "1"
#             },
#             "output": {
#                 "ip": "192.168.1.50",
#                 "register": "23",
#                 "idle_value": "2",
#                 "active_value": "1"
#             }
#                 }
# conveyor_main( configuration

# )

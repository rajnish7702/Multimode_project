from operator_panel.common_utils import ModbusController


class PLC:
    plc = ModbusController()
    ip = "192.168.1.50"
    plc.connect(ip, mode="TCP")

    def __init__(self):
        # self.plc = plc_controller.ModbusController()
        # self.ip = "192.168.1.50"
        # self.plc.connect(self.ip,mode='TCP')
        ...

    # def check_connection(self):
    #     for i in range(10):
    #         status = self.plc.connect(self.ip,mode='TCP')
    #         if status:
    #             return True
    #         time.sleep(2)
    #     return False


class Button(PLC):
    def __init__(self, ip, address, idle_val=0, active_val=1):
        super().__init__()
        PLC.ip = ip
        self.address = address
        self.idle_value = idle_val
        self.active_value = active_val
        # if self.check_connection():
        #     self.status = self.get_status()
        # else:
        #     self.get_status = False

    def get_status(self):
        state = self.plc.read_holding_register(self.address)
        # shreyas how to check if we get wrong key value
        if state == self.idle_value:
            return self.idle_value
        else:
            return self.active_value

    def get_raw_status(self):
        s = self.plc.read_holding_register(self.address)
        return s

    def write_value(self, value):
        self.plc.write_holding_register(self.address, value)


# process_running = Button("192.168.1.50",24,0,1)
# sensor_trig = Button("192.168.1.50",2,0,1)
# emergency_button = Button("192.168.1.50",8,1,0)


# while True:
#     print(f"process_trigger: {process_running.get_status()}")
#     print(f"sensor_trigger: {sensor_trig.get_status()}")
#     print(f"emergency: {emergency_button.get_status()}")
#     time.sleep(0.1)

from . import plc_controller

class PLC():
    def __init__(self, ip):
        self.plc = plc_controller.ModbusController()
        self.ip = ip
        self.connection_established = self.plc.connect(self.ip,mode='TCP')

class Button():
    def __init__(self, plc, address, idle_val=0, active_val=1):
        self.plc_obj = plc
        self.address = address
        self.idle_value = idle_val
        self.active_value = active_val

    def get_value(self):
        state = self.plc_obj.read_holding_register(self.address)
        if state == self.idle_value:
            return self.idle_value
        else:
            return self.active_value

    def set_value(self, value):
        if value:
            self.plc_obj.write_holding_register(self.address, self.active_value)
        else:
            self.plc_obj.write_holding_register(self.address, self.idle_value)

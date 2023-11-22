from . import plc_controller

class robot_controller():
    def __init__(self,ip):
        self.robot = plc_controller.ModbusController()
        self.status = self.robot.connect(ip,mode='TCP')
        self.address = {}
        self.address['pos'] = 141
        self.address['exe'] = 142

    def get_pos(self):

        return self.robot.read_holding_register(self.address['pos']) or None

    
    def move_pos(self,pos):
        self.robot.write_holding_register(self.address['pos'],pos)
        self.robot.write_holding_register(self.address['exe'],1)
        while self.robot.read_holding_register(self.address['exe']) == 1:
            pass
        


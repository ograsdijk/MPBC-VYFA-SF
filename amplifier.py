import pyvisa
import logging
from enum import Enum
from rich.logging import RichHandler
from pyvisa.errors import VisaIOError
from attributes import Property, FloatProperty, BoolProperty, FlagProperty, \
                        IntProperty, FloatPropertyNGet

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

class Alarms(Enum):
    SHG_TEMPERATURE     = 0
    TEC_TEMPERATURE     = 1
    PUMP_BIAS           = 2
    LOSS_OF_OUTPUT      = 3
    CASE_TEMPERATURE    = 4

class Faults(Enum):
    SHG_TEMPERATURE     = 0
    TEC_TEMPERATURE     = 1
    LASER_DIODE_CURRENT = 2
    WATCHDOG_TIMEOUT    = 3
    CASE_TEMPERATURE    = 4

class LaserState(Enum):
    OFF                 = 0
    KEYLOCK             = 6
    INTERLOCK           = 7
    FAULT               = 8
    LOS                 = 9
    STARTUP             = 20
    MANUAL_TURNING_ON   = 31
    MANUAL_ON           = 41
    SEED_ON             = 43
    SEED_OK             = 44
    PREAMP_TURN_ON      = 45
    PREAMP_TURN_OFF     = 46
    PREAMP_ON           = 47
    PREAMP_OK           = 48
    BOOSTER_TURN_ON     = 50
    BOOSTER_TURN_OFF    = 51
    BOOSTER_ON          = 52
    BOOSTER_OK          = 53

class MPBAmplifier:

    model                   = Property('Model', 'MODEL')
    serial                  = Property('Serial', 'SN')
    enabled                 = BoolProperty(
                                            'Enable Emission', 
                                            'LDenable', 
                                            read_only = False
                                            )
    state                   = BoolProperty('State', 'STATE')
    laserstate              = IntProperty('Laser state', 'LASERSTATE')

    SHGTemperatureSetpoint  = FloatProperty(
                                            'SHG Temperature Setpoint', 
                                            'TECSETPT 4', 
                                            read_only = False
                                            )
    SeedCurrent             = FloatPropertyNGet('Seed Current', 'LDCURRENT 1')
    PreampCurrent           = FloatPropertyNGet('Preamp Current', 'LDCURRENT 2')
    BoosterCurrent          = FloatPropertyNGet(
                                                'Booster Current', 
                                                'LDCURRENT 3', 
                                                read_only = False
                                                )
    BoosterCurrentSetpoint  = FloatProperty(
                                            'Booster Current Setpoint', 
                                            'LDCur 3', 
                                            read_only = False
                                            )
    SHGTemperature          = FloatProperty('SHG Temperature', 'TECTEMP 4')

    SeedPower               = FloatPropertyNGet('Seed Power', 'POWER 1')
    OutputPower             = FloatPropertyNGet('Output Power', 'POWER 0')
    
    alarms                  = FlagProperty('Alarms', 'ALR')
    faults                  = FlagProperty('Faults', 'FLT')

    def __init__(self, COM, baud_rate = 9600):
        self.instr = None
        self.rm = pyvisa.ResourceManager()

        # translate com port to visa port
        if 'COM' in COM:
            COM = f"ASRL{COM.strip('COM')}::INSTR"

        if COM not in self.rm.list_resources():
            logging.error(f"No device on {COM}")
            return 

        self.instr = self.rm.open_resource(COM, baud_rate = baud_rate)
        self.instr.read_termination = '\r'
        self.instr.write_termination = '\r'

        model = self.model
        if not model or '2RU-VYFL' not in model:
            logging.error("No connection to MPB 2RU-VYFL")
            if model:
                logging.error(f"Return model string is {model}")
            self.instr = None


    def _query(self, command):
        if self.instr:
            try:
                return self.instr.query(command).strip('D >')
            except VisaIOError as e:
                logging.error(f"Query error on {self.instr.resource_name} {command} : {str(e)}")
                return None


    def _write(self, command):
        if self.instr:
            try:
                self.instr.write(command)
            except VisaIOError as e:
                logging.error(f"Write error on {self.instr.resource_name} {command} : {str(e)}")

    def _read(self):
        if self.instr:
            try:
                return self.instr.read()
            except VisaIOError as e:
                logging.error(f"Read error on {self.instr.resource_name} : {str(e)}")
                return None

    def EnterTestEvironment(self):
        logging.warning("Entering the test environment")
        logging.info(self._query("testeoa"))
        logging.info(self._read())
        logging.info(self._read())
        return

    def SaveAll(self):
        """Save settings to non-volatile memory
        """
        self._write("SAVEALL")
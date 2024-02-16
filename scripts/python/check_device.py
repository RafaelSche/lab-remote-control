import pyvisa
import sys


resource_manager = pyvisa.ResourceManager()
client = resource_manager.open_resource(sys.argv[1])

try:
    print(client.query('*IDN?'))
except Exception as e:
    print(type(e), e)
finally:
    client.close()

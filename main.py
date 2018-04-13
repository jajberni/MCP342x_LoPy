from machine import Pin, I2C
from MCP342x import MCP342x
import time

sensor_type = "None"

try:
    i2c = I2C(0, I2C.MASTER, pins=('P22', 'P21'))
    addr68_ch0 = MCP342x(i2c, 0x68, channel=0, resolution=18, gain=8,
                         scale_factor=1000.0)
    addr68_ch1 = MCP342x(i2c, 0x68, channel=1, resolution=18, gain=8,
                         scale_factor=1000.0)
    addr68_ch2 = MCP342x(i2c, 0x68, channel=2, resolution=18, gain=8,
                         scale_factor=1000.0)
    addr68_ch3 = MCP342x(i2c, 0x68, channel=3, resolution=18, gain=8,
                         scale_factor=1000.0)
    time.sleep(1)
    print('Ready to read ADC')
except Exception as error:
    print(error)
    pass

while True:
    adc_values = [-1.0, -1.0, -1.0, -1.0]
    try:
        adc_values[0] = addr68_ch0.convert_and_read()
        adc_values[1] = addr68_ch1.convert_and_read()
        adc_values[2] = addr68_ch2.convert_and_read()
        adc_values[3] = addr68_ch3.convert_and_read()

    except Exception as error:
        print(error)

    print("ADC:{ch0},{ch1},{ch2},{ch3}".format(
        sensor_type=sensor_type, ch0=adc_values[0], ch1=adc_values[1],
        ch2=adc_values[2], ch3=adc_values[3]))

    time.sleep(1.0)

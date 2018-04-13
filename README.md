# MCP342x_LoPy
MicroPython driver for the MCP342x ADC.

This is a python library for the MCP342x ADC designed to operate with
[PyCom](https://pycom.io/) boards. It is based on
[Steve Marple's MCP342x Python Library](https://github.com/stevemarple/python-MCP342x),
which depends on the SMBus python library.
This one doesn't depend on the SMBus library, since it uses native I2C communications.

The MCP342x communicates with the PyCom board using the I2C bus.
The default I2C address of the device is selectable in the range of 0x68 to 0x 0x49.

**Connecting the board**

The current board uses Grove connectors. Alternatively you can use normal jumper
cables and solder them to the breakout pins on the board.

The default connection is to the 3.3V, GND, SDA (white) to P22 and SCL (yellow) to P21.
Other pins can be assigned when defining the I2C bus in the main program.

The 4 channels of the MCP3424 are available with screw terminals.

**Testing the library**

Upload the `boot.py`, `main.py` and `lib/MCP342x.py` to your PyCom board.
The demo script will stream the measurements on the serial console at 1Hz.

# Functions

This library provides a class `MPC342x` with the functionality for reading each
channel in the ADC.


  * **Constructor**

  The constructor takes the i2c port and the bus address as arguments.
  It is possible to define the device model, the channel number, gain(1,2,4,8),
  resolution (12,14,16,18), scale_factor and offset.
  The default is one-shot mode, but it is possible to run in continuous mode.

  ```python
  i2c = I2C(0, I2C.MASTER, pins=('P22', 'P21'))

   addr68_ch0 = MCP342x(i2c, address=0x68,
     device='MCP3424',
     channel=0,
     gain=1,
     resolution=12,
     continuous_mode=False,
     scale_factor=1.0,
     offset=0.0)

   ```

  * **convert_and_read()**

  Measures on the channel with the current settings and returns the measurement.

#### TODO: complete documentation.

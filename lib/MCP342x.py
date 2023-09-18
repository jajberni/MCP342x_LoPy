"""
MicroPython driver for the mcp342x ADC.
Adapted to PyCom boards from stevemarple/python-MCP342x
https://github.com/stevemarple/python-MCP342x

"""
import time
import uasyncio as asyncio


__author__ = 'Jose A. Jimenez-Berni'
__version__ = '0.2.0'
__license__ = 'MIT'


class MCP342x(object):
    """
    Class to represent MCP342x ADC.
    """
    _gain_mask            = 0b00000011
    _resolution_mask      = 0b00001100
    _continuous_mode_mask = 0b00010000
    _channel_mask         = 0b01100000
    _not_ready_mask       = 0b10000000

    _gain_to_config = {1: 0b00,
                       2: 0b01,
                       4: 0b10,
                       8: 0b11}

    _resolution_to_config = {12: 0b0000,
                             14: 0b0100,
                             16: 0b1000,
                             18: 0b1100}

    _channel_to_config = {0: 0b00000000,
                          1: 0b00100000,
                          2: 0b01000000,
                          3: 0b01100000}

    _conversion_ms = {12: 5,    # 240 SPS (samples/sec)
                      14: 17,   # 60 SPS
                      16: 67,   # 15 SPS
                      18: 267}  # 3.75 SPS

    _resolution_to_lsb = {12: 1e-3,
                          14: 250e-6,
                          16: 62.5e-6,
                          18: 15.625e-6}

    @staticmethod
    def config_to_gain(config):
        return [g for g, c in MCP342x._gain_to_config.items() if c == config & MCP342x._gain_mask][0]

    @staticmethod
    def config_to_resolution(config):
        return [g for g, c in MCP342x._resolution_to_config.items() if c == config & MCP342x._resolution_mask][0]

    @staticmethod
    def config_to_lsb(config):
        return MCP342x._resolution_to_lsb[MCP342x.config_to_resolution(config)]

    @staticmethod
    def config_to_str(config, width = 8):
        n = config & 0x7f
        s = bin(n)[2:]
        bin_str = '0b' + ('0' * (width - len(s))) + s
        hex_str = hex(n)
        dec_str = str(n)
        return bin_str + ',' + hex_str + ',' + dec_str

    def __init__(
        self,
        i2c,
        address,
        device = 'MCP3424',
        channel = 0,
        gain = 1,
        resolution = 12,
        continuous_mode = False,  # True: continuous, False: one-shot; default to one-shot
        scale_factor = 1.0,
        offset = 0.0
    ):
        if device not in ('MCP3422', 'MCP3423', 'MCP3424',
                          'MCP3426', 'MCP3427', 'MCP3428'):
            raise Exception('Unknown device: ' + str(device))

        self.i2c = i2c
        self.address = address
        self.device = device
        self.scale_factor = scale_factor
        self.offset = offset

        self.config = 0
        self.sign_bit_mask = 0
        self.count_mask = 0
        self.bytes_to_read = 0
        self.cbuffer = bytearray(1)
        self.cbuffer[0] = 0x00

        self.set_channel(channel)
        self.set_gain(gain)
        self.set_resolution(resolution)
        self.set_mode(continuous_mode)

    def __repr__(self):
        return (type(self).__name__
                + ': device=' + self.device
                + ' addr=' + hex(self.get_address())
                + ' chnl=' + str(self.get_channel())
                + ' res=' + str(self.get_resolution())
                + ' gain=' + str(self.get_gain())
                + ' config:' + MCP342x.config_to_str(self.config)
               )

    def get_i2c(self):
        return self.i2c

    def get_address(self):
        return self.address

    def get_gain(self):
        return MCP342x.config_to_gain(self.config)

    def get_resolution(self):
        return MCP342x.config_to_resolution(self.config)

    def get_continuous_mode(self):
        return bool(self.config & MCP342x._continuous_mode_mask)

    def get_channel(self):
        return [g for g, c in MCP342x._channel_to_config.items() if c == self.config & MCP342x._channel_mask][0]

    def get_config(self):
        return self.config

    def get_scale_factor(self):
        return self.scale_factor

    def get_offset(self):
        return self.offset

    def set_address(self, address):
        self.address = address

    def set_gain(self, gain):
        if gain not in MCP342x._gain_to_config:
            raise Exception('Illegal gain')

        self.config &= (~MCP342x._gain_mask & 0x7f)
        self.config |= MCP342x._gain_to_config[gain]

    def set_resolution(self, resolution):
        if resolution not in MCP342x._resolution_to_config:
            raise Exception('Illegal resolution')
        elif resolution == 18 and \
                self.device not in ('MCP3422', 'MCP3423', 'MCP3424'):
            raise Exception('18 bit sampling not suuported by ' +
                            self.device)

        self.config &= (~MCP342x._resolution_mask & 0x7f)
        self.config |= MCP342x._resolution_to_config[resolution]
        self.sign_bit_mask = 1 << (resolution - 1)
        self.count_mask = self.sign_bit_mask - 1
        self.bytes_to_read = 4 if resolution == 18 else 3

    def set_mode(self, continuous_mode):
        if continuous_mode:  # continuous conversion mode
            self.config |= MCP342x._continuous_mode_mask
        else:  # one-shot conversion mode
            self.config &= (~MCP342x._continuous_mode_mask & 0x7f)

    def set_channel(self, channel):
        if channel not in MCP342x._channel_to_config:
            raise Exception('Illegal channel')
        elif channel in (2, 3) and \
                self.device not in ('MCP3424', 'MCP3428'):
            raise Exception('Channel ' + str(channel) +
                            ' not supported by ' + self.device)

        self.config &= (~MCP342x._channel_mask & 0x7f)
        self.config |= MCP342x._channel_to_config[channel]

    def set_scale_factor(self, scale_factor):
        self.scale_factor = scale_factor

    def set_offset(self, offset):
        self.offset = offset

    def set_config(self, config):
        self.config = config & 0x7f

    def get_conversion_ms(self):
        return MCP342x._conversion_ms[self.get_resolution()]

    def initiate_conversion(self):
        """Send the current config, along with a high /RDY bit.
        """
        self.cbuffer[0] = self.config | MCP342x._not_ready_mask
        print('Writing ' + hex(self.address) + ' cfg_reg: ' + bin(self.cbuffer[0]))
        self.i2c.writeto(self.address, self.cbuffer)

    def raw_read(self):
        d = self.i2c.readfrom(self.address, self.bytes_to_read)
        config_used = d[-1]
        # Verify a matching configuration.
        if (config_used & 0x7f) != (self.config & 0x7f):
            raise Exception('Config does not match: '
                            + MCP342x.config_to_str(config_used)
                            + ' != '
                            + MCP342x.config_to_str(self.config))
        # Check if conversion result is ready.
        if config_used & MCP342x._not_ready_mask:
            return None  # not ready
        else:
            count = 0
            for i in range(self.bytes_to_read - 1):
                count <<= 8
                count |= d[i]
            sign_bit = count & self.sign_bit_mask
            count &= self.count_mask
            if sign_bit:
                # Count is negative, so perform 2's complement, i.e. -(~orig_count + 1)
                count = -(~count & self.count_mask) - 1
            return count

    def read(self):
        time.sleep_ms(self.get_conversion_ms())
        for _ in range(5):
            count = self.raw_read()
            if count is not None:
                return count
            time.sleep_ms(5)
        raise Exception('Conversion not performed in time')

    async def read_async(self):
        await asyncio.sleep_ms(self.get_conversion_ms())
        for _ in range(5):
            count = self.raw_read()
            if count is not None:
                return count
            await asyncio.sleep_ms(5)
        raise Exception('Conversion not performed in time')

    def voltage(self, count):
        """Using the given raw count, calculate voltage (voltage difference between IN+ and IN-).
        """
        return count * MCP342x.config_to_lsb(self.config) / MCP342x.config_to_gain(self.config)

    def scaled(self, value, scale_factor = None, offset = None):
        """Scale the given value (whether raw count or a converted voltage).
        Used to account for gain or attenuation, transform to a sensor input value, etc.
        """
        sf = scale_factor if scale_factor is not None else self.scale_factor
        offs = offset if offset is not None else self.offset
        return (value * sf) + offs

    def convert_and_read(self):
        self.initiate_conversion()
        return self.read()

    async def convert_and_read_async(self):
        self.initiate_conversion()
        return await self.read_async()

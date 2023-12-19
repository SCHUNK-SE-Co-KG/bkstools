#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Created on 04.03.2022

@author: R001483
'''

import minimalmodbus
import time
import wrapt
import serial


@wrapt.patch_function_wrapper( serial.Serial, 'read' )
def read_my(wrapped, instance, args, kwargs):
    # here, wrapped is the original __init__,
    # instance is `self` instance (it is not true for classmethods though),
    # args and kwargs are tuple and dict respectively.

#def read_my( self, nb_bytes_to_read ):
    read_old = wrapped
    self = instance
    t0 = time.monotonic()
    t_end = t0 + self.timeout
    answer = b""
    nb_reads = 0
    nb_bytes_to_read = args[0]
    while (True):
        answer += read_old( nb_bytes_to_read )
        nb_reads += 1
        if ( len( answer ) == nb_bytes_to_read ):
            break
        if ( time.monotonic() > t_end ):
            break

    t1 = time.monotonic()
    print( f"read {len(answer)} bytes in {nb_reads} reads in {t1-t0}s")
    return answer

def mb():
    mb_bks = minimalmodbus.Instrument('COM2', 14)  # port name, slave address (in decimal)
    #mb_bks.serial.port                     # this is the serial port name
    mb_bks.serial.baudrate = 115200         # Baud
    mb_bks.serial.bytesize = 8
    mb_bks.serial.parity   = minimalmodbus.serial.PARITY_EVEN
    mb_bks.serial.stopbits = 1
    mb_bks.serial.timeout  = 0.05          # seconds

    mb_bks.address                         # this is the slave address number
    mb_bks.mode = minimalmodbus.MODE_RTU   # rtu or ascii mode
    mb_bks.clear_buffers_before_each_transaction = True

    #exception_status = ord( mb_bks._perform_command( 7, "" ) )
    #print( f"exception_status=0x{exception_status:02x}")

    ## Read actual_pos (PV = ProcessValue) ##
    #mb_bks.serial.read_old = mb_bks.serial.read
    #mb_bks.serial.read = read_my
    actual_pos = mb_bks.read_float(0x230-1, byteorder=minimalmodbus.BYTEORDER_LITTLE)  # Registernumber, number of decimals
    print(actual_pos)
    #
    # sw_version_txt = mb_bks.read_string( 0x1118-1, 11 )
    # print(sw_version_txt)
    #
    # ## Change actual_pos setpoint (SP) ##
    # #NEW_actual_pos = 95
    # #mb_bks.write_register(24, NEW_actual_pos, 1)  # Registernumber, value, number of decimals for storage


def main():
    mb()

if __name__ == '__main__':
    try:
        from pyschunk.tools import attach_to_debugger
        attach_to_debugger.AttachToDebugger( main )
    except KeyboardInterrupt:
        print( "Interrupted by user." )
    #main()

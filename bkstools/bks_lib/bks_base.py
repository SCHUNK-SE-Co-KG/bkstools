# -*- coding: UTF-8 -*-
'''
Created on 21.11.2018

@author: Dirk Osswald

@brief Provides the basic BKSBase class for generic access to SCHUNK BKS grippers via the HTTP/JSON webinterface
'''


from threading import Thread, current_thread
import re

from bkstools.bks_lib.bks_modbus import BKS_Modbus
from bkstools.bks_lib.bks_http import BKS_HTTP
import time


#                         1                 12 3   32 4 5   54 6 7  78     89  96
rex_serial = re.compile( "(COM\d+|/dev/[^,]+)(,(\d+))?(,(\d+))?(,(\d)([NEO])(\d))?" )

def GetModbusSettings( host ):
    mob_serial = rex_serial.match( host )
    if ( mob_serial ):
        port = mob_serial.group(1)

        if ( mob_serial.group(3) ):
            slave_id = int( mob_serial.group(3) )
        else:
            slave_id = 12
        if ( slave_id < 0  or  247 < slave_id ):
            raise ValueError( "slave_id is not in 0..247" )
        try:
            baudrate = int( mob_serial.group(5) )
        except TypeError:
            baudrate = 115200

        try:
            nb_data_bits = int( mob_serial.group(7) )
        except TypeError:
            nb_data_bits = 8

        try:
            parity = mob_serial.group(8)
        except TypeError:
            parity = "E"
        if ( parity is None ):
            parity = "E"

        try:
            nb_stop_bits = int( mob_serial.group(9) )
        except TypeError:
            nb_stop_bits = 1

        return (port, slave_id, baudrate, nb_data_bits, parity, nb_stop_bits)
    return None

def BKSBase( host, max_age_in_s=5*60, debug=False, repeater_timeout=3.0, repeater_nb_tries=5 ):
    """Factory function to return an object to allow access to SCHUNK BKS grippers
    """
    modbus_settings = GetModbusSettings( host )

    if ( modbus_settings ):
        return BKS_Modbus( *modbus_settings, max_age_in_s, debug, repeater_timeout, repeater_nb_tries )
    else:
        return BKS_HTTP( host, max_age_in_s, debug )




g_user_input = None

#from bkstools.bks_lib.debug import Print

def take_input( prompt ):
    '''Helper function to prompt for user input. To be run in a separate thread.
    The user provided keyboard input is available in global g_user_input
    '''
    global g_user_input
    #Print( f"{current_thread()!r}: {prompt}" )
    #g_user_input = input()

    g_user_input = input( prompt )


def do_something_input( a_function, prompt ):
    '''A function to do something while waiting for user input
    '''
    global g_user_input

    g_user_input = None
    input_thread = Thread( target=take_input, args=[prompt] )
    input_thread.start()

    while ( g_user_input is None ):
        a_function()

    input_thread.join()
    #Print( f"joined alive={input_thread.is_alive()}")
    return g_user_input

def keep_communication_alive( bksb ):
    '''Function to be called to keep communication with gripper alive
    and keep the gripper out of ERR_COMM_LOST. Must be called repeatedly
    '''
    plc_sync_input = bksb.plc_sync_input  # @UnusedVariable
    #Print( f"keeping alive in thread {current_thread()!r} error={((plc_sync_input[0] | bksb.sw_error) == 0)}" )
    time.sleep( 0.050 )

def keep_communication_alive_input( bksb, prompt ):
    '''Helper to keep communication alive (and gripper out of ERR_COMM_LOST error) while prompting for user input
    '''
    return do_something_input( lambda : keep_communication_alive(bksb), prompt )


def keep_communication_alive_sleep( bksb, t ):
    end = time.time() + t
    while ( time.time() < end ):
        keep_communication_alive( bksb )

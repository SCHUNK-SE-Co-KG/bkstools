#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Created on 18.10.2018
#
# @author: Dirk Osswald
'''
Move a SCHUNK BKS gripper (like EGI/EGU/EGK) according to the parameters given.|n
|n
You can provide a single absolute or relative target position or a sequence|n
of (mixed) absolute or relative target positions. You can even|n
include pauses of fixed length in a sequence.|n
|n
Example usage:|n
-  %(prog)s -H 10.49.57.13 --pos=50|n
-  %(prog)s -H 10.49.57.13 --pos=10.5,50,100 --vel=50|n
-  %(prog)s -H 10.49.57.13 --pos=10,50,stay5s,10r,-20r|n
'''
#-  %(prog)s -H 10.49.57.13 --pos=10.5,50,100 --vel=50,10,25.5 --acc=10,20,30 --loop --interactive

import os.path
import re
import pyschunk.tools.mylogger
import time
from bkstools.bks_lib.bks_base import BKSBase
from bkstools.bks_lib.bks_modbus import cRepeater
from pyschunk.generated.generated_enums import eCmdCode
from bkstools.bks_lib.debug import Print, ApplicationError
from bkstools.bks_lib.debug import InsufficientWriteRights  # @UnusedImport
from bkstools.bks_lib.debug import g_logmethod              # @UnusedImport

logger = pyschunk.tools.mylogger.getLogger( "BKSTools.bks_move" )
pyschunk.tools.mylogger.setupLogging()
g_logmethod = logger.info

from bkstools.bks_lib import bks_options



def mklist( s, l=None ):
    '''return a list of all the values in s. Verify that the resulting list length matches that of the list l (if given).
    If the resulting list would have length 1 and l has more items then the resulting list is a list of len(l) times s.
    '''
    sl = eval( "[" + s + "]", {"__builtins__":None}, {} )
    if ( l is None ):
        return sl
    if ( len(sl) == len(l)):
        return sl
    if ( len( sl ) == 1 ):
        return sl*len(l)
    raise ApplicationError( f"Lengths of pos/vel parameters do not match. Expected 1 or {len(l)} but got {len(sl)} from {sl!r}" )


def GetMovementTime( p0, p1, v, a ):
    return abs( (p1-p0) / v ) # TODO: take a into account


def main():
    if ( "__file__" in globals() ):
        prog = os.path.basename( globals()["__file__"] )
    else:
        # when runnging as an exe generated by py2exe then __file__ is not defined!
        prog = "bks_move.exe"

    parser = bks_options.cBKSTools_OptionParser( prog=prog,
                                                 description = __doc__ )     # @UndefinedVariable

    parser.add_argument( '--pos',
                         dest="poss",
                         default="",
                         required=True,
                         help="""Required position(s) to move to in mm.
                         Single position or a list of comma separated positions.
                         If a plain number is given then it is interpreted as
                         an absolute target position. If a number with a "r" suffix
                         is given like "5r" or "-10r" then it is interpreted as
                         a relative target position and is taken relative to the
                         actual position of the gripper at the time that new target
                         position is considered.  To make the gripper pause for
                         a fixed amount of time a position can be given as "stay5s"
                         which would make the gripper stay in the current position for 5 seconds.""" )
    parser.add_argument( '--vel',
                         dest="vels",
                         default="15.0",
                         help="""Optional velocitie(s) to move with in mm/s.
                         Single velocity for all movements or a list of as many comma separated velocities as positions given with --pos. Default is %(default)s.""" )
    # acceleration can only be set by user SERVICE...
    #parser.add_argument( '--acc',
    #                     dest="accs",
    #                     default="250.0",
    #                     help="""Optional acceleration(s) to move with in mm/(s*s).
    #                     Single acceleration for all movements or a list of as many comma separated accelerations as positions given with --pos. Default is %(default)s.""" )
#     parser.add_argument( '--cur',
#                          dest="curs",
#                          default="0.2",
#                          help="""Optional current(s) to move with in A.
#                          Single current for all movements or a list of as many comma separated currents as positions given with --pos. Default is %(default)s.""" )

    parser.add_argument( '--loop',
                         action='store_true',
                         help="Flag, if set then the movement list will be looped forever." )
    parser.add_argument( '--auto_acknowledge',
                         action='store_true',
                         help="Flag, if set then occurring errors are automatically acknowledged. Use with caution!" )

    parser.add_argument( '--interactive',
                         action='store_true',
                         help="Flag, if set then the movement list will be processed interactively, i.e. each new movement must be explicitly confirmed by pressing RETURN." )

    parser.add_argument( '--wait_time',
                         dest="wait_after_pos_reached",
                         default=0.5, type=float,
                         help="""Time in s to wait after a movement is reached before starting next movement in non interactive mode. Default is %(default)f""" )

    args = parser.parse_args()

    # For the "stayXs" and the "Xr" positions these have to be converted to strings before evaluating them:
    #                        1       2   3     3       2   4        5     5            4 1
    poss_strings = re.sub( r"(stay\s*(\d+(\.\d*)?|\.\d+)s?|([+-]?\d+(\.\d*)?|[+-]?\.\d+)r)", r"'\1'", args.poss )

    poss=mklist( poss_strings )
    vels=mklist( args.vels, poss )
    #accs=mklist( args.accs, poss )
    #curs=mklist( args.curs, poss )
    eps = 0.1

    bks = BKSBase( args.host, debug=args.debug, repeater_timeout=args.repeat_timeout, repeater_nb_tries=args.repeat_nb_tries )

    Print( f"Starting at {bks.actual_pos:.1f} mm" )

    bks.command_code = eCmdCode.CMD_ACK

    looping = True # doit at least once
    nb_loops = 0
    nb_errors = 0
    nb_warnings = 0

    def CheckForErrors( bks, auto_acknowledge ):
        #--- Check for errors / warnings:
        nonlocal nb_errors, nb_warnings
        err_code = bks.err_code
        wrn_code = bks.wrn_code

        try:
            wc_str = bks.enums["wrn_code"].GetName(wrn_code, "?" )
        except KeyError:
            wc_str = "?"
        try:
            ec_str = bks.enums["err_code"].GetName(err_code, "?" )
        except KeyError:
            ec_str = "?"

        if ( err_code != 0 ):
            if ( auto_acknowledge ):
                bks.command_code = eCmdCode.CMD_ACK
                Print( f"!!!\n!!! Gripper reports error 0x{err_code:02x} ({ec_str}). Ignored!\n!!!" )
                nb_errors += 1
            else:
                raise ApplicationError( f"Gripper reports error 0x{err_code:02x} ({ec_str}). Giving Up." )

        if ( wrn_code == bks.enums["wrn_code"]["WRN_NOT_FEASIBLE"] ):
            nb_warnings += 1
            bks.sys_msg_req = 0
            msg = bks.sys_msg_buffer
            raise ApplicationError( f"Gripper reports command not feasible!\nDetails from syslog: {msg}" )

        elif ( wrn_code != 0 ):
            nb_warnings += 1
            Print( f"!!! Gripper reports warning 0x{wrn_code:02x} ({wc_str}). Ignored." )

    try:
        while looping:
            try:
                # The acceleration can only be set and read by SERVICE or ROOT
                #a = bks.set_acc
                a = 5000.0

                #for (p,v,a,c) in zip( poss, vels, accs, curs ):
                for (p,v) in zip( poss, vels ):
                    move_relative = False
                    if ( type(p) is str ):
                        if ( p.startswith( "stay") ):
                            T = float( re.sub( r"stay\s*(\d+(\.\d*)?|\.\d+)s?", r"\1", p ) )
                            Print( f"pausing for {T:.3f}s ..." )
                            time.sleep( T )
                            continue
                        if ( p.endswith( "r" ) ):
                            p = float( re.sub( r"([+-]?\d+(\.\d*)?|[+-]?\.\d+)r", r"\1", p ) )
                            move_relative = True
                        else:
                            raise ApplicationError( f"Invalid position {p}. giving up." )

                    bks.set_pos = p
                    bks.set_vel = v
                    #try:
                    #    bks.set_acc = a
                    #    #bks.set_cur = c
                    #except InsufficientWriteRights:
                    #    # only SERVCICE can set set_acc
                    #    pass # TODO: give some indication that setting the acceleration failed

                    CheckForErrors( bks, args.auto_acknowledge)

                    time.sleep(0.1)
                    if ( move_relative ):
                        if ( args.interactive ):
                            input( f"Press RETURN to move relative by {p:.1f} mm with {v:.1f} mm/s..." )
                        Print( f"moving relative by {p:.1f} mm with {v:.1f} mm/s ..." )
                        bks.command_code = eCmdCode.MOVE_POS_REL
                        target_pos_abs = bks.actual_pos+p
                    else:
                        if ( args.interactive ):
                            input( f"Press RETURN to move absolute to {p:.1f} mm with {v:.1f} mm/s..." )
                        Print( f"moving absolute to {p:.1f} mm with {v:.1f} mm/s ..." )
                        bks.command_code = eCmdCode.MOVE_POS
                        target_pos_abs = p

                    now = time.time()
                    t0 = now
                    ttimeout = t0 + GetMovementTime( bks.actual_pos, target_pos_abs, v, a ) + 1.0

                    # check for errors / warnings once after command code was set:
                    CheckForErrors( bks, args.auto_acknowledge)

                    while ( now < ttimeout and abs( bks.actual_pos - target_pos_abs ) > eps ):
                        time.sleep(0.02)
                        now = time.time()

                    if ( now > ttimeout ):
                        # check for errors / warnings on a timeout:
                        CheckForErrors( bks, args.auto_acknowledge)
                        Print( f"Timeout! after {(ttimeout-t0):.3f} s"  )

                    Print( f"reached {bks.actual_pos:.1f} mm" )
                    time.sleep( args.wait_after_pos_reached )
                looping = args.loop
                nb_loops += 1

            except KeyboardInterrupt:
                Print( "\nUser interrupt, fast-stopping" )
                looping = False
                bks.command_code = eCmdCode.CMD_FAST_STOP
                time.sleep(1)
    finally:
        Print( "\n===" )
        try:
            Print( f"finally reached {bks.actual_pos:.1f} mm after {nb_loops} movement cycles." )
        except Exception:
            pass
        Print( f"Gripper reported {nb_errors} errors and {nb_warnings} warnings." )
        try:
            Print( f"Performed {cRepeater.s_nb_repeaters} read/write accesses with {cRepeater.s_nb_repeaters_with_failures} ({100.0*cRepeater.s_nb_repeaters_with_failures/cRepeater.s_nb_repeaters:.1f} %) recoverable communication-failures.")
        except ZeroDivisionError:
            # cRepeater not available for BKS_HTTP modules, so the print yields a ZeroDivisionError. Just ignore
            pass

if __name__ == '__main__':
    from pyschunk.tools import attach_to_debugger
    attach_to_debugger.AttachToDebugger( main )
    #main()

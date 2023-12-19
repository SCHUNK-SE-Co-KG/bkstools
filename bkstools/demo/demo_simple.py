#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Created on 2021-08-06
#
# @author: Dirk Osswald
'''
Simple basic control (move, grip, release) of a SCHUNK BKS gripper (like EGI/EGU/EGK/EZU)|n
|n
Example usage:|n
-  %(prog)s -H 10.49.57.13
'''

import os.path
import time

from bkstools.bks_lib.bks_base import BKSBase, keep_communication_alive_input, keep_communication_alive_sleep
from pyschunk.generated.generated_enums import eCmdCode
from bkstools.bks_lib.debug import Print, Var, ApplicationError, g_logmethod  # @UnusedImport
from bkstools.bks_lib import bks_options
from bkstools.scripts.bks_grip import WaitGrippedOrError

def main():
    if ( "__file__" in globals() ):
        prog = os.path.basename( globals()["__file__"] )
    else:
        # when runnging as an exe generated by py2exe then __file__ is not defined!
        prog = "demo_simple.exe"


    #--- create a command line option parser and parse the command line:
    parser = bks_options.cBKSTools_OptionParser( prog=prog,
                                                 description = __doc__,   # @UndefinedVariable
                                                 additional_arguments=[ "force" ] )
    args = parser.parse_args()

    #--- Create a BKSBase object to interact with the gripper:
    bksb = BKSBase( args.host, debug=args.debug, repeater_timeout=args.repeat_timeout, repeater_nb_tries=args.repeat_nb_tries )


    def my_input( prompt ):
        '''alias
        '''
        return keep_communication_alive_input( bksb, prompt )

    def my_sleep( t ):
        '''alias
        '''
        return keep_communication_alive_sleep( bksb, t )

    # Remarks:
    # - The bksb object just created queried the gripper for all its available
    #   parameters on construction. These parameters are avaialbe as
    #   properties of the bksb object (i.e. they can be accessed like normal member variables)
    # - E.g. the actual position of the gripper is available now
    #   as `bksb.actual_pos`. When the script accesses this property
    #   then actually a http get request is sent to gripper and the JSON
    #   response is parsed, converted accordingly and returned.
    # - For writable parameters like the `bksb.command_code` a http post
    #   request is generated when the script sets that property.

    #--- Prepare gripper: Acknowledge any pending error:
    bksb.command_code = eCmdCode.CMD_ACK
    time.sleep(0.1)

    print( f"Actual position is {bksb.actual_pos:.1f} mm." )

    #--- Open gripper by moving to an absolute postion:
    bksb.set_pos = 30.0 # target position at 30 mm (distance between fingers)
    bksb.set_vel = 50.0 # target velocity limited to 50 mm/s
    my_input( f"\nPress return to move to absolute position {bksb.set_pos:.1f} mm:")
    bksb.command_code = eCmdCode.MOVE_POS
    my_sleep(3)

    #--- Perform a simple grip (from outside) movement:
    bksb.set_force = 50  # target force to 50 %
    bksb.set_vel = 0.0   # target velocity 0 => BasicGrip
    bksb.grp_dir = False # grip from outside
    my_input( f"\nActual postion is {bksb.actual_pos:.1f} mm.\nInsert a workpiece to grasp from outside. (Do not use your finger!)\nPress return to perform a grip from outside movement:")
    bksb.command_code = eCmdCode.MOVE_FORCE    # (for historic reasons the actual grip command for simple gripping is called MOVE_FORCE...)
    WaitGrippedOrError( bksb )

    #--- Perform a release operation movement:
    my_input( f"\nFound workpiece at {bksb.actual_pos:.1f} mm.\nPress return to release the gripped workpiece:")
    # This will move the fingers `bksb.wp_release_delta` mm away from the workpiece
    bksb.command_code = eCmdCode.CMD_RELEASE_WORK_PIECE
    my_sleep(1)

    #--- Perform a simple grip (from inside) movement:
    bksb.set_force = 50 # target force to 50 %
    bksb.grp_dir = True # grip from inside
    my_input( f"\nActual postion is {bksb.actual_pos:.1f} mm.\nInsert a workpiece to grasp from inside. Do not use your finger!\nPress return to perform a grip from inside movement:")

    bksb.command_code = eCmdCode.MOVE_FORCE    # (for historic reasons the actual grip command for simple gripping is called MOVE_FORCE...)
    WaitGrippedOrError( bksb )

    #--- Perform a release operation movement:
    my_input( f"\nFound workpiece at {bksb.actual_pos:.1f} mm.\nPress return to release the gripped workpiece:")
    bksb.command_code = eCmdCode.CMD_RELEASE_WORK_PIECE
    my_sleep(1)


if __name__ == '__main__':
    from pyschunk.tools import attach_to_debugger
    attach_to_debugger.AttachToDebugger( main )
    #main()

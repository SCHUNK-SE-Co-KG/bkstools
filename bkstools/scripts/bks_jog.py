#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Created on 18.10.2018
#
# @author: Dirk Osswald
'''
Simple interactive moving of a SCHUNK BKS gripper (like EGI/EGU/EGK) in position, speed or jog mode.|n
|n
Example usage:|n
-  %(prog)s -H 10.49.57.13 |n
'''

import os.path
import requests

import pyschunk.tools.mylogger
import pyschunk.guistuff

import time
from tkinter import * #@UnusedWildImport
from bkstools.bks_lib.bks_base import BKSBase
from pyschunk.generated.generated_enums import eCmdCode
from bkstools.bks_lib.bks_gui import cAppWithExceptionHandler
from bkstools.bks_lib.debug import Print, Var, ApplicationError, InsufficientReadRights, InsufficientWriteRights, ControlledFromOtherChannel, g_logmethod  # @UnusedImport
from bkstools.bks_lib import hsm_enums
from bkstools.bks_lib.bks_modbus import RepeaterException

logger = pyschunk.tools.mylogger.getLogger( "BKSTools.bks_jog" )
pyschunk.tools.mylogger.setupLogging()
g_logmethod = logger.info

from bkstools.bks_lib import bks_options

class cJogApp(cAppWithExceptionHandler):
    '''tkinter application for interactive jogging
    '''
    def __init__(self, master, args ):
        cAppWithExceptionHandler.__init__(self, master=master, class_="cJogApp" )

        self.bks = BKSBase( args.host, debug=args.debug, repeater_timeout=args.repeat_timeout, repeater_nb_tries=args.repeat_nb_tries )
        self.args = args
        self.moving = 0
        self.cyclic_update = True

        self.set_pos = 0.0
        self.set_vel = 15.0   # 15 is default minimum feasible velocity
        self.set_acc = 500.0  # 250 is default minimum feasible acceleration
        #self.desired_current      = 0.2   # not available any longer
        self.parameter = ""
        self.parameter_name = None
        self.try_internal_params = True

        f = Frame( master )
        pady= 1
        font1=("Helvetica", "8")
        font2=("Helvetica", "12")
        font3=("Helvetica", "7")
        Label( f, text="Keep middle mouse button or cursor-left key pressed: Jog in negative direction", anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Keep right mouse key or cursor-right key pressed: Jog in positive direction" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press U to toggle cyclic updating" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press S to stop a movement" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press F12 or Pause to fast_stop" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press R to determine base zero position (only for ROOT)" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press Q to send CMD_ACK" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press CTRL-P to prepare for shutdown" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press CTRL-R to reset" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press M and enter numeric position to move to and press enter to start position movement" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press CTRL-M and enter numeric position and press enter to to just set desired position" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press V and enter numeric velocity to move with and press enter to start movement" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press CTRL-V and enter numeric velocity and press enter to to just set desired velocity" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        Label( f, text="Press (CTRL-)A and enter numeric acceleration and press enter to to just set desired acceleration" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        #Label( f, text="Press (CTRL-)C and enter numeric current and press enter to to just set desired current" , anchor=W, justify=LEFT, font=font1 ).pack( side=TOP, fill=X, pady=pady )
        self.v_ver = StringVar()
        self.v_ver.set( "<not connected yet>")
        self.l_ver = Label( f, textvariable=self.v_ver, font=font2 )
        self.l_ver.pack(side=TOP, pady=5)

        f_params = Frame( f )
        f_labels = Frame( f_params )
        f_values = Frame( f_params )
        padx = 0
        pady = 5

        def ParamLabelPack( text="" ):
            l = Label( f_labels, text=text, font=font2, anchor=E, justify=RIGHT, foreground="#606060" )
            l.pack(side=TOP, padx=padx, pady=pady, fill=X, expand=YES )
            return l
        def ValueLabelPack( textvariable=None ):
            l = Label( f_values, textvariable=textvariable, font=font2, anchor=W, justify=LEFT )
            l.pack(side=TOP, padx=padx, pady=pady, fill=X, expand=YES )
            return l

        ParamLabelPack( "actual_user:" )
        self.v_user = StringVar()
        self.v_user.set( "<not connected yet>")
        self.l_user = ValueLabelPack( self.v_user )

        ParamLabelPack( "actual_pos:" )
        self.v_pos = StringVar()
        self.v_pos.set( "<not connected yet>")
        self.l_pos = ValueLabelPack( self.v_pos )

        ParamLabelPack( "application_state:" )
        self.v_application_state = StringVar()
        self.v_application_state.set( "<not connected yet>")
        self.l_application_state = ValueLabelPack( self.v_application_state )

        #ParamLabelPack( "motion_engine_state:" )
        #self.v_motion_engine_state = StringVar()
        #self.v_motion_engine_state.set( "<not connected yet>")
        #self.l_motion_engine_state = ValueLabelPack( self.v_motion_engine_state )

        ParamLabelPack( "comm_state:" )
        self.v_anybus_state = StringVar()
        self.v_anybus_state.set( "<not connected yet>")
        self.l_anybus_state = ValueLabelPack( self.v_anybus_state )

        ParamLabelPack( "supervised_by_plc:" )
        self.v_supervised_by_plc = IntVar()
        self.c_supervised_by_plc = Checkbutton( f_values, text="", variable=self.v_supervised_by_plc, font=font2, anchor=W, justify=LEFT )
        self.c_supervised_by_plc.pack( side=TOP, padx=padx, pady=1, fill=X, expand=YES )

        ParamLabelPack( "ctrl_authority:" )
        self.v_ctrl_authority = StringVar()
        self.v_ctrl_authority.set( "<not connected yet>")
        self.l_ctrl_authority = ValueLabelPack( self.v_ctrl_authority )

        ParamLabelPack( "err_code:" )
        self.v_err_code = StringVar()
        self.v_err_code.set( "<not connected yet>")
        self.l_err_code = ValueLabelPack( self.v_err_code )

        ParamLabelPack( "wrn_code:" )
        self.v_wrn_code = StringVar()
        self.v_wrn_code.set( "<not connected yet>")
        self.l_wrn_code = ValueLabelPack( self.v_wrn_code )
        f_labels.pack(side=LEFT)
        f_values.pack(side=LEFT)
        f_params.pack(side=TOP)
        self.grey_out_labels = [ self.l_ver, self.l_user, self.l_pos, self.l_application_state, self.l_ctrl_authority, self.l_err_code, self.l_wrn_code, self.l_anybus_state, self.c_supervised_by_plc ]
        # self.l_motion_engine_state,

        self.v_status_line = StringVar()
        self.v_status_line.set( "" )
        self.l_status_line = Label( f, textvariable=self.v_status_line, fg="blue", font=font3, anchor=W, justify=LEFT, background="#f8f8f8" )
        self.l_status_line.pack(side=TOP, pady=pady, fill=X )
        self.foreground = pyschunk.guistuff.colors.grey50

        f.pack( fill=BOTH, expand=1 )

        self.after_move_stop_id = None
        self.master.bind('<Button-2>', self.cbMoveNegative )
        self.master.bind('<ButtonRelease-2>', self.cbMoveStop )
        self.master.bind('<Button-3>', self.cbMovePositive )
        self.master.bind('<ButtonRelease-3>', self.cbMoveStop )
        self.master.bind('<KeyPress>', self.cbKeyPress )
        self.master.bind('<KeyRelease>', self.cbKeyRelease )
        self.master.bind('q', self.cbAcknowledge )
        self.master.bind('<Control-Key-p>', self.cbPrepareShutdown )
        self.master.bind('<Control-Key-r>', self.cbReset )
        self.master.bind('<F12>', self.cbFastStop )
        self.master.bind('<Pause>', self.cbFastStop )

        self.master.bind('m', self.cbEnterMovePos )
        self.master.bind('v', self.cbEnterMoveVel )
        self.master.bind('a', self.cbEnterAcceleration )
        #self.master.bind('c', self.cbEnterCurrent )
        self.master.bind('0', self.cbEnterDigit )
        self.master.bind('1', self.cbEnterDigit )
        self.master.bind('2', self.cbEnterDigit )
        self.master.bind('3', self.cbEnterDigit )
        self.master.bind('4', self.cbEnterDigit )
        self.master.bind('5', self.cbEnterDigit )
        self.master.bind('6', self.cbEnterDigit )
        self.master.bind('7', self.cbEnterDigit )
        self.master.bind('8', self.cbEnterDigit )
        self.master.bind('9', self.cbEnterDigit )
        self.master.bind('-', self.cbEnterDigit )
        self.master.bind('.', self.cbEnterDigit )
        self.master.bind(',', self.cbEnterDigit )
        self.master.bind('<BackSpace>', self.cbBackspaceDigit )
        self.master.bind('<Escape>', self.cbEscape )
        self.master.bind('<Return>', self.cbEndCommnand )

        self.after( 500, self.cbUpdate )

    def SetStatusline( self, msg, is_error=False ):
        self.v_status_line.set( msg )
        if ( is_error ):
            self.l_status_line.config( foreground="red" )
        else:
            self.l_status_line.config( foreground="blue" )

    def pevent(self,event):
        print(("event.char=%r (%s" % (event.char,type(event.char))))
        print(("event.delta=%r (%s" % (event.delta,type(event.delta))))
        print(("event.keycode=%r (%s" % (event.keycode,type(event.keycode))))
        print(("event.keysym=%r (%s" % (event.keysym,type(event.keysym))))
        print(("event.state=%r (%s" % (event.state,type(event.state))))
        print(("event.type=%r (%s" % (event.type,type(event.type))))
        print("---")

    def cbEnterMovePos(self ,event):
        #self.pevent(event)
        self.parameter = ""
        self.parameter_name = "set_pos"
        if ( event.state == 12 ):
            # CTRL-m was pressed
            self.entered_command = None
        else:
            self.entered_command = eCmdCode.MOVE_POS
        self.UpdateInteraction()

    def cbEnterMoveVel(self, event):
        #self.pevent(event)
        self.parameter = ""
        self.parameter_name = "set_vel"
        if ( event.state == 12 ):
            # CTRL-v was pressed
            self.entered_command = None
        else:
            self.entered_command = eCmdCode.MOVE_VEL
        self.UpdateInteraction()

    def cbEnterAcceleration(self, event):
        self.parameter = ""
        self.parameter_name = "set_acc"
        self.entered_command = None
        self.UpdateInteraction()

#     def cbEnterCurrent(self, event):
#         self.parameter = ""
#         self.parameter_name = "desired_current"
#         self.entered_command = None
#         self.UpdateInteraction()

    def cbEnterDigit(self, event):
        if ( not self.parameter is None ):
            if ( event.char == "," ):
                event.char = "."
            self.parameter += event.char
            self.UpdateInteraction()

    def cbBackspaceDigit(self, event):
        self.parameter = self.parameter[:-1]
        self.UpdateInteraction()


    def cbEscape(self, event):
        self.parameter = ""
        self.parameter_name = None
        self.SetStatusline( "" )


    def UpdateInteraction(self):
        if ( self.entered_command ):
            self.SetStatusline( "setting %s=%s... (preparing %r)" % (self.parameter_name,self.parameter,eCmdCode.GetName( self.entered_command )) )
        else:
            self.SetStatusline( "setting %s=%s..." % (self.parameter_name,self.parameter) )

    def cbEndCommnand(self,event):  # @UnusedVariable
        if ( self.parameter_name is None ):
            return
        try:
            if ( self.parameter == "" ):
                # reuse previously set value or default:
                val = self.__dict__[ self.parameter_name ]
            else:
                val = float( self.parameter )

            self.__dict__[ self.parameter_name ] = val

            if ( self.entered_command ):
                self.bks.set_pos = self.set_pos
                self.bks.set_vel = self.set_vel
                try:
                    self.bks.set_acc = self.set_acc
                    #self.bks.set_curr = self.set_cur # not available any longer
                except (InsufficientWriteRights,RepeaterException):
                    # only SERVCICE can set set_acc
                    pass # TODO: give some indication that setting the acceleration failed

                self.bks.command_code = self.entered_command
                self.SetStatusline( "set %s=%r and sent %s" % (self.parameter_name,val,eCmdCode.GetName( self.entered_command )) )
            else:
                self.SetStatusline( "set %s=%r" % (self.parameter_name,val) )
            self.parameter = None
        except Exception as e:
            self.SetStatusline( "failed to set %s from %r: %r" % (self.parameter_name,self.parameter,e), True )

    def SetBuildinfo(self):
        try:
            build_info = self.bks.build_info # cache the build info so that it is queried from the gripper only once
            self.v_ver.set( "%s B%s %s %s %s %s" % (build_info.buildDescriptor, build_info.buildNumber, build_info.compileDate, build_info.compileTime, build_info.buildUser, build_info.buildHost))
        except (InsufficientReadRights, RepeaterException): # FIXME: remove RepeaterException
            self.v_ver.set( "Firmware version =  ? (InsufficientReadRights)" )

    def cbUpdate(self):
        try:
            self.v_pos.set( "%.2f" % float( self.bks.actual_pos ) )

            try:
                system_state = int( self.bks.system_state )
                application_state   = (system_state & 0x0000ff00) >> 8
                #motion_engine_state = (system_state & 0x000000ff)
                self.v_application_state.set( "%d (%s)" % (application_state, hsm_enums.application_state_machine.GetName( application_state, "?" ) ) )
                #self.v_motion_engine_state.set( "%d (%s)" % ( motion_engine_state, hsm_enums.motion_engine.GetName( motion_engine_state, "?" )) )
            except InsufficientReadRights:
                self.v_application_state.set( "? (InsufficientReadRights)" )
                #self.v_motion_engine_state.set( "? (InsufficientReadRights)" )

            if self.try_internal_params:
                try:
                    anybus_default_state = "?"
                    anybus_state = int(self.bks.internal_params.comm_state)
                    self.v_anybus_state.set( "%d (%s)" % ( anybus_state, self.bks.enums["comm_state"].GetName( anybus_state, anybus_default_state )) )
                except InsufficientReadRights:
                    self.v_anybus_state.set( "? (InsufficientReadRights)" )
                    self.try_internal_params = False
                except RepeaterException:
                    self.v_anybus_state.set( "(not available)" )
                    self.try_internal_params = False

                try:
                    supervised_by_plc = int(self.bks.internal_params.supervised_by_plc)
                    self.v_supervised_by_plc.set( supervised_by_plc )
                except (InsufficientReadRights,RepeaterException):
                    self.c_supervised_by_plc.config( state=DISABLED )
                    self.try_internal_params = False

                try:
                    ctrl_authority = int( self.bks.ctrl_authority )
                    if ( ctrl_authority == 0 ):
                        s = "Service-Interface"
                    elif ( ctrl_authority == 1 ):
                        s = "Fieldbus"
                    elif ( ctrl_authority == 2 ):
                        s = "Webinterface"
                    else:
                        s = "? unknown"
                    self.v_ctrl_authority.set( "%d (%s)" % (ctrl_authority,s) )
                    if ( ctrl_authority == 2 ):
                        self.l_ctrl_authority.config( foreground="#00c000" )
                    else:
                        self.l_ctrl_authority.config( foreground="#ff0000" )
                except InsufficientReadRights:
                    self.v_ctrl_authority.set( "? (InsufficientReadRights)" )

                self.SetBuildinfo()

            err_code = int( self.bks.err_code )
            wrn_code = int( self.bks.wrn_code )
            self.v_err_code.set( "0x%02x (%s)" % ( err_code, self.bks.enums["err_code"].GetName( err_code, "?" )) )
            if ( err_code != 0 ):
                self.l_err_code.config( foreground="#ff0000" )
            else:
                self.l_err_code.config( foreground="#000000" )
            self.v_wrn_code.set( "0x%02x (%s)" % ( wrn_code, self.bks.enums["wrn_code"].GetName( wrn_code, "?" )) )
            if ( wrn_code != 0 ):
                self.l_wrn_code.config( foreground="#ff0000" )
            else:
                self.l_wrn_code.config( foreground="#000000" )
            new_foreground = pyschunk.guistuff.colors.black
        except (requests.ConnectionError, requests.ReadTimeout):
            new_foreground = pyschunk.guistuff.colors.grey50

        if ( self.foreground != new_foreground ):
            for l in self.grey_out_labels:
                l.config( foreground=new_foreground)
            self.foreground = new_foreground

            if new_foreground == pyschunk.guistuff.colors.black:
                self.SetBuildinfo()
                au = int( self.bks.actual_user )
                self.v_user.set( "%d (%s)" % (au, self.bks.enums["actual_user"].GetName( au )) )


        if ( self.cyclic_update ):
            self.after( 100, self.cbUpdate )


    def cbLeave(self,event):
        self.cursor_in_window = False
        self.cbMoveStop( event )

    def cbEnter(self,event):  # @UnusedVariable
        self.cursor_in_window = True

    def cbAcknowledge(self,event):  # @UnusedVariable
        self.bks.command_code = eCmdCode.CMD_ACK

    def cbPrepareShutdown(self,event):  # @UnusedVariable
        self.bks.command_code = eCmdCode.CMD_DISCONNECT

    def cbReset(self,event):  # @UnusedVariable
        self.bks.command_code = eCmdCode.CMD_REBOOT

    def cbKeyPress(self,event):
        if (event.keysym in ["s"]):
            self.bks.command_code = eCmdCode.CMD_STOP

        elif (event.keysym in ["r"]):
            #self.bks.command_code = eCmdCode.CMD_REFERENCE
            self.bks.command_code = eCmdCode.CMD_DETERMINE_BASE_ZERO_POS

        elif (event.keysym in ["u"]):
            self.cyclic_update = not self.cyclic_update
            if ( self.cyclic_update ):
                self.try_internal_params = True
                self.cbUpdate()

        elif (event.keysym in ["Right"]):
            if ( self.after_move_stop_id ):
                self.after_cancel( self.after_move_stop_id )
            self.cbMovePositive( event )
        elif (event.keysym in ["Left"]):
            if ( self.after_move_stop_id ):
                self.after_cancel( self.after_move_stop_id )
            self.cbMoveNegative( event )


    def cbKeyRelease(self,event):
        if (event.keysym in ["Left"] or event.keysym in ["Right"]):
            # On Linux the auto-repeat function will generate
            # Keypress and Keyrelease events with high frequency when the key is pressed longer
            # Sequence is: Keyrelease 1.8ms Keypress 20.0ms ...
            # So we must not react to the Keyreleases right away. So delay
            # their handling and cancel the handing when Keypress is received:
            self.after_move_stop_id = self.after(10, lambda : self.cbMoveStop( event ) )

    def cbMoveNegative(self,event):
        self.moving = -1
        #self.bks.command_code = eCmdCode.CMD_ACK
        time.sleep(0.05)
        self.bks.command_code = 0x18

    def cbMovePositive(self,event):
        self.moving = 1
        #self.bks.command_code = eCmdCode.CMD_ACK
        time.sleep(0.05)
        self.bks.command_code = 0x17

    def cbMoveStop(self,event):
        self.moving = 0
        self.bks.command_code = eCmdCode.CMD_STOP

    def cbFastStop(self,event):
        self.moving = 0
        self.bks.command_code = eCmdCode.CMD_FAST_STOP

def main():
    if ( "__file__" in globals() ):
        prog = os.path.basename( globals()["__file__"] )
    else:
        # when runnging as an exe generated by py2exe then __file__ is not defined!
        prog = "bks_jog.exe"

    parser = bks_options.cBKSTools_OptionParser( prog=prog,
                                                 description = __doc__ )     # @UndefinedVariable

    args = parser.parse_args()


    #--- Start GUI:
    pyschunk.guistuff.widgets.RunGUI( cJogApp,
                                      "BKS-Jog @ %s" % (args.host),
                                      args )


if __name__ == '__main__':
    from pyschunk.tools import attach_to_debugger
    attach_to_debugger.AttachToDebugger( main )


#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Created on 2019-01-18
#
# @author: Dirk Osswald
'''
Simple interactive display of cyclic data of a SCHUNK BKS gripper (like EGI/EGU/EGK), |n
including control- and statusword.|n
|n
Example usage:|n
-  %(prog)s -H 10.49.57.13 |n
'''

import os.path

import pyschunk.tools.mylogger
import pyschunk.guistuff

import requests
import minimalmodbus

from tkinter import * #@UnusedWildImport
from tkinter import ttk
#from bkstools.bks_lib.bks_base import BKSBase, requests, uint32_to_int32, int32_to_uint32
from bkstools.bks_lib.bks_base import BKSBase, BKS_HTTP
from bkstools.bks_lib.bks_base_common import uint32_to_int32, int32_to_uint32
from bkstools.bks_lib.bks_gui import cAppWithExceptionHandler
from bkstools.bks_lib.debug import UnsupportedCommand
from pyschunk.generated.generated_enums import eCmdCode


logger = pyschunk.tools.mylogger.getLogger( "BKSTools.bks_status" )
pyschunk.tools.mylogger.setupLogging()
g_logmethod = logger.info

from bkstools.bks_lib import bks_options

######
# add workaround for a bug in int TkInter for python 3.7, see https://bugs.python.org/issue44592
def my_nametowidget(self, name):
    """Return the Tkinter instance of a widget identified by
    its Tcl name NAME."""
    name = str(name).split('.')
    w = self

    if not name[0]:
        w = w._root()
        name = name[1:]

    for n in name:
        if not n:
            break
        try:
            w = w.children[n]
        except KeyError as e:  # @UnusedVariable
            # When opening the ctrl-authority combobox the update callback lands here with KeyError: 'popdown'
            #print( e )
            break # Just ignore that and return current widget w

    return w

Misc._nametowidget = my_nametowidget
######

class cstatusApp(cAppWithExceptionHandler):
    '''tkinter application for interactive status display
    '''

    def __init__(self, master, args ):
        cAppWithExceptionHandler.__init__(self, master=master, class_="cJogApp" )

        self.bks = BKSBase( args.host, debug=args.debug, repeater_timeout=args.repeat_timeout, repeater_nb_tries=args.repeat_nb_tries )

        # determine whether gripper uses old or new style cyclic data:
        try:
            dummy = self.bks.plc_sync_input.status_dword

            self.cyclic_data_in_struct = True
            #print "using old style cyclic data"

        except Exception:
            self.cyclic_data_in_struct = False
            #print "using new style cyclic data"

        self.args = args
        self.SetTitle()

        font1=("Helvetica", "8")
        font3=("Helvetica", "7")
        self.color_connected = "#80ff80"
        self.color_disconnected = "#ff8080"
        self.change_background_widgets = []
        self.background = ""

        self.v_jog_mode_minus = IntVar()
        self.v_jog_mode_plus = IntVar()
        self.control_bits_definition = [
            ("fast_stop", IntVar(), IntVar()), # 0
            ("stop", IntVar(), IntVar()), # 1
            ("acknowledge", IntVar(), IntVar()), # 2
            ("prepare_for_shutdown", IntVar(), IntVar()), # 3
            ("softreset", IntVar(), IntVar()), # 4
            ("emergency_release", IntVar(), IntVar()), # 5
            ("repeat_command_toggle", IntVar(), IntVar()), # 6
            ("grip_direction", IntVar(), IntVar()), # 7
            ("jog_mode_minus", IntVar(), self.v_jog_mode_minus), # 8
            ("jog_mode_plus", IntVar(), self.v_jog_mode_plus), # 9
            ("reserved10", IntVar(), IntVar()), # 10
            ("release_work_piece", IntVar(), IntVar()), # 11
            ("grip_work_piece", IntVar(), IntVar()), # 12
            ("move_to_absolute_position", IntVar(), IntVar()), # 13
            ("move_to_relative_position", IntVar(), IntVar()), # 14
            ("move_velocity_controlled", IntVar(), IntVar()), # 15
            ("grip_workpiece_with_position", IntVar(), IntVar()), # 16
            ("reserved17", IntVar(), IntVar()), # 17
            ("reserved18", IntVar(), IntVar()), # 18
            ("reserved19", IntVar(), IntVar()), # 19
            ("reserved20", IntVar(), IntVar()), # 20
            ("reserved21", IntVar(), IntVar()), # 21
            ("reserved22", IntVar(), IntVar()), # 22
            ("reserved23", IntVar(), IntVar()), # 23
            ("reserved24", IntVar(), IntVar()), # 24
            ("reserved25", IntVar(), IntVar()), # 25
            ("reserved26", IntVar(), IntVar()), # 26
            ("reserved27", IntVar(), IntVar()), # 27
            ("reserved28", IntVar(), IntVar()), # 28
            ("reserved29", IntVar(), IntVar()), # 29
            ("reserved30", IntVar(), IntVar()), # 30
            ("use_gpe", IntVar(), IntVar()), # 31
        ]

        self.status_bits_definition = [
            ("ready_for_operation", None, IntVar()), # 0
            ("control_authority", None, IntVar()), # 1
            ("ready_for_shutdown", None, IntVar()), # 2
            ("not_feasible", None, IntVar()), # 3
            ("success", None, IntVar()), # 4
            ("command_received_toggle", None, IntVar()), # 5
            ("warning", None, IntVar()), # 6
            ("error", None, IntVar()), # 7
            ("emergency_released", None, IntVar()), # 8
            ("softwarelimit", None, IntVar()), # 9
            ("reserved10", None, IntVar()), # 10
            ("no_workpiece_detected", None, IntVar()), # 11
            ("gripped", None, IntVar()), # 12
            ("position_reached", None, IntVar()), # 13
            ("pre_holding", None, IntVar()), # 14
            ("moving_velocity_controlled", None, IntVar()), # 15
            ("workpiece_lost", None, IntVar()), # 16
            ("wrong_workpiece_detected", None, IntVar()), # 17
            ("reserved18", None, IntVar()), # 18
            ("reserved19", None, IntVar()), # 19
            ("reserved20", None, IntVar()), # 20
            ("reserved21", None, IntVar()), # 21
            ("reserved22", None, IntVar()), # 22
            ("reserved23", None, IntVar()), # 23
            ("reserved24", None, IntVar()), # 24
            ("reserved25", None, IntVar()), # 25
            ("reserved26", None, IntVar()), # 26
            ("reserved27", None, IntVar()), # 27
            ("reserved28", None, IntVar()), # 28
            ("reserved29", None, IntVar()), # 29
            ("reserved30", None, IntVar()), # 30
            ("brake_active", None, IntVar()), # 31
        ]

        self.asf = pyschunk.guistuff.widgets.cAutoScrollFrame(master,background=pyschunk.guistuff.colors.schunk_background )
        f = self.asf.content
        def cbMousewheel(event):
            # TODO: check if we're the ones to scroll
            #if ( self.winfo_rootx() <= event.x  and event.x <= self.winfo_rootx())
            try:
                self.asf.canvas.yview_scroll(-1*(event.delta//120), "units")
            except TclError:
                pass
        self.asf.canvas.bind_all("<MouseWheel>", cbMousewheel)
        pyschunk.guistuff.widgets.BindMouseWheel( self.asf.canvas, cbMousewheel )

        f_control = Frame( f )

        f_control_top = Frame( f_control )

        self.v_update_output = IntVar()
        self.v_update_output.set( self.bks is BKS_HTTP )

        cuo = Checkbutton( f_control_top, text="Read outputs", variable=self.v_update_output )
        cuo.pack( side=LEFT )
        pyschunk.guistuff.tooltip.cMyToolTip( cuo, "If checked: cyclically read outputs set by another master, write on change only.\nIf unchecked: write our outputs cyclically, even if not changed." )

        def control_authority_combobox_selected( event ):
            print( f"selected {self.v_control_authority.get()} = {control_authority_dict[ self.v_control_authority.get() ]:02x}" )
            self.bks.ctrl_authority = control_authority_dict[ self.v_control_authority.get() ]
            #time.sleep(0.1)
            print( f"new ctrl_authority=0x{self.bks.ctrl_authority:02x}" )

        control_authority_dict = { "SERVICE_CAN_INTERFACE"              : 0,
                                   "FIELDBUS_INTERFACE"                 : 1,
                                   "SERVICE_ETHERNET_INTERRFACE"        : 2,
                                   "SERVICE_CAN_INTERFACE + Tool"       : 0 | 0x90,
                                   "FIELDBUS_INTERFACE + Tool"          : 1 | 0x90,
                                   "SERVICE_ETHERNET_INTERRFACE + Tool" : 2 | 0x90, }
        self.v_control_authority = StringVar()

        control_authority = ttk.Combobox( f_control_top, values=list( control_authority_dict.keys() ), textvariable = self.v_control_authority )
        control_authority.pack( side=LEFT )
        control_authority.bind('<<ComboboxSelected>>', control_authority_combobox_selected )

        self.v_control = StringVar()
        self.v_control.set( "<not connected yet>")
        self.l_control = Label( f_control_top, textvariable=self.v_control, font=font1 )
        self.l_control.pack(side=LEFT, pady=1)
        f_control_top.pack(side=TOP )
        self.change_background_widgets.append( self.l_control )

        def AddBits( f, definitions, do_command ):
            f_bits = Frame( f )
            f_bit1 = Frame( f_bits )
            if ( do_command ):
                f_btn = Frame( f_bits )
                f_bit2 = Frame( f_bits )

                copy_control_left_to_right = Button( f_btn, text="=>", command=self.cbCopyControlToRight, background="#d0d0d0")
                copy_control_left_to_right.pack( side=TOP, fill=Y, expand=1, pady=10, padx=3 )
                pyschunk.guistuff.tooltip.cMyToolTip( copy_control_left_to_right, "Copy prepared control bit set-up area shown left\nto the actual control bits shown right\nand to the grippper in a single step." )

                copy_control_right_to_left = Button( f_btn, text="<=", command=self.cbCopyControlToLeft, background="#d0d0d0")
                copy_control_right_to_left.pack( side=TOP, fill=Y, expand=1, pady=10, padx=3 )
                pyschunk.guistuff.tooltip.cMyToolTip( copy_control_right_to_left, "Copy actual control bits shown right\n to the control bit set-up area shown left." )

            for (i,(bit_name,ivar1,ivar2)) in enumerate( definitions ):
                bit_no = i
                extra_tip = ""
                if ( i == 8 ):
                    extra_tip = "Shortcut: Cursor-Left\n\n"
                elif ( i == 9 ):
                    extra_tip = "Shortcut: Cursor-Right\n\n"

                if ( do_command ):
                    c1 = Checkbutton( f_bit1, variable=ivar1, font=font1, command=lambda bit_no=bit_no,ivar1=ivar1,ivar2=ivar2: self.cbControl1( bit_no, ivar1, ivar2 ) )
                    c1.pack( side=TOP, fill=X, pady=0 )
                    c2 = Checkbutton( f_bit2, text=bit_name, variable=ivar2, font=font1, command=lambda bit_no=bit_no,ivar1=ivar1,ivar2=ivar2: self.cbControl2( bit_no, ivar1, ivar2 ) )
                    c2.bind( "<Control-Button-1>", lambda event=None, bit_no=bit_no,ivar1=ivar1,ivar2=ivar2: self.cbControlAll( event, bit_no, ivar1, ivar2 ) )
                    c2.pack( anchor=W, side=TOP, pady=0 )

                    pyschunk.guistuff.tooltip.cMyToolTip( c1, "Control bit set-up area\n\nThe bits in this row are _NOT_ copied to the gripper right away.\n"
                                                          + "Instead you can set up a number of bits and then use the \"=>\" button\n"
                                                          + "to copy multiple bits at once to the gripper.\n\n"
                                                          + "Bit #%d, masks=(0x%04x, 0x%04x)" % (bit_no,1<<bit_no, 0xffff - (1<<bit_no)) )
                    pyschunk.guistuff.tooltip.cMyToolTip( c2, "Actual control bits of the gripper\n\n"
                                                          + "The check boxes shown reflect the actual state of the corresponding bits in the gripper.\n"
                                                          + "Thus changes performed by a PLC can be observed here.\n"
                                                          + "Additionally you can set the bits here and these are directly copied to the gripper one by one\n\n"
                                                          + "Pro-Tip: Control-Click to a check box changes all actual control bits to the new value\n\n"
                                                          + "%sBit #%d, masks=(0x%04x, 0x%04x)%s" % (extra_tip, bit_no,1<<bit_no, 0xffff - (1<<bit_no), extra_tip) )
                else:
                    c = Checkbutton( f_bit1, text=bit_name, variable=ivar2, font=font1, state=DISABLED, disabledforeground="black" )
                    c.pack( anchor=W, side=TOP, pady=0 )
                    pyschunk.guistuff.tooltip.cMyToolTip( c, "Actual status bits of the gripper\n\nBit#%d, masks=(0x%04x, 0x%04x)" % (bit_no,1<<bit_no, 0xffff - (1<<bit_no)) )
            f_bit1.pack( side=LEFT, fill=BOTH, expand=1, pady=0 )
            if ( do_command ):
                f_btn.pack( side=LEFT, fill=BOTH, expand=1, pady=0 )
                f_bit2.pack( anchor=W, side=LEFT, fill=BOTH, expand=1, pady=0 )
            f_bits.pack( side=TOP, expand=1, pady=0 )

        AddBits( f_control, self.control_bits_definition, True )
#         for (i,(bit_name,ivar)) in enumerate( self.control_bits_definition ):
#             f_controlbit = Frame( f_control )
#             mask = 1 << i
#             c = Checkbutton( f_controlbit, text=bit_name, variable=ivar, command=lambda mask=mask,ivar=ivar: self.cbControl( mask, ivar ) )
#             c.pack( side=LEFT, fill=X )
#             pyschunk.guistuff.tooltip.cMyToolTip( c, "#%d, masks=(0x%04x, 0x%04x)" % (i,1<<i, 0xffff - (1<<i)) )
#             f_controlbit.pack( fill=BOTH, expand=1 )

        self.b_zero_vector_search = Button( f_control, text="Zero-Vector search", command=self.cbZeroVectorSearch )
        self.b_zero_vector_search.pack( side=TOP, fill=X, expand=YES )
        # list of widgets that prevent jogging with cursor keys when focus is in that widget:
        self.do_not_jog = []

        self.v_set_pos = StringVar()
        self.e_set_pos = Entry( f_control, textvariable=self.v_set_pos, justify=LEFT, font=font1 )
        self.e_set_pos.pack( side=TOP, fill=X, expand=YES )
        self.e_set_pos.bind( "<Return>", self.cbSetDesiredPosition )
        pyschunk.guistuff.tooltip.cMyToolTip( self.e_set_pos, "set_pos" )
        self.do_not_jog.append( self.e_set_pos )

        self.v_set_vel = StringVar()
        self.e_set_vel = Entry( f_control, textvariable=self.v_set_vel, justify=LEFT, font=font1 )
        self.e_set_vel.pack( side=TOP, fill=X, expand=YES )
        self.e_set_vel.bind( "<Return>", self.cbSetDesiredVelocity )
        pyschunk.guistuff.tooltip.cMyToolTip( self.e_set_vel, "set_vel" )
        self.do_not_jog.append( self.e_set_vel )

        self.v_desired_force = StringVar()
        self.e_desired_force = Entry( f_control, textvariable=self.v_desired_force, justify=LEFT, font=font1 )
        self.e_desired_force.pack( side=TOP, fill=X, expand=YES )
        self.e_desired_force.bind( "<Return>", self.cbSetGrippingForce )
        pyschunk.guistuff.tooltip.cMyToolTip( self.e_desired_force, "desired_force" )
        self.do_not_jog.append( self.e_desired_force )

        # just for proper alignment with status
        self.e_dummy = Entry( f_control, text="-", justify=LEFT, font=font1, state='readonly' )
        self.e_dummy.pack( side=TOP, fill=X, expand=YES )


        f_control.pack( side=LEFT, fill=BOTH, expand=1 )

        f_status = Frame( f )

        self.v_status = StringVar()
        self.v_status.set( "<not connected yet>")
        self.l_status = Label( f_status, textvariable=self.v_status, font=font1 )
        self.l_status.pack(side=TOP, pady=1)
        self.change_background_widgets.append( self.l_status )

        AddBits( f_status, self.status_bits_definition, False )

        self.v_actual_pos = StringVar()
        self.e_actual_pos = Entry( f_status, textvariable=self.v_actual_pos, justify=LEFT, font=font1, state='readonly'  )
        self.e_actual_pos.pack( side=TOP, fill=X, expand=YES )
        pyschunk.guistuff.tooltip.cMyToolTip( self.e_actual_pos, "actual_pos" )

        self.v_reserved = StringVar()
        self.e_reserved = Entry( f_status, textvariable=self.v_reserved, justify=LEFT, font=font1, state='readonly' )
        self.e_reserved.pack( side=TOP, fill=X, expand=YES )
        pyschunk.guistuff.tooltip.cMyToolTip( self.e_reserved, "reserved" )

        self.v_wrn_code = StringVar()
        self.e_wrn_code = Entry( f_status, textvariable=self.v_wrn_code, justify=LEFT, font=font1, state='readonly' )
        self.e_wrn_code.pack( side=TOP, fill=X, expand=YES )
        pyschunk.guistuff.tooltip.cMyToolTip( self.e_wrn_code, "warning code" )

        self.v_err_code = StringVar()
        self.e_err_code = Entry( f_status, textvariable=self.v_err_code, justify=LEFT, font=font1, state='readonly' )
        self.e_err_code.pack( side=TOP, fill=X, expand=YES )

        self.nb_error_messages_in_tooltip = 10
        def CBErrorCodeTooltip( w ):
            tt = f"System log\n\nLast {self.nb_error_messages_in_tooltip} system log entries:\n"
            for i in range( self.nb_error_messages_in_tooltip ):
                self.bks.sys_msg_req = i
                msg = self.bks.sys_msg_buffer.strip( " \t\0" )
                tt += f"{i:02d}: {msg}\n"
            return tt
        pyschunk.guistuff.tooltip.cSelectiveToolTip( self.e_err_code, CBErrorCodeTooltip )


        f_status.pack( side=LEFT,fill=BOTH, expand=1 )
        f.pack( fill=BOTH, expand=1 )
        self.asf.pack( fill=BOTH, expand=1 )
        self.asf.ShowContent()

        self.v_status_line = StringVar()
        self.v_status_line.set( "" )
        self.l_status_line = Label( master, textvariable=self.v_status_line, fg="blue", font=font3, anchor=W, justify=LEFT, background="#f8f8f8" )
        self.l_status_line.pack(side=TOP, pady=3, fill=X )

        self.master.bind('<KeyPress>', self.cbKeyPress )
        self.master.bind('<KeyRelease>', self.cbKeyRelease )
        self.master.bind('<Escape>', self.cbEscape )

        self.reverse_bit_order = self.bks.fieldbus_type == self.bks.enums[ "fieldbus_type"]["PROFINET"]
        self.last_plc_sync_output = self.bks.plc_sync_output

        self.after( 500, self.cbUpdate )

    def cbZeroVectorSearch(self,event=None):
        self.bks.command_code = eCmdCode.CMD_ZERO_VECTOR_SEARCH

    def Unfocus(self,event=None):
        '''Unfocus text Entry objects so that jogging with cursor keys works again
        '''
        self.master.focus()


    def SetTitle(self):
        title = "BKS-Control/Status @ %s (" % (self.args.host)
        try:
            au = int( self.bks.actual_user )
            title += "Firmware: V" + self.bks.sw_version_txt + ", " + self.bks.sw_build_date + ", " + self.bks.sw_build_time + ", current user: %d (%s)" % (au, self.bks.enums["actual_user"].GetName( au ))
        except Exception:
            title += "Firmware: ?, current user: ?"
        title += ")"
        #print "title=%r" % title
        self.master.title( title )

    def SetStatusline( self, msg, is_error=False ):
        self.v_status_line.set( msg )
        if ( is_error ):
            self.l_status_line.config( foreground="red" )
        else:
            self.l_status_line.config( foreground="blue" )

    def cbEscape(self, event):
        self.SetStatusline( "" )
        self.Unfocus()

    def cbKeyPress(self,event):
        w = self.master.focus_get()
        if w in self.do_not_jog:
            return

        if (event.keysym in ["Right"]):
            self.v_jog_mode_plus.set( 1 )
            self.cbControl2( 9, self.control_bits_definition[9][1], self.v_jog_mode_plus )
        elif (event.keysym in ["Left"]):
            self.v_jog_mode_minus.set( 1 )
            self.cbControl2( 8, self.control_bits_definition[8][1], self.v_jog_mode_minus )

    def cbKeyRelease(self,event):
        if (event.keysym in ["Left"]):
            self.v_jog_mode_minus.set( 0 )
            self.cbControl2( 8, self.control_bits_definition[8][1], self.v_jog_mode_minus )
        if (event.keysym in ["Right"]):
            self.v_jog_mode_plus.set( 0 )
            self.cbControl2( 9, self.control_bits_definition[9][1], self.v_jog_mode_plus )

    def cbSetDesiredPosition( self, event ):
        if ( self.cyclic_data_in_struct ):
            self.bks.plc_sync_output.set_pos = self.last_plc_sync_output.set_pos = int( self.v_set_pos.get() )
        else:
            self.last_plc_sync_output[1] = int32_to_uint32( int( self.v_set_pos.get() ) )
            self.bks.set_value( "plc_sync_output[ 1 ]", value=int32_to_uint32( int( self.v_set_pos.get() ) ) )
        self.SetStatusline( "set_pos is set" )

    def cbSetDesiredVelocity( self, event ):
        if ( self.cyclic_data_in_struct ):
            self.bks.plc_sync_output.set_vel = self.last_plc_sync_output.set_vel = int( self.v_set_vel.get() )
        else:
            self.last_plc_sync_output[2] = int32_to_uint32( int( self.v_set_vel.get() ) )
            self.bks.set_value( "plc_sync_output[ 2 ]", value=int32_to_uint32( int( self.v_set_vel.get() ) ) )
        self.SetStatusline( "set_vel is set" )

    def cbSetGrippingForce( self, event ):
        if ( self.cyclic_data_in_struct ):
            self.bks.plc_sync_output.gripping_force = self.last_plc_sync_output.gripping_force = int( self.v_desired_force.get() )
        else:
            self.last_plc_sync_output[3] = int32_to_uint32( int( self.v_desired_force.get() ) )
            self.bks.set_value( "plc_sync_output[ 3 ]", value=int32_to_uint32( int( self.v_desired_force.get() ) ) )
        self.SetStatusline( "gripping_force is set" )


    def cbControl1( self, i, ivar1, ivar2 ):
        #print "cbControl1, i=%r ivar1.get=%r ivar2.get=%r" % (i, ivar1.get(), ivar2.get())
        pass

    def cbControl2( self, i, ivar1, ivar2 ):
        #print "cbControl2, i=%r ivar1.get=%r ivar2.get=%r" % (i, ivar1.get(), ivar2.get())
        # ivar2 has already the new value after the on-going user triggered change

        if ( ivar2.get() ):
            if ( self.cyclic_data_in_struct ):
                self.last_plc_sync_output.control_dword |= self.GetBitMask(i)
                self.bks.plc_sync_output.control_dword = self.last_plc_sync_output.control_dword
            else:
                self.last_plc_sync_output[0] |= self.GetBitMask(i)
                try:
                    self.bks.set_value( "plc_sync_output[ 0 ]", value=self.last_plc_sync_output[0]  )
                except UnsupportedCommand:
                    self.SetStatusline("Gripper reports unsupported command!", is_error=True )
                    return
        else:
            if ( self.cyclic_data_in_struct ):
                self.last_plc_sync_output.control_dword &= (0xffffffff - self.GetBitMask(i))
                self.bks.plc_sync_output.control_dword = self.last_plc_sync_output.control_dword
            else:
                self.last_plc_sync_output[0] &= (0xffffffff - self.GetBitMask(i))
                self.bks.set_value( "plc_sync_output[ 0 ]", value=self.last_plc_sync_output[0] )
        self.SetStatusline("OK")

    def cbControlAll( self, event, i, ivar1, ivar2 ):
        #print "cbControlAll, event=%r, i=%r ivar1.get=%r ivar2.get=%r" % (event, i,ivar1.get(), ivar2.get())
        # ivar2 has still the old value before the on-going user triggered change
        if ( ivar2.get() ):
            v = 0x00000000
        else:
            v = 0xffffffff

        if ( self.cyclic_data_in_struct ):
            self.bks.plc_sync_output.control_dword = self.last_plc_sync_output.control_dword = v
        else:
            self.last_plc_sync_output[0] = v
            self.bks.set_value( "plc_sync_output[ 0 ]", value=v )

        self.cbUpdate()
        return "break"

    def cbCopyControlToLeft(self):
        for (bit_name,ivar1,ivar2) in self.control_bits_definition:  # @UnusedVariable
            ivar1.set( ivar2.get() )

    def cbCopyControlToRight(self):
        v = 0x00000000
        for (i,(bit_name,ivar1,ivar2)) in enumerate( self.control_bits_definition ):  # @UnusedVariable
            ivar2.set( ivar1.get() )
            if ( ivar1.get() ):
                v |= self.GetBitMask( i )
        if ( self.cyclic_data_in_struct ):
            self.bks.plc_sync_output.control_dword = self.last_plc_sync_output.control_dword = v
        else:
            self.last_plc_sync_output[0] = v
            self.bks.set_value( "plc_sync_output[ 0 ]", value=v )

    def GetBitMask(self,i):
        """Return a bit mask for bit i in Siemens (PLC order), i.e. Bytes ABCD get DCBA
        """
        if ( self.reverse_bit_order ):
            if ( i < 8 ):
                ii = i+24
            elif ( i < 16 ):
                ii = i+8
            elif ( i < 24 ):
                ii = i-8
            else:
                ii = i-24
            return 1 << ii
        else:
            return 1 << i


    def cbUpdate(self):
        try:
            if ( self.v_update_output.get() ):
                plc_sync_output = self.last_plc_sync_output = self.bks.plc_sync_output
            else:
                plc_sync_output = self.last_plc_sync_output
                self.bks.plc_sync_output = self.last_plc_sync_output  # rewrite even if not changed

                #--- update frequency measurement
                # import time
                # now = time.time()
                # try:
                #     dt = now-self.last_time
                #     if ( dt > self.max_dt ):
                #         self.max_dt = dt
                #         print( f"new max_dt={self.max_dt}")
                # except Exception:
                #     self.max_dt = 0
                #     pass
                # self.last_time = now
                #---

            plc_sync_input  = self.bks.plc_sync_input
            if ( self.cyclic_data_in_struct ):
                control = plc_sync_output.control_dword
                status = plc_sync_input.status_dword
                set_pos = plc_sync_output.set_pos
                set_vel = plc_sync_output.set_vel
                desired_force = plc_sync_output.gripping_force
                actual_pos = plc_sync_input.actual_pos
                reserved = plc_sync_input.reserved
                wc = plc_sync_input.wrn_code
                ec = plc_sync_input.err_code
            else:
                control = plc_sync_output[ 0 ]
                status  = plc_sync_input[ 0 ]
                set_pos = uint32_to_int32( plc_sync_output[ 1 ] )
                set_vel = uint32_to_int32( plc_sync_output[ 2 ] )
                desired_force = uint32_to_int32( plc_sync_output[ 3 ] )
                actual_pos = uint32_to_int32( plc_sync_input[ 1 ] )
                reserved = plc_sync_input[ 2 ]
                wc_ec = plc_sync_input[ 3 ]
                ec = wc_ec & 0x0000ffff
                wc = (wc_ec >> 16 ) & 0x0000ffff
            self.v_control.set( "0x%08x" % (control) )
            self.v_status.set( "0x%08x" % (status) )

            for (defs,value) in [(self.control_bits_definition,control), (self.status_bits_definition,status) ]:
                for (i,(n,ivar1,ivar2)) in enumerate(defs):  # @UnusedVariable
                    ivar2.set( (value & self.GetBitMask(i)) != 0 )


            if ( not self.e_set_pos == self.e_set_pos.focus_get() ):
                # only update values if not in focus to allow user to edit
                self.v_set_pos.set( set_pos )
            if ( not self.e_set_vel== self.e_set_vel.focus_get() ):
                self.v_set_vel.set( set_vel )
            if ( not self.e_desired_force== self.e_desired_force.focus_get() ):
                self.v_desired_force.set( desired_force )

            self.v_actual_pos.set( actual_pos )
            if ( reserved > 0x7fffffff ):
                reserved = reserved - 0xffffffff -1
            self.v_reserved.set( reserved )

            try:
                wc_str = self.bks.enums["wrn_code"].GetName(wc, "?" )
            except KeyError:
                wc_str = "?"
            try:
                ec_str = self.bks.enums["err_code"].GetName(ec, "?" )
            except KeyError:
                ec_str = "?"
            self.v_wrn_code.set( "wc=0x%04x (%s)" % (wc, wc_str) )
            self.v_err_code.set( "ec=0x%04x (%s)" % (ec,ec_str) )

            new_background = self.color_connected

        except (requests.ConnectionError, requests.ReadTimeout, minimalmodbus.ModbusException):
            new_background = self.color_disconnected

        if ( self.background != new_background ):
            for w in self.change_background_widgets:
                w.config( background=new_background)
            self.background = new_background

            self.SetTitle()

        self.after( 5, self.cbUpdate )


def main():
    if ( "__file__" in globals() ):
        prog = os.path.basename( globals()["__file__"] )
    else:
        # when runnging as an exe generated by py2exe then __file__ is not defined!
        prog = "bks_status.exe"

    parser = bks_options.cBKSTools_OptionParser( prog=prog,
                                                 description = __doc__ )     # @UndefinedVariable

    args = parser.parse_args()


    #--- Start GUI:
    pyschunk.guistuff.widgets.RunGUI( cstatusApp,
                                      None,
                                      args )


if __name__ == '__main__':
    from pyschunk.tools import attach_to_debugger
    attach_to_debugger.AttachToDebugger( main )


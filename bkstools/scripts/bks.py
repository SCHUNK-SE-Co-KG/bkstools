#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Created on 18.10.2018
#
# @author: Dirk Osswald
'''
Read and/or write parameters of a SCHUNK BKS gripper (like EGI/EGU/EGK) according to the parameters given.|n
|n
Example usage:|n
-  %(prog)s -H 10.49.57.13 --list|n
-  %(prog)s -H 10.49.57.13 actual_pos|n
-  %(prog)s -H 10.49.57.13 actual_pos set_pos=25.4|n
-  %(prog)s -H 10.49.57.13 actual_pos plc_sync_output plc_sync_input system_state internal_params.comm_state -D -10.0 --gpd|n
-  %(prog)s -H COM2 serial_no_num serial_no_num:08x|n
-  %(prog)s -H COM3,12,19200 set_pos=12.34|n
-  %(prog)s -H /dev/ttyUSB0 sw_build_date
'''

import math
import requests

import os
import time
import sys
from pyschunk.tools import peek
import pyschunk.tools.mylogger
from bkstools.bks_lib import hsm_enums, hms, bks_options

from bkstools.bks_lib.bks_base import BKSBase
from bkstools.bks_lib.bks_base_common import Str2Value
from bkstools.bks_lib.debug import Error, Print, Var, ApplicationError, InsufficientAccessRights, InsufficientReadRights, InsufficientWriteRights, g_logmethod  # @UnusedImport
from bkstools.bks_lib.bks_modbus import RepeaterException

logger = pyschunk.tools.mylogger.getLogger( "BKSTools.bks" )
pyschunk.tools.mylogger.setupLogging()
g_logmethod = logger.info


g_file_format_name = dict()
g_file_format_name[ True ] = ".gpd"
g_file_format_name[ False ] = ".csv"

g_time_format_name = dict()
g_time_format_name[ True ] = "absolute"
g_time_format_name[ False ] = "relative"

g_char_offset = 1.7

def ErrorOrWarningCodeToStr( bks, code_int ):
    return (code_int, "0x%02x=%s" % (code_int, bks.enums["err_code"].GetName( code_int, "?" )))

def ApplicationStateToStr( bks, code_int ):  # @UnusedVariable
    application_state   = (code_int & 0x0000ff00) >> 8
    return  (application_state, "0x%02x=%s" % (application_state, hsm_enums.application_state_machine.GetName( application_state, "?" )))

def AnybusStateToStr( bks, code_int ):  # @UnusedVariable
    anybus_state = (code_int & 0x000000ff)
    return  (anybus_state, "0x%02x=%s" % (anybus_state, bks.enums[ "comm_state" ].GetName( anybus_state, "?" )))

def PrintD( msg ):
    """Print msg with time prefix
    """
    date = time.strftime( "%H:%M:%S", time.localtime( time.time() ) )
    Print( "%s %s" % (date, msg) )


def GetHHMMSSms( t, use_comma ):
    r = time.strftime( "%H:%M:%S", time.localtime( t ) )
    if ( use_comma ):
        r += ","
    else:
        r += "."

    r += ("%.3f" % (math.modf( t )[0])) [2:]
    return r


def ListParameters( bks ):
    slist = list( enumerate(bks.data) )
    def sort_by_instance(t):
        (i,d) = t
        return d["instance"]

    slist.sort( key=sort_by_instance)
    for (i,d) in slist:
        try:
            datatype_description = bks.GetDatatypeDescription( i )
            value = bks.get_value(i)#,datatype)
        except InsufficientReadRights:
            value = "? (Insufficient read rights)"
        except RepeaterException as e:
            if ( "device busy" in str( e.original_exception ) ):
                value = f"? ({e.original_exception})"
        Print( "%d instance=0x%04x name=%20s datatype=%s = %r" % (i, d["instance"], d["name"], datatype_description, value) )

def UmlautEncode( msg ):
    r = ""
    for c in msg:
        if c == "ä": c = "ae"
        if c == "ö": c = "oe"
        if c == "ü": c = "ue"
        if c == "Ä": c = "Ae"
        if c == "Ö": c = "Oe"
        if c == "Ü": c = "Ue"
        if c == "ß": c = "ss"
        r += c
    return r

class cRecording( object ):
    def __init__(self, bks, parameternames, parameterformats, do_gpd, do_absolute_time, title, output_file_name_without_suffix, output_directly, cyclically, duration, separator, use_comma ):
        self.bks = bks
        self.parameternames_to_record = parameternames
        self.parameterformats = parameterformats
        self.parameternames_to_print  = list( parameternames ) # we need a copy since we might want to modify parameternames_to_print without modifying parameternames_to_record
        if ( "system_state" in parameternames ):
            self.parameternames_to_print.append( "system_state_application_state" )
            self.parameternames_to_print.append( "system_state_motion_engine_state" )
        self.do_gpd = do_gpd
        self.do_absolute_time = do_absolute_time
        self.title = title
        self.output_file_name_without_suffix = output_file_name_without_suffix
        self.output_file_number = 0
        self.output_directly = output_directly
        self.cyclically = cyclically
        self.duration = duration
        self.t0 = time.time()
        self.t_oldest = self.t0
        self.records = []
        self.sep = separator
        self.use_comma = use_comma
        self.print_header = True

        self.status_dword_bits = [
            ( "ready_for_operation",        bks.sw_ready_for_operation ),
            ( "control_authority",          bks.sw_control_authority ),
            ( "ready_for_shutdown",         bks.sw_ready_for_shutdown ),
            ( "not_feasible",               bks.sw_not_feasible ),
            ( "success",                    bks.sw_success ),
            ( "command_received_toggle",    bks.sw_command_received_toggle ),
            ( "warning",                    bks.sw_warning ),
            ( "error",                      bks.sw_error ),
            ( "emergency_released",         bks.sw_emergency_released ),
            ( "softwarelimit",              bks.sw_softwarelimit ),
            ( "no_workpiece_detected",      bks.sw_no_workpiece_detected ),
            ( "gripped",                    bks.sw_gripped ),
            ( "position_reached",           bks.sw_position_reached ),
            ( "pre_holding",                bks.sw_pre_holding),
            ( "moving_velocity_controlled", bks.sw_moving_velocity_controlled ),
            ( "workpiece_lost",             bks.sw_workpiece_lost ),
            ( "wrong_workpiece_detected",   bks.sw_wrong_workpiece_detected ),
            ( "brake_active",               bks.sw_brake_active ),
         ]
        self.control_dword_bits = [
            ( "fast_stop",                    bks.cw_fast_stop ),
            ( "stop",                         bks.cw_stop ),
            ( "acknowledge",                  bks.cw_acknowledge ),
            ( "prepare_for_shutdown",         bks.cw_prepare_for_shutdown ),
            ( "softreset",                    bks.cw_softreset ),
            ( "emergency_release",            bks.cw_emergency_release ),
            ( "repeat_command_toggle",        bks.cw_repeat_command_toggle ),
            ( "grip_direction",               bks.cw_grip_direction ),
            ( "jog_mode_minus",               bks.cw_jog_mode_minus ),
            ( "jog_mode_plus",                bks.cw_jog_mode_plus ),
            ( "release_work_piece",           bks.cw_release_work_piece ),
            ( "grip_work_piece",              bks.cw_grip_work_piece ),
            ( "move_to_absolute_position",    bks.cw_move_to_absolute_position ),
            ( "move_to_relative_position",    bks.cw_move_to_relative_position ),
            ( "move_velocity_controlled",     bks.cw_move_velocity_controlled ),
            ( "grip_workpiece_with_position", bks.cw_grip_workpiece_with_position ),
            ( "use_gpe",                      bks.cw_use_gpe ),
        ]

        self.special_names_prefix_bits = [
            pyschunk.tools.util.Struct( parametername="plc_sync_input.status_dword", prefix="sw", bits=self.status_dword_bits, value_index=None ),
            pyschunk.tools.util.Struct( parametername="plc_sync_input[0]", prefix="sw", bits=self.status_dword_bits, value_index=None ),
            pyschunk.tools.util.Struct( parametername="plc_sync_output.control_dword", prefix="cw", bits=self.control_dword_bits, value_index=None ),
            pyschunk.tools.util.Struct( parametername="plc_sync_output[0]", prefix="cw", bits=self.control_dword_bits, value_index=None )
        ]

        self.special_names_codes = [
            pyschunk.tools.util.Struct( parameternames=("err_code", "plc_sync_input.err_code"), parametername_to_record=None,           value_index=None, GetStr=ErrorOrWarningCodeToStr, last_value=None, char_offset=None, color='textcolor rgbcolor "red"' ),
            pyschunk.tools.util.Struct( parameternames=("wrn_code", "plc_sync_input.wrn_code"), parametername_to_record=None,           value_index=None, GetStr=ErrorOrWarningCodeToStr, last_value=None, char_offset=None, color='textcolor rgbcolor "orange"' ),
            pyschunk.tools.util.Struct( parameternames=("system_state_application_state",),     parametername_to_record="system_state", value_index=None, GetStr=ApplicationStateToStr,   last_value=None, char_offset=None, color='textcolor rgbcolor "blue"' ),
#            pyschunk.tools.util.Struct( parameternames=("system_state_motion_engine_state",),   parametername_to_record="system_state", value_index=None, GetStr=MotionEngineStateToStr,  last_value=None, char_offset=None, color='textcolor rgbcolor "#228b22"' ), # forestgreen   #006400"' ), #darkgreen
            pyschunk.tools.util.Struct( parameternames=("internal_params.comm_state",),         parametername_to_record="internal_params.comm_state", value_index=None, GetStr=AnybusStateToStr,  last_value=None, char_offset=None, color='textcolor rgbcolor "#043d5d"' ), #HMS corporate identity color
        ]

        self.Prepare_special_names_prefix_bits()

    def Prepare_special_names_prefix_bits(self):
        for parametername in self.parameternames_to_print:
            for o in self.special_names_prefix_bits:
                if ( parametername == o.parametername ):
                    # separate special value into its bits
                    for (name,mask) in o.bits:  # @UnusedVariable
                        o.value_index = self.parameternames_to_record.index( o.parametername ) +1 # +1 since the first index in the record is the time
            for o in self.special_names_codes:
                if ( parametername in o.parameternames ):
                    if ( o.parametername_to_record is None ):
                        o.parametername_to_record = parametername
                    o.value_index = self.parameternames_to_record.index( o.parametername_to_record ) +1 # +1 since the first index in the record is the time


    def GetGPDHeader( self, t_start, output_file_name, use_absolute_time ):
        title = ""
        if ( self.title != "" ):
            title += self.title + '\\n'

        title += "File: %s\\n" % (output_file_name)
        title += "Gripper: host=%s   fieldbus_type=%s   serial_number=%s\\n" % (self.bks.host, self.bks.enums[ "fieldbus_type"].GetName( self.bks.fieldbus_type, "unknown" ), self.bks.serial_no_txt)
        try:
            build_info = self.bks.build_info # cache the build info so that it is queried from the gripper only once
            title += "Firmware: %s B%s %s %s %s %s\\n" % (build_info.buildDescriptor, build_info.buildNumber, build_info.compileDate, build_info.compileTime, build_info.buildUser, build_info.buildHost)
        except AttributeError as e:
            title += "Firmware: ? (%r)" % (e)
        except InsufficientReadRights as e:
            title += "Firmware: ? (%r)" % (e)

        t0date = time.strftime( "%Y-%m-%d %H:%M:%S (%Z)", time.localtime( t_start ) )
        title += "t0 = %s" % (t0date)

        r = """# combined gnuplot commands + data. Use plot.py for easy viewing
## set encoding iso_8859_1
## set grid y2tics
## set key outside
## set title "%s"
# set link y2 via 1.*y inverse 1.*y
## set datafile separator "%s"
""" % (title, self.sep)

        if ( use_absolute_time ):
            prefix_absolute_time = "##"
            prefix_relative_time = "###"
        else:
            prefix_absolute_time = "###"
            prefix_relative_time = "##"

        r += """
#---
# use this for timeline in clock time (hours, minutes, seconds):
%s timecolumn=2
%s set xlabel 'absolue time [UTC]'
%s set xdata time
%s set timefmt "%%s"
%s# set format x "%%Y-%%m-%%d %%H:%%M:%%.3S"  # date + time
%s set format x "%%H:%%M:%%.3S"          # time
%s set xtics rotate by 45 right
#---
""" % ((prefix_absolute_time,)*7)

        r += """
#---
# use this for timeline in relative time since start
%s timecolumn=1
%s set xlabel 'relative time [s]'
#---
""" % ((prefix_relative_time,)*2)

        r = UmlautEncode( r )
        i=4   # with output of time as absolute time and HH:MM:SS.ms
        offset = -1
        char_offset_factor = 1
        for parametername in self.parameternames_to_record:
            r += "## plot using (column(timecolumn)):%d with linespoints title '%s'\n" % (i,parametername)
            i += 1

        for parametername in self.parameternames_to_print:
            for o in self.special_names_prefix_bits:
                if ( parametername == o.parametername ):
                    # separate special value into its bits
                    for (name,mask) in o.bits:  # @UnusedVariable
                        r += "## plot using (column(timecolumn)):(%d+0.8*$%d) with filledcurves y2=%d.1 title '%s.%s' axes x1y2\n" % (offset, i, offset, o.prefix, name)
                        r += "## set y2tics add ('%s.%s' %d)\n" % (o.prefix,name, offset)
                        i += 1
                        offset -= 1
            for o in self.special_names_codes:
                if ( parametername in o.parameternames ):
                    o.char_offset = g_char_offset * char_offset_factor
                    if ( o.parametername_to_record is None ):
                        o.parametername_to_record = parametername
                    r += '## set label "\\n|%s" at graph 1,character %.1f left %s\n' % (parametername.split( "." )[-1], o.char_offset+0.2, o.color)
                    char_offset_factor += 1

        r += "## set bmargin %d\n" % ( int( g_char_offset * char_offset_factor)+2  )

        return r

    def GetCSVHeader( self, t_start, output_file_name ):  # @UnusedVariable
        #--- Printer header line if running cyclically:
        header = ""
        if ( not self.duration is None ):
            header = "rel_time" + self.sep + "abs_time" + self.sep + "time_of_day" + self.sep
            for parametername in self.parameternames_to_record:
                header += parametername + self.sep
            for parametername in self.parameternames_to_print:
                for o in self.special_names_prefix_bits:
                    if ( parametername == o.parametername ):
                        # separate special value into its bits
                        for (name,mask) in o.bits:  # @UnusedVariable
                            header += name + self.sep
            header += "\n"
        return header

    def GetHeader(self, t_start=None, output_file_name="" ):
#         header = self.GetGPDHeader( t_start, output_file_name, self.do_absolute_time ) # we have to call GetGPDHeader() even if gpd is not the output format since the GetGPDHeader() initializes some data
#         if ( not self.do_gpd ):
#             header = self.GetCSVHeader( t_start, output_file_name )
        if ( self.do_gpd ):
            header = self.GetGPDHeader( t_start, output_file_name, self.do_absolute_time ) # we have to call GetGPDHeader() even if gpd is not the output format since the GetGPDHeader() initializes some data
        else:
            header = self.GetCSVHeader( t_start, output_file_name )
        return header

    def GetValue(self, value, nbdigits=6, valueformat="" ):
        if ( value is None ):
            return "NaN"

        if ( valueformat != "" ):
            s = "{0" + valueformat + "}"
            return s.format( value )
        if ( type( value ) is float ):
            s = "%.*f" % (nbdigits,value)
            if ( self.use_comma ):
                s = s.replace(".",",")
            return s
        return value

    def GetValueString(self, name, value, valueformat ):
        if ( self.cyclically ):
            return "%s%s" % (self.GetValue(value, valueformat=valueformat), self.sep)
        else:
            return "%s=%s%s" % (name, self.GetValue(value, valueformat=valueformat), self.sep)


    def GetRecordString( self, record, tstart ):
        s = ""
        sl = ""
        t = record[0] - tstart
        if ( self.cyclically ):
            #s += "%.3f%s" % (t, self.sep)
            s += "%s%s%s%s%s%s" % (self.GetValue(t,3), self.sep, self.GetValue(record[0],3), self.sep, GetHHMMSSms( record[0], self.use_comma ), self.sep )
        for (parametername,value,parameterformat) in zip( self.parameternames_to_record, record[1:], self.parameterformats ):
            s += self.GetValueString( parametername, value, parameterformat )

        for parametername in self.parameternames_to_print:
            #for (special_name,prefix,bits) in self.special_names_prefix_bits:  # @UnusedVariable
            for o in self.special_names_prefix_bits:
                if ( parametername == o.parametername ):
                    # separate special value into its bits
                    if ( len( record ) <= o.value_index ):
                        continue
                    rv = record[ o.value_index ]
                    try:
                        v = int( rv )
                        for (name,mask) in o.bits:
                            if ( v & mask ):
                                bit_value = 1
                            else:
                                bit_value = 0
                            s += self.GetValueString( name, bit_value )

                    except TypeError:
                        # happens when a parameter could not be read (temporarily), e.g. due to missing read rights)
                        for (name,mask) in o.bits:
                            bit_value = None
                            s += self.GetValueString( name, bit_value )

            for o in self.special_names_codes:
                if ( self.do_gpd and parametername in o.parameternames ):
                    if ( len( record ) <= o.value_index ):
                        for o in self.special_names_codes:
                            o.last_value = None   # reset last values, so that state/code labels are reprinted on reconnect
                        continue
                    rv = record[ o.value_index ]
                    try:
                        code_int = int( rv )
                        (new_value,label_str) = o.GetStr( self.bks, code_int)
                    except TypeError:
                        # happens when a parameter could not be read (temporarily), e.g. due to missing read rights)
                        new_value = "NaN"  # when using None then initally unreadable values are not shown but should be
                        label_str = "???"
                    if ( new_value != o.last_value ):
                        sl += '\n## set label "\\n%s" at %.3f,character %.1f point pointtype 9 pointsize 1.5 left %s' % (label_str, t, o.char_offset, o.color)
                        o.last_value = new_value
        return s + sl


    def CheckPurge(self, now ):
        """Check if recorded data can be purged and do so if. This keeps the used memory limited for long running records
        """
        if ( self.duration and ((now - self.t_oldest) > (abs( self.duration ) + 60.0)) ):
            # time to delete some records: args duration plus an extra 60s have been recorded
            #Debug( "Before delete: %d records recorded" % (len(self.records)) )
            for (i,r) in enumerate( self.records ):
                t_record = r[0]
                if ( now - t_record < abs( self.duration ) + 3.0 ):
                    break
            newest_records = self.records[ i: ]
            del self.records
            self.records = newest_records
            self.t_oldest = self.records[0][0]
            #Debug( "After delete: %d records recorded" % (len(self.records)) )


    def AddRecord(self, now ):
        reconnect = False
        values = []
        for parametername in self.parameternames_to_record:
            try:
                value = self.bks.get_value( parametername )

            except requests.RequestException:
                if ( not reconnect ):
                    reconnect = True
                values = [None] * len(self.parameternames_to_record)
                break
            except InsufficientReadRights:
                value = None
            values.append( value )
        record = [time.time()] + values

        if ( self.output_directly ):
            if ( self.print_header ):
                Print( self.GetHeader() )
                self.print_header = False

            Print( self.GetRecordString( record, math.floor( self.t0 ) ) )
        else:
            self.records.append( record )

            self.CheckPurge( now )

        return reconnect

    def SaveOutput(self):
        if ( self.do_gpd ):
            suffix = ".gpd"
        else:
            suffix = ".csv"

        if ( "{n}" in self.output_file_name_without_suffix ):
            while True:
                self.output_file_number += 1
                output_file_name = self.output_file_name_without_suffix.replace( "{n}", "-%02d" % (self.output_file_number) ) + suffix
                if ( not os.path.exists( output_file_name ) ):
                    break
        else:
            output_file_name = self.output_file_name_without_suffix + suffix

        now = time.time()
        if ( self.duration ):
            tstart = max( self.t0, now - abs( self.duration ) )
        else:
            tstart = self.t0

        tstart = math.floor( tstart )


        f = open( output_file_name, "w")
        f.write( self.GetHeader( tstart, output_file_name ) )
        for record in self.records:
            t = record[0]
            if ( t >= tstart ):
                f.write( self.GetRecordString( record, tstart ) + "\n" )
        f.close()
        del f
        Print( "\nSaved recording of %s - %s to file %r" % (time.strftime( "%H:%M:%S", time.localtime( tstart ) ), time.strftime( "%H:%M:%S", time.localtime( now ) ), output_file_name) )

def GetTitleFromPeekInput( peek_input ):
    """Clean up peek_input from unwanted cursor movement stuff and the like
    """
    cleaned = peek_input
    for pattern in ("\x1b\x5b\x44", # cursor left
                    "\x1b\x5b\x41", # cursor up
                    "\x1b\x5b\x43", # cursor right
                    "\x1b\x5b\x42", # cursor down
                    ):
        cleaned = cleaned.replace( pattern, "" )
    return cleaned

#     for c in peek_input:
#         # TODO: instead of just deleting the cursor movements we could actually apply them correctly...
#         if ( c == "\x1b" ):
#
#         print "c=%r 0x%02x" % (c,ord(c))
#         r += c
#     return r


def main():
    if ( "__file__" in globals() ):
        prog = os.path.basename( globals()["__file__"] )
    else:
        # when runnging as an exe generated by py2exe then __file__ is not defined!
        prog = "bks.exe"

    parser = bks_options.cBKSTools_OptionParser( prog=prog,
                                                 description = __doc__ )    # @UndefinedVariable

    parser.add_argument( '-l', '--list',
                         dest="list_parameters",
                         action="store_true",
                         help="Flag, if given then all parameternames of the connected SCHUNK BKS gripper will be printed" )
    parser.add_argument( 'other', nargs='*',
                         help="""list of space separated firmware parameter names to read and/or write, e.g. 'actual_pos set_pos=4.5'.
                         |n|n
                         For structured parameters you can access a single element for reading or writing by giving the name as PARAMETERNAME.ELEMENTNAME
                         like in 'plc_sync_input.actual_velocity' or 'plc_sync_output.control_dword=0x1245678'.
                         For structured parameters you can access the whole parameter for writing by giving the value as a tuple like in
                         'plc_sync_output="(11,22,33,44)"'. The number of values in the tuple must match the number of elements in
                         the structured parameter.
                         |n|n
                         By adding ":FORMAT" the output format of a parameter can changed. For example to output a value as hex with leading zeros
                         add ":04x" to the parametername. The syntax for the FORMAT is the one used for python f-strings or string.format().
                         |n|n
                         Try option --list to get a list of all parameter names.""" )
    parser.add_argument( '-p', '--period',
                         dest="period",
                         default=0.0, type=float,
                         help="""Period in s for cyclic processing of parameters. Default is 0.0 to cycle as fast as possible.""" )
    parser.add_argument( "-D", "--duration",
                           dest="duration",
                           type=float,
                           default=None,
                           help="""The duration for recording in s. Default is None meaning run only once.
                           Setting this to 0.0 means record forever.
                            |n|n
                           Positive numbers make the recording stop after the specified time.
                            |n|n
                           Negative numbers make the recording run forever, but on save only the last -DURATION seconds are written to the output file.
                           (The latter is usefull for GPD recording mostly.)""" )

    parser.add_argument( '--gpd',
                         dest="do_gpd",
                         action="store_true",
                         help="""Flag, if set then the output format is set to gpd (GNUplot data). Only usefull with -D set to non-None.
                         The default output format is csv (Character Separated Values).
                         With negative duration -D this can be changed interactively after start.""" )
    parser.add_argument( '--absolute_time',
                         dest="do_absolute_time",
                         action="store_true",
                         help="""Flag, if set then the X axis of the output plot uses absolute time in UTC. Default is to use relative time bbksnning from the start of measurement. Only used with GPD data format.
                         With negative duration -D this can be changed interactively after start.""" )
    parser.add_argument( '--gpdtitle',
                         dest="gpd_title",
                         default="", type=str,
                         help="""User defined title of the gpd plot, see --gpd. This will be prepended to the build info and recording date.
                         With negative duration -D this can be changed interactively after start.""" )
    parser.add_argument( "-o", "--output",
                           dest="output_file_name_without_suffix",
                           type=str,
                           default="out{n}",
                           help="""The name of the output file to write to without suffix. Default is %(default)s.
                           If "{n}" is part of the file name then it will be replaced with an increasing number starting with 1.
                           Usefull when the save-and-keep-recording is used. When --gpd is used a ".gpd" suffix will be appended, else a ".csv" suffix.""" )
    parser.add_argument( "--separator",
                           dest="separator",
                           type=str,
                           default=" ",
                           help="""The separator to put between fields in the output. Default is "%(default)s".
                           For easy EXCEL import you might want to set this to ";".""" )
    parser.add_argument( '--use_comma',
                         dest="use_comma",
                         action="store_true",
                         help="""Flag, if set then floating point numbers will be output with a comma instead of a dot as decimal point.
                         Usefull for CSV output and easy import into German EXCEL or the like.""" )

    args = parser.parse_args()

    if ( not args.list_parameters and len(args.other)==0 ):
        Error( "No parameter names given to read or write. Try --help!" )
        exit(1)

    # determine parameters to get and set
    parameternames_get = []
    parameterformats   = []
    parameternames_set = []
    for a in args.other:
        if ( "=" in a ):
            parameternames_set.append( a )
        else:
            if ( ":" in a ):
                a_split =  a.split(":")
                parameternames_get.append( a_split[0] )
                parameterformats.append( ":" + a_split[1] )
            else:
                parameternames_get.append( a )
                parameterformats.append( "" )

    maxage_s = 5*60.0
    if ( args.force_reread ):
        maxage_s = 0.0

    #--- Create the BKS object:
    bks = BKSBase( args.host, maxage_s, debug=args.debug, repeater_timeout=args.repeat_timeout, repeater_nb_tries=args.repeat_nb_tries )

    #ft = bks.enums[ "fieldbus_type"].GetName( bks.fieldbus_type, "unknown" )  # @UnusedVariable

    #--- List all parameter names if requested:
    if ( args.list_parameters ):
        ListParameters( bks )
        sys.exit(0)

    def PrintHelp( current_file_format, current_time_format ):
        Print( "\nRecording with %.1fs recording window" % (args.duration) )
        Print( "  - Press H to reprint this short help" )
        Print( "  - Press Q (+optional_plot_title) + Return to save recording and quit" )
        Print( "  - Press S (+optional_plot_title) + Return to save recording and continue recording" )
        Print( "  - Press CTRL-C to quit without saving" )
        Print( "  - Current output format is %r.\n    Press G + Return to switch to GPD or C + Return to CSV" % (current_file_format) )
        if ( current_file_format == ".gpd" ):
            Print( "  - Current time format is %r.\n    Press A + Return to switch to absolute or R + Return to relatie time" % (current_time_format) )

    #--- Enter loop to print all selected parameters once or cyclically:
    t0 = time.time()
    if ( args.duration is None ):
        # run once
        tend = t0
        output_directly = True
        cyclically = False
    elif ( args.duration < 0.0):
        # record forever but report only last args.duration seconds
        tend = t0 + 24.0*3600.0 # 24h is like forever, right?
        output_directly = False
        cyclically = True
        PrintHelp( g_file_format_name[ args.do_gpd ], g_time_format_name[ args.do_absolute_time ] )
        PrintD( "Recording started, connected to %s." % (args.host) )
        peek.Start()

    elif ( args.duration == 0.0):
        # record forever
        tend = t0 + 24.0*3600.0 # 24h is like forever, right?
        output_directly = True
        cyclically = True
    elif ( args.duration > 0.0):
        # record for args.duration seconds only
        tend = t0 + args.duration
        output_directly = True
        cyclically = True
        Print( "\n" )
        PrintD( "Starting to record for %.1fs" % (args.duration) )


    recording = cRecording( bks, parameternames_get, parameterformats, args.do_gpd, args.do_absolute_time, args.gpd_title, args.output_file_name_without_suffix, output_directly, cyclically, args.duration, args.separator, args.use_comma )

    reconnecting = False
    while True:
        now = time.time()
        if ( recording.AddRecord( now ) ):
            # not connected, try to reconnect
            if ( not reconnecting ):
                PrintD( "Lost connection to %s. Trying to reconnect..." % (args.host) )
                reconnecting = True
        elif (reconnecting):
            PrintD( "Reconnected to %s." % (args.host) )
            reconnecting = False


        for a in parameternames_set:
            (parametername,value) = a.split("=")
            datatype = bks.data[bks.GetIndexOfName( parametername )]["datatype"]
            if ( (len(datatype) != 1)  or (datatype[0] != hms.HMS_Datatypes.ABP_CHAR) ):
                value = Str2Value( value )
            bks.set_value( parametername, value=value )

        if ( peek.InputAvailable() ):
            peek_input = peek.Getch()
            # remark:
            # - when run from a cygwin mintty console then peek_input now contains the full input including cursor movement commands.
            # - when run from a native windows console then we have to peek for
            #   more input, but that will yield the final input from the user,
            #   including inserts, deletions, history retrieval. Good.
            #print "peek_input=%r" % (peek_input)
            c = peek_input[0]
            if ( c in ["q", "Q", "s", "S"] ):
                while ( peek.InputAvailable() ):
                    peek_input += peek.Getch()
                title = GetTitleFromPeekInput( peek_input[1:-1] )
                if ( len(title) > 0 ):
                    recording.title = title
                recording.SaveOutput()

                if ( c in ["q", "Q"] ):
                    break
            if ( c in ["g", "G"] ):
                recording.do_gpd = True
                recording.use_comma = False # makes no sense for GPD
                PrintD( "Switched output format to GPD")
            if ( c in ["c", "C"] ):
                recording.do_gpd = False
                recording.use_comma = args.use_comma
                PrintD( "Switched output format to CSV")
            if ( c in ["a", "A"] ):
                recording.do_absolute_time = True
                PrintD( "Switched GPD time format to absolute")
            if ( c in ["r", "R"] ):
                recording.do_absolute_time = False
                PrintD( "Switched GPD time format to relative")
            if ( c in ["h", "H"] ):
                PrintHelp( g_file_format_name[ recording.do_gpd ], g_time_format_name[ recording.do_absolute_time ])
            peek.Clear()

        if ( args.period > 0.0 ):
            time.sleep( args.period )

        if ( now >= tend ):
            break


if __name__ == '__main__':
    try:
        from pyschunk.tools import attach_to_debugger
        attach_to_debugger.AttachToDebugger( main )
    except KeyboardInterrupt:
        PrintD( "Interrupted by user." )
    #main()

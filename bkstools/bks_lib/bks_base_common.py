# -*- coding: UTF-8 -*-
'''
Created on 2022-03-07

@author: Dirk Osswald

@brief Provides the basic BKSBaseCommon class for generic access to SCHUNK BKS grippers
'''


import struct

from pyschunk.generated.generated_enums import eCmdCode, eErrorCode  # @UnusedImport
from pyschunk.tools.util import GetPersistantDict, enum
from bkstools.bks_lib import hms
from bkstools.bks_lib.debug import Print, Error, Debug, Var, ApplicationError, InsufficientAccessRights, InsufficientReadRights, InsufficientWriteRights, ControlledFromOtherChannel, ServiceNotAvailable, UnsupportedCommand  # @UnusedImport

# The following Python module must be imported explicitly to be able to generate
# standalone exes with py2exe on Python 3
import dbm.dumb  # @UnusedImport

import re

class Struct(object):
    """Create an instance with argument=value slots.
    This is for making a lightweight object whose class doesn't matter.
    When using AddOrdered then the represention of self is given with the subelements ordered as the order of the calls to AddOrdered"""
    def __init__(self, **entries):
        self.__dict__.update(entries)
        self._ordered_names = []
        self._bks_obj_infos = {}

    def AddOrdered( self, name, value, bks_obj, index, element_index ):
        self._ordered_names.append( name )
        self._bks_obj_infos[ name ] = (bks_obj, index, element_index)
        self.__dict__[ name ] = value

        setattr( Struct,
                 name,
                 property( lambda self: self.get_value( name ),
                           lambda self,value: self.set_value( name, value ) ) )

    def get_value(self, name ):
        #print "Struct.get_value %s" % name
        return self.__dict__[name]

    def set_value(self, name, value):
        #print "Struct.set_value %s = %r" % (name, value)
        (bks_obj, index, element_index) = self._bks_obj_infos[ name ]
        bks_obj.set_value( index_or_name=index, value=value, elementindices=element_index )
        self.__dict__[name] = value

    def __cmp__(self, other):
        def CmpReplacement( a, b ):
            if ( a < b ):
                return -1
            if ( a == b ):
                return 0
            return 1
        if isinstance(other, Struct):
            return CmpReplacement( self.__dict__, other.__dict__ )
        else:
            return CmpReplacement( self.__dict__, other )

    def __repr__(self):
        #args = ['%s=%s' % (k, repr(v)) for (k, v) in vars(self).items()]
        args = ['%s=%s\n' % (k, self.__dict__[k]) for k in self._ordered_names ]
        return 'Struct(%s)' % ', '.join(args)


def make_property_name( name ):
    """Return a name suitable as a property name:
    - Converts spaces to _
    """
    return name.replace(" ", "_")


def chunkstring(string, length):
    """Return a tuple of strings of length length from string string
    """
    return (string[0+i:length+i] for i in range(0, len(string), length))


def Str2Value( valuestr ):
    '''Convert value valuestr given as string 'reasonably' into a value:
    - 0x123 or 0Xabc will be parsed as a hex number yielding an unsigned integer
    - 123.45 or 1e5 or 1E-3 will be parsed as a float number
    - 123 will be parsed as an integer
    - CMD_REFERENCE will yield 146, the SMP command code 0x92
    '''
    try:
        return eval( valuestr, {"__builtins__":None}, {} )
    except SyntaxError:
        return valuestr
    except (NameError, TypeError):
        #uninterpretable string

        # try SMP command codes
        try:
            return eCmdCode[valuestr]
        except KeyError:
            return valuestr

def uint32_to_int32( uint32 ):
    """return the value of uint32 interpreted as an int32
    """
    if ( uint32 > 0x7fffffff ):
        return uint32 - 0x100000000
    return uint32

def int32_to_uint32( int32 ):
    """return the value of int32 interpreted as an uint32
    """
    if ( int32 < 0 ):
        return int32 + 0x100000000
    return int32

def Reverse( hex_string ):
    """reverse a hex string "01234" -> "3401"
    """
    r = ""
    for i in range( 0, len( hex_string ), 2 ):
        r = hex_string[i:i+2] + r
    return r

class BKSBaseCommon(object):

    def GetSettings(self, host):
        # On linux and when using Grippes with Modbus-RTU comunication the host
        # might be a serial port like /dev/ttyUSB0, which is not adequate as file name
        # So modify that first:
        hostsuffix = host.replace( "/", "_" )
        return GetPersistantDict( name=".bks3." + hostsuffix )

    def __init__(self, host, max_age_in_s=5*60, debug=False ):
        self.host = host
        self.max_age_in_s = max_age_in_s
        self.debug = debug

        #t0=time.time()

        self.enums = dict()
        self.name_to_index = dict()
        self.inst_to_index = dict()
        self.failed_requests = dict()

        # for now this is not available via webinterface or via hsm_enums, so enter explicitly:
        anybus_state_enum = enum( SETUP=0, NW_INIT=1, WAIT_PROCESS=2, IDLE=3, PROCESS_ACTIVE=4, ERROR=5, EXCEPTION=7 )
        self.enums[ "comm_state" ] = anybus_state_enum

        self.settings = self.GetSettings(host)
        self.data = self.settings.setdefault( "data", None )

    def UpdateEnum( self, d ):
        raise NotImplementedError() # derived classes must implement this

    def SetAttributes(self, extra_parameter_dicts=[] ):
        #t1=time.time()
        #Print("init read took %fs" % (t1-t0))

        ###
        # FIXME: this is a wild hack necessary since meta-info cannot be read via modbus
        if ( self.data is None ):
            return

        for d in extra_parameter_dicts:
            self.data.append( d )

        ###

        #Print( Var( "self.data" ) )
        for (i,d) in enumerate( self.data ) :
            # d is a dict like
            #  { u'default': None,
            #    u'elementname': None,
            #    u'name': u'command_code',
            #    u'descriptor': [19],
            #    u'datatype': [5],
            #    u'max': None,
            #    u'min': None,
            #    u'numelements': 1,
            #    u'instance': 32002,
            #    u'numsubelements': None}

            #if ( d["name"] == "start_firmware_flash" ): #errorneous for now (2019-01-25 no longer needed?)
            #    continue

            if ( len( d["datatype"] ) == 1 ):
                datatype = d["datatype"][0]
            else:
                # for structures we cannot set the datatype
                datatype = None
            #Print( "%d name=%s datatype=%r(%s) = %r" % (i,d["name"], datatype, hms.HMS_Datatypes.GetName(datatype), self.get_value(i,datatype)) )
            self._add_property( d["name"], i, datatype, d["instance"] )

            if ( datatype == hms.HMS_Datatypes.ABP_ENUM ):
                self.UpdateEnum( d )

            if ( d["name"] == "fieldbus_input" or d["name"] == "fieldbus_input_frame" or d["name"] == "plc_sync_input" ):
                # its an EGL-C or an Ethernet/IP brick where the synchronous data is named differently.
                # make it available with the EGI name to make scripts like bks_status and bks_jog work:
                self._add_property( "plc_sync_input", i, datatype )

            if ( d["name"] == "fieldbus_output" or d["name"] == "fieldbus_output_frame" or d["name"] == "plc_sync_output" ):
                # its an EGL-C where the synchronous data is named differently.
                # make it available with the EGI name to make scripts like bks_status and bks_jog work:
                self._add_property( "plc_sync_output", i, datatype )

            if ( d["name"] == "system_state" ):
                setattr( self.__class__,
                         "system_state_application_state",
                         property( lambda self: (self.system_state &0x0000ff00) >>8 ) ) #(no setter needed since read only)
                setattr( self.__class__,
                         "system_state_motion_engine_state",
                         property( lambda self: (self.system_state &0x000000ff) ) )     #(no setter needed since read only)

    def SetupControlword( self ):
        #-- The bits of the control word
        self.cw_fast_stop                = self.PLCReorder( 1 << 0 )
        self.cw_stop                     = self.PLCReorder( 1 << 1 )
        self.cw_acknowledge              = self.PLCReorder( 1 << 2 )
        self.cw_prepare_for_shutdown     = self.PLCReorder( 1 << 3 )
        self.cw_softreset                = self.PLCReorder( 1 << 4 )
        self.cw_emergency_release        = self.PLCReorder( 1 << 5 )
        self.cw_repeat_command_toggle    = self.PLCReorder( 1 << 6 )
        self.cw_grip_direction           = self.PLCReorder( 1 << 7 )
        self.cw_jog_mode_minus           = self.PLCReorder( 1 << 8 )
        self.cw_jog_mode_plus            = self.PLCReorder( 1 << 9 )
        self.cw_reserved10               = self.PLCReorder( 1 << 10 )
        self.cw_release_work_piece       = self.PLCReorder( 1 << 11 )
        self.cw_grip_work_piece          = self.PLCReorder( 1 << 12 )
        self.cw_move_to_absolute_position= self.PLCReorder( 1 << 13 )
        self.cw_move_to_relative_position= self.PLCReorder( 1 << 14 )
        self.cw_move_velocity_controlled = self.PLCReorder( 1 << 15 )
        self.cw_grip_workpiece_with_position = self.PLCReorder( 1 << 16 )
        self.cw_use_gpe                  = self.PLCReorder( 1 << 31 )

    def SetupStatusword( self ):
        #-- The bits of the status word
        self.sw_ready_for_operation        = self.PLCReorder( 1 << 0 )
        self.sw_control_authority          = self.PLCReorder( 1 << 1 )
        self.sw_ready_for_shutdown         = self.PLCReorder( 1 << 2 )
        self.sw_not_feasible               = self.PLCReorder( 1 << 3 )
        self.sw_success                    = self.PLCReorder( 1 << 4 )
        self.sw_command_received_toggle    = self.PLCReorder( 1 << 5 )
        self.sw_warning                    = self.PLCReorder( 1 << 6 )
        self.sw_error                      = self.PLCReorder( 1 << 7 )
        self.sw_emergency_released         = self.PLCReorder( 1 << 8 )
        self.sw_softwarelimit              = self.PLCReorder( 1 << 9 )
        self.sw_reserved10                 = self.PLCReorder( 1 << 10 )
        self.sw_no_workpiece_detected      = self.PLCReorder( 1 << 11 )
        self.sw_gripped                    = self.PLCReorder( 1 << 12 )
        self.sw_position_reached           = self.PLCReorder( 1 << 13 )
        self.sw_pre_holding                = self.PLCReorder( 1 << 14 )
        self.sw_moving_velocity_controlled = self.PLCReorder( 1 << 15 )
        self.sw_workpiece_lost             = self.PLCReorder( 1 << 16 )
        self.sw_wrong_workpiece_detected   = self.PLCReorder( 1 << 17 )
        self.sw_brake_active               = self.PLCReorder( 1 << 31 )

    def PLCReorder( self, v32 ):
        return v32

    def _add_property(self, name, i, datatype, inst=0 ):
        setattr( self.__class__,
                 make_property_name( name ),
                 property( lambda self: self.get_value( i, datatype),
                           lambda self,value: self.set_value( i, datatype, value ) ) )
        self.name_to_index[ name ] = i
        self.inst_to_index[ inst ] = i


    def GetIndexOfName( self, name ):
        try:
            return self.name_to_index[ name ]
        except KeyError:
            try:
                instance = eval( name, {}, {} )
                if ( type( instance ) is int ):
                    return self.GetIndexOfInstance(instance)
                else:
                    raise ApplicationError( f"name {name!r} is not a known parameter name nor a valid parameter id. Giving up!")
            except (KeyError, NameError):
                raise ApplicationError( f"name {name!r} is not a known parameter name nor a valid parameter id. Giving up!")


    def GetIndexOfInstance(self, inst):
        return self.inst_to_index[inst]

    def GetSingleValue( self, datatype, data ):
        if ( datatype == hms.HMS_Datatypes.ABP_FLOAT ):
            if ( self.reverse_data ):
                v32 = int( Reverse(data), 16 )
            else:
                v32 = int( data, 16 )
            #packed = chr( v32 & 0x000000ff ) + chr( (v32>>8) & 0x000000ff ) + chr( (v32>>16) & 0x000000ff ) + chr( (v32>>24) & 0x000000ff )
            packed = bytes( (v32 & 0x000000ff,
                             (v32>>8) & 0x000000ff,
                             (v32>>16) & 0x000000ff,
                             (v32>>24) & 0x000000ff) )

            return struct.unpack("f", packed)[0]

        if ( datatype in (hms.HMS_Datatypes.ABP_ENUM,
                          hms.HMS_Datatypes.ABP_UINT8,
                          hms.HMS_Datatypes.ABP_UINT16,
                          hms.HMS_Datatypes.ABP_UINT32,
                          hms.HMS_Datatypes.ABP_UINT64) ):
            try:
                if ( self.reverse_data ):
                    return int( Reverse(data), 16 )
                else:
                    return int( data, 16 )
            except TypeError as e:  # @UnusedVariable
                #raise ApplicationError( "get_value failed for data = %r with %r" % (data,e))
                # fails for 80
                # debug.ApplicationError: get_value failed for data = {u'error': 9} with TypeError("int() can't convert non-string with explicit base",
                return data
        if ( datatype in (hms.HMS_Datatypes.ABP_SINT8,
                          hms.HMS_Datatypes.ABP_SINT16,
                          hms.HMS_Datatypes.ABP_SINT32,
                          hms.HMS_Datatypes.ABP_SINT64) ):
            if ( self.reverse_data ):
                v = int( Reverse(data), 16 )
            else:
                v = int( data, 16 )
            if ( datatype == hms.HMS_Datatypes.ABP_SINT8 and v >= 0x80 ):
                v = -((v-1) ^ 0xff)
            if ( datatype == hms.HMS_Datatypes.ABP_SINT16 and v >= 0x8000 ):
                v = -((v-1) ^ 0xffff)
            if ( datatype == hms.HMS_Datatypes.ABP_SINT32 and v >= 0x80000000 ):
                v = -((v-1) ^ 0xffffffff)
            if ( datatype == hms.HMS_Datatypes.ABP_SINT64 and v >= 0x8000000000000000 ):
                v = -((v-1) ^ 0xffffffffffffffff)
            return v

        if ( datatype == hms.HMS_Datatypes.ABP_BOOL ):
            return bool( int( data, 16 ) )

        if ( datatype == hms.HMS_Datatypes.ABP_CHAR ):
            s = ""
            for cc in chunkstring( data, 2 ):
                c = chr( int( cc, 16 ) )
                if ( c == "\x00" ):
                    break
                s += c
            return s
        raise ApplicationError( "Unknown datatype %d (%s)" % (datatype,hms.HMS_Datatypes.GetName( datatype ) ) )

    def MakeIndex( self, index_or_name ):
        if ( type( index_or_name ) is str ):
            return self.GetIndexOfName( index_or_name )
        else:
            return index_or_name

    def get_value( self, index_or_name, datatype=None ):
        #print "get-value %r %r" % (index_or_name, datatype)
        if ( type( index_or_name ) is str  and  "." in index_or_name ):
            (name,subname) = index_or_name.split(".")
            sv = self.get_value( name )
            return sv.__dict__[ subname ]

        if ( type( index_or_name ) is str  and  "[" in index_or_name ):
            mob = re.match( "(\w+)\[(.+)\]", index_or_name )
            elementindex  = Str2Value( mob.group(2) )
            index_or_name = Str2Value( mob.group(1) )

            # HMS web interface does not support reading a single element of an array
            value_all = self.get_value( index_or_name, datatype )
            return value_all[ elementindex ]

        index = self.MakeIndex( index_or_name )

        if ( datatype is None ):
            if ( len( self.data[index]["datatype"] ) == 1 ):
                datatype = self.data[index]["datatype"][0]
            else:
                return self.GetStructuredValue( index )

        return self.UpdateValue( index_or_name, datatype, index )

    def UpdateValue( self, index_or_name, datatype, index ):
        raise NotImplementedError() # must be implemented by drived class

    def GetDatatypeDescription(self, index_or_name ):
        index = self.MakeIndex( index_or_name )

        # a structure:
        # 104    dict: {u'default': None, u'elementname': [u'err_code', u'timestamp', u'msg'], u'name': u'error_log_entry', u'descriptor': [1, 1, 1], u'datatype': [8, 6, 7], u'max': u'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', u'min': u'000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', u'numelements': 3, u'instance': 32833, u'numsubelements': [1, 1, 64]}
        #     u'datatype' (56064216)    <type 'list'>: [8, 6, 7]
        #     u'default' (56012552)    NoneType: None
        #     u'descriptor' (56010512)    <type 'list'>: [1, 1, 1]
        #     u'elementname' (56010032)    <type 'list'>: [u'err_code', u'timestamp', u'msg']
        #     u'instance' (56065176)    int: 32833
        #     u'max' (56011496)    unicode: FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        #     u'min' (56009792)    unicode: 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
        #     u'name' (56009264)    unicode: error_log_entry
        #     u'numelements' (56064888)    int: 3
        #     u'numsubelements' (56012384)    <type 'list'>: [1, 1, 64]
        #     __len__    int: 10
        #
        # an array:
        # 109    dict: {u'default': None, u'elementname': None, u'name': u'statistic_counters', u'descriptor': [3], u'datatype': [6], u'max': u'FFFFFFFF', u'min': u'00000000', u'numelements': 18, u'instance': 32880, u'numsubelements': None}
        #     u'datatype' (55920904)    <type 'list'>: [6]
        #     u'default' (55921744)    NoneType: None
        #     u'descriptor' (55918768)    <type 'list'>: [3]
        #     u'elementname' (55918936)    NoneType: None
        #     u'instance' (55921792)    int: 32880
        #     u'max' (55922104)    unicode: FFFFFFFF
        #     u'min' (55919440)    unicode: 00000000
        #     u'name' (55921048)    unicode: statistic_counters
        #     u'numelements' (55921864)    int: 18
        #     u'numsubelements' (55921360)    NoneType: None
        #     __len__    int: 10
        #
        # a normal:
        # 110    dict: {u'default': u'02BC', u'elementname': None, u'name': u'brake_test_duration_time', u'descriptor': [3], u'datatype': [5], u'max': u'0384', u'min': u'01F4', u'numelements': 1, u'instance': 32896, u'numsubelements': None}
        #     u'datatype' (55920184)    <type 'list'>: [5]
        #     u'default' (55922176)    unicode: 02BC
        #     u'descriptor' (55920016)    <type 'list'>: [3]
        #     u'elementname' (55919728)    NoneType: None
        #     u'instance' (55918720)    int: 32896
        #     u'max' (55920952)    unicode: 0384
        #     u'min' (55920832)    unicode: 01F4
        #     u'name' (55919104)    unicode: brake_test_duration_time
        #     u'numelements' (55921312)    int: 1
        #     u'numsubelements' (55922272)    NoneType: None
        #     __len__    int: 10

        if ( len( self.data[index]["datatype"] ) > 1 ):
            dtd = "Structure{"
            sep = ""
            for ei in range( self.data[index]["numelements"] ):
                datatype       = self.data[index]["datatype"][ei]
                numsubelements = self.data[index]["numsubelements"][ei]
                idtd = "%r(%s)" % (datatype, hms.HMS_Datatypes.GetName(datatype))

                dtd += sep
                sep = ","
                if ( numsubelements > 1 ):
                    dtd += "Array[%d] of %s" % (numsubelements, idtd)
                else:
                    dtd += idtd
            return dtd + "}"
        else:
            datatype = self.data[index]["datatype"][0]
            dtd = "%r(%s)" % (datatype, hms.HMS_Datatypes.GetName(datatype))

            if (  self.data[index]["numelements"] > 1 ):
                return "Array[%d] of %s" % (self.data[index]["numelements"], dtd)
            return dtd



# -*- coding: UTF-8 -*-
'''
Created on 2022-03-07

@author: Dirk Osswald

@brief Provides the class for generic access to SCHUNK BKS grippers via the HTTP/JSON webinterface
'''


import requests
import struct

from pyschunk.generated.generated_enums import eCmdCode, eErrorCode  # @UnusedImport
from pyschunk.tools.util import enum
from bkstools.bks_lib import hms
from bkstools.bks_lib.debug import Print, Error, Debug, Var, ApplicationError, InsufficientAccessRights, InsufficientReadRights, InsufficientWriteRights, ControlledFromOtherChannel, ServiceNotAvailable, UnsupportedCommand  # @UnusedImport
import time
from bkstools.bks_lib.bks_base_common import BKSBaseCommon, Struct, int32_to_uint32, Reverse

import re
import sys
import pprint

class BKS_HTTP(BKSBaseCommon):
    """Class where instances allow access to SCHUNK BKS grippers via the HTTP/JSON webinterface.

    The actually available parameters are read from the gripper at construction time
    and are made available as properties of the instance object.
    The parameter list read from the gripper is cached persistently on hard disc. The cached values
    are used if available and if they are not older than max_age_in_s (default: 5 minutes)
    """
    def __init__(self,host, max_age_in_s=5*60, debug=False ):
        BKSBaseCommon.__init__( self, host, max_age_in_s, debug )

        #                                                     1   1
        self.rex_result = re.compile( b'\s*{\s*"result"\s*:\s*(\d+)\s*}\s*' )

        self._session = requests.Session() # this will reuse connections to increase performance and avoid error 10048

        self.timeout = (5,0.75) # (timeout_for_initial_connect, timeout_for_consecutive_reads) according to http://docs.python-requests.org/en/master/user/advanced/#timeouts

        r = self.session_get( url = "http://" + self.host + "/adi/info.json", timeout=self.timeout )
        self.CheckResponse( r, "get" )
        self.reverse_data = (r.json()["dataformat"] == 0)

        self.SetAttributes()
        self.UpdateMetadata()

        self.SetFieldbus()

        self.SetupControlword()
        self.SetupStatusword()


    def UpdateMetadata(self):
        now = time.time()
        data_timestamp = self.settings.setdefault( "data_timestamp", 0 )
        if ( self.data is None or now - data_timestamp > self.max_age_in_s ):
            r = self.session_get( url = "http://" + self.host + "/adi/metadata2.json?offset=0&count=256", timeout=self.timeout )
            self.CheckResponse( r, "get" )
            self.data = r.json()
            self.settings[ "data" ] = self.data
            self.settings[ "data_timestamp" ] = now
            self.settings.sync()

    def UpdateEnum(self, d):
        name = str(d["name"])
        now = time.time()
        enum_timestamp = self.settings.setdefault( "%s.enum_timestamp" % (name), 0 )
        self.enums[ name ] = self.settings.setdefault( "%s.enum" % (name), None )

        if ( self.enums[ name ] is None or now - enum_timestamp > self.max_age_in_s ):
            r = self.session_get( url = "http://" + self.host + "/adi/enum.json?inst=%d" % (d["instance"]), timeout=self.timeout )
            try:
                self.CheckResponse( r, "get" )
                enum_data = r.json()
            except ApplicationError as e:
                sys.stderr.write( "Failed to read enums for instance %d=0x%04x: %r (ignored)\n" % (d["instance"],d["instance"],e))
                enum_data = []

            # enum_data is a list of elemntes like:
            #   dict: {u'string': u'ERROR_NONE', u'value': 0}
            new_enum = enum()
            for le in enum_data:
                if ( str(le["string"]) != "" ):  #unused enum values are reported as "", so ignore these to avoid KeyError
                    new_enum.Add( str(le["string"]), le["value"] )

            self.enums[ name ] = new_enum

            self.settings[ "%s.enum" % (name) ] = new_enum
            self.settings[ "%s.enum_timestamp" % (name) ] = now
            self.settings.sync()

    def SetFieldbus(self):
        # determine if the parameter fieldbus_type is available / set to EtherNet/IP
        try:
            if ( self.fieldbus_type == self.enums[ "fieldbus_type"]["EtherNet/IP (TM)"] ):
                self.reverse_data = True
        except AttributeError:
            #  EGL-C has no fieldbus_type (yet), so determine the fieldbus type from the module info:

            #Error( "Could not determine fieldbus type, asuming PROFINET")

            # the enum is not available as well, so fake that as well:
            fieldbus_type_enum = enum( UNKNOWN=0, PROFINET=1, ETHERNET_IP=2, ETHERCAT=3, MODBUS_TCP=4, COMMON_ETHERNET=5, IOLINK=6, MODBUS_RTU=7 )
            self.enums[ "fieldbus_type" ] = fieldbus_type_enum

            networktype_to_fieldbus_type = dict()
            networktype_to_fieldbus_type[ 137 ] = self.enums[ "fieldbus_type"]["PROFINET"]
            networktype_to_fieldbus_type[ 147 ] = self.enums[ "fieldbus_type"]["MODBUS_TCP"]
            networktype_to_fieldbus_type[ 155 ] = self.enums[ "fieldbus_type"]["ETHERNET_IP"]

            r = self.session_get( url = "http://" + self.host + "/module/info.json", timeout=self.timeout )
            self.CheckResponse( r, "get" )
            try:
                networktype = r.json()["networktype"]

                self.fieldbus_type = networktype_to_fieldbus_type[ networktype ]
            except KeyError:
                # no "networktype" available (e.g. for common-ethernet
                Error( "Could not determine network type." )
                raise

            Debug( f"Determined fieldbus_type from networktype: {self.fieldbus_type}={self.enums[ 'fieldbus_type' ].GetName( self.fieldbus_type )}" )

    def PLCReorder( self, v32 ):
        """return v32 with bytes in v32 reordered for the actual fieldbus_type
        """
        if ( self.fieldbus_type == self.enums[ "fieldbus_type"]["PROFINET"] ):
            return ((v32 & 0xff000000)>>24) | ((v32 & 0x00ff0000)>>8) | ((v32 & 0x0000ff00)<<8) | ((v32 & 0x000000ff)<<24)
        return v32

    def session_get(self, **kwargs ):
        if ( self.debug ):
            Debug( "Sending get request:" )
            for key, value in kwargs.items():
                Debug( "  %s=%s" % (key, value) )

        r = self._session.get(**kwargs)

        if ( self.debug ):
            self.pprint_response( r )

        return r

    def session_post(self, **kwargs ):
        if ( self.debug ):
            Debug( "Sending post request:" )
            for key, value in kwargs.items():
                Debug( "  %s=%s" % (key, value) )

        r = self._session.post(**kwargs)

        if ( self.debug ):
            self.pprint_response( r )

        return r

    def pprint_response(self, response ):
        Debug( "Received response:" )
        for e in [ "ok", "reason" , "status_code", "content", "_content_consumed", "_next", "apparent_encoding", "elapsed", "encoding", "headers", "history", "url" ]:
            v = pprint.pformat( eval( f"response.{e}") )
            Debug( f"  {e}={v}" )



    def GetStructuredValue( self, index ):
        s = Struct()

        r = self.session_get( url = "http://" + self.host + "/adi/data.json?offset=%d&count=1" % index, timeout=self.timeout )
        self.CheckResponse(r, "get")
        data = r.json()[0] # TODO: cope with other indices (for arrays?)
        #Debug( "get_value data= %r" % data)
        try:
            if ( type( data ) is dict  and  data["error"] in (hms.HMS_ErrorCodes.ABP_ERR_ATTR_NOT_GETABLE,hms.HMS_ErrorCodes.ABP_ERR_PROTECTED_ACCESS) ):
                # value is inaccessible due to insufficient read rights
                raise InsufficientReadRights()

            for si in range( len( self.data[index]["datatype"] ) ):

                nb_bytes =  self.data[index]["numsubelements"][ si ] * hms.HMS_Datatypes_size_in_bytes[ self.data[index]["datatype"][ si ] ]
                nb_chars =  nb_bytes << 1

                data_i = data[:nb_chars]
                data = data[nb_chars:]
                #s.__dict__[ self.data[index]["elementname"][ si ] ] = self.GetSingleValue(  self.data[index]["datatype"][ si ] , data_i )
                s.AddOrdered( self.data[index]["elementname"][ si ],
                              self.GetSingleValue(  self.data[index]["datatype"][ si ] , data_i ),
                              self,
                              index,
                              si )
        except InsufficientAccessRights as e:
            raise #reraise to let caller handle that withut clutter

        except Exception as e:
            # for easy debugging:
            Error( "GetStructuredValue( index=%d ) failed with %r\n  r=%r\n  data=%r" % (index, e, r, data ))
            raise

        return s


    def UpdateValue( self, index_or_name, datatype, index ):
        r = self.session_get( url = "http://" + self.host + "/adi/data.json?offset=%d&count=1" % index, timeout=self.timeout )
        self.CheckResponse(r, "get")
        data = r.json()[0]
        #Debug( "get_value data= %r" % data)
        try:
            if ( type( data ) is dict  and  data["error"] in (hms.HMS_ErrorCodes.ABP_ERR_ATTR_NOT_GETABLE,hms.HMS_ErrorCodes.ABP_ERR_PROTECTED_ACCESS) ):
                # value is inaccessible due to insufficient read rights
                if ( index in self.failed_requests and self.failed_requests[ index ] == r.json() ):
                    # same error as before, so do not reprint
                    pass
                else:
                    self.failed_requests[ index ] = r.json()
                    Error( f"get request for parameter {index_or_name} failed. response: {r.json()!r}. (Future errors for the same parameter will not be printed again)" )
                raise InsufficientReadRights()

            if ( self.data[index]["numelements"] > 1 ):
                if ( len( self.data[index]["datatype"] ) > 1 ):
                    return self.GetStructuredValue(index)
                l = []
                nb_bytes =  hms.HMS_Datatypes_size_in_bytes[ datatype ]
                nb_chars =  nb_bytes << 1

                for si in range( self.data[index]["numelements"] ):  # @UnusedVariable
                    data_i = data[:nb_chars]
                    l.append( self.GetSingleValue( datatype, data_i ) )
                    data = data[nb_chars:]

                if ( datatype == hms.HMS_Datatypes.ABP_CHAR ):
                    return "".join(l)
                return l
            else:
                return self.GetSingleValue( datatype, data )

        except Exception as e:  # @UnusedVariable
            # for easy debugging:
            #Error( "get_value( index_or_name=%r, datatype=%r ) failed with %r\n  r=%r\n  data=%r" % (index_or_name, datatype, e, r, data ))
            raise

    def get_value_by_inst(self, inst, datatype=None):

        index = self.GetIndexOfInstance(inst)

        if (datatype is None):
            if (len(self.data[index]["datatype"]) == 1):
                datatype = self.data[index]["datatype"][0]
            else:
                return self.GetStructuredValue(index)

        r = self.session_get(url="http://" + self.host + "/adi/data.json?offset=%d&count=1" % index,
                             timeout=self.timeout)
        self.CheckResponse(r, "get")
        data = r.json()[0]
        # Debug( "get_value data= %r" % data)
        try:
            if (type(data) is dict and data["error"] in (
                    hms.HMS_ErrorCodes.ABP_ERR_ATTR_NOT_GETABLE, hms.HMS_ErrorCodes.ABP_ERR_PROTECTED_ACCESS)):
                # value is inaccessible due to insufficient read rights
                if (index in self.failed_requests and self.failed_requests[index] == r.json()):
                    # same error as before, so do not reprint
                    pass
                else:
                    self.failed_requests[index] = r.json()
                    Error(
                        f"get request for parameter {inst} failed. response: {r.json()!r}. (Future errors for the same parameter will not be printed again)")
                raise InsufficientReadRights()

            if (self.data[index]["numelements"] > 1):
                if (len(self.data[index]["datatype"]) > 1):
                    return self.GetStructuredValue(index)
                l = []
                nb_bytes = hms.HMS_Datatypes_size_in_bytes[datatype]
                nb_chars = nb_bytes << 1

                for si in range(self.data[index]["numelements"]):  # @UnusedVariable
                    data_i = data[:nb_chars]
                    l.append(self.GetSingleValue(datatype, data_i))
                    data = data[nb_chars:]

                if (datatype == hms.HMS_Datatypes.ABP_CHAR):
                    return "".join(l)
                return l
            else:
                return self.GetSingleValue(datatype, data)

        except Exception as e:  # @UnusedVariable
            # for easy debugging:
            # Error( "get_value( index_or_name=%r, datatype=%r ) failed with %r\n  r=%r\n  data=%r" % (index_or_name, datatype, e, r, data ))
            raise

    def set_value( self, index_or_name, datatype=None, value=None, elementindices=None ):
        # for structured elements:
        #  GET /adi/update.json?inst=32834&value=0003&elem=7 HTTP/1.1

        # for arrays:
        #  GET /adi/update.json?inst=32880&value=000000fb&elem=0 HTTP/1.1

        if ( (type( index_or_name ) is str  and  "." in index_or_name)  or not elementindices is None ):
            # its a structured parameter and only a single element is accessed:

            if ( type( index_or_name ) is str  and  "." in index_or_name ):
                (name,subname) = index_or_name.split(".")
                index = self.MakeIndex( name  )
                e = self.data[index]["elementname"].index( subname )
            else:
                index = self.MakeIndex( index_or_name  )
                e = elementindices

            datatype = self.data[index]["datatype"][e]
            hexvalue = self.SingleValueToJSONValue( index, datatype, value )

            inst = self.data[ index ]["instance"]
            r = self.session_post( url="http://" + self.host + "/adi/update.json?inst=%d&value=%s&elem=%d" % (inst,hexvalue,e), timeout=self.timeout )
            self.CheckResponse( r, "post" )
            return

        if ( type(value) in (Struct,tuple) ):
            # its a structure and all elements are given
            index = self.MakeIndex( index_or_name  )
            hexvalue = ""
            for ei in range( len( self.data[index]["datatype"] ) ):
                datatype = self.data[index]["datatype"][ei]
                elementname = self.data[index]["elementname"][ei]
                if ( type( value ) is tuple ):
                    elementvalue = value[ei]
                else:
                    elementvalue = value.__dict__[ elementname ]
                hexvalue += self.SingleValueToJSONValue( index, datatype, elementvalue )

            inst = self.data[ index ]["instance"]
            r = self.session_post( url="http://" + self.host + "/adi/update.json?inst=%d&value=%s" % (inst,hexvalue), timeout=self.timeout )
            self.CheckResponse( r, "post" )
            return

        if ( type( index_or_name ) is str  and  "[" in index_or_name ):
            mob = re.match( "(\w+)\[(.+)\]", index_or_name )
            elementindices = [eval(mob.group(2))]
            index_or_name = mob.group(1)

        index = self.MakeIndex( index_or_name )

        if ( elementindices is None ):
            elementindices = list(range( self.data[index]["numelements" ]))

        if ( datatype is None ):
            if ( len( self.data[index]["datatype"] ) == 1 ):
                # array or normal variable
                datatype = self.data[index]["datatype"][0]

        inst = self.data[ index ]["instance"]

        if ( self.data[index]["numelements" ] > 1 ):
            #its an array
            len_value = 1
            try:
                len_value = len( value )
            except TypeError:
                pass

            if ( len_value == 1 ):
                # only a single value is given, so forward that to all array elements
                value = [value] * len(elementindices)

            if ( datatype == hms.HMS_Datatypes.ABP_CHAR ):
                hexvalue = self.SingleValueToJSONValue( index, datatype, value )
                r = self.session_post( url="http://" + self.host + "/adi/update.json?inst=%d&value=%s" % (inst,hexvalue), timeout=self.timeout )
                self.CheckResponse( r, "post" )
                return

            if ( len( value ) != len( elementindices ) ):
                raise ApplicationError( "Number of values to set for array does not match! Expected 1 or %d values, but not %d" % (self.data[index]["numelements" ],len(value)) )

            if ( len( elementindices ) == self.data[ index]["numelements"] ):
                # whole array is given, so use a single post for performance and workaround bug EGI-6151:

                hexvalue = ""
                for (e,v) in zip( elementindices, value ):
                    hexvalue += self.SingleValueToJSONValue( index, datatype, v )
                r = self.session_post( url="http://" + self.host + "/adi/update.json?inst=%d&value=%s" % (inst,hexvalue), timeout=self.timeout )
                self.CheckResponse( r, "post" )
            else:
                for (e,v) in zip( elementindices, value ):
                    hexvalue = self.SingleValueToJSONValue( index, datatype, v )
                    r = self.session_post( url="http://" + self.host + "/adi/update.json?inst=%d&value=%s&elem=%d" % (inst,hexvalue,e), timeout=self.timeout )
                    self.CheckResponse( r, "post" )
            return

        else:
            # normal
            hexvalue = self.SingleValueToJSONValue( index, datatype, value )

            r = self.session_post( url="http://" + self.host + "/adi/update.json?inst=%d&value=%s" % (inst,hexvalue), timeout=self.timeout )
            self.CheckResponse( r, "post" )
            return

    def AdjustStringValue(self, value, numelements):
        if ( len( value ) > numelements ):
            Debug( "String value %r truncated to %r to fit in actual parameter with numelements=%d\n" % (value, value[:numelements], numelements) )
            return value[numelements]
        elif ( len( value ) < numelements ):
            Debug( "String value %r appended with \\0 to fit in actual parameter with numelements=%d\n" % (value, numelements) )
            return value + "\x00" * (numelements - len(value))
        return value

    def SingleValueToJSONValue(self, index, datatype, value ):
        reverse_data = self.reverse_data
        if ( datatype == hms.HMS_Datatypes.ABP_FLOAT ):
            packed = struct.pack( "!f", value )
            hexvalue = ""
            for c in packed:
                hexvalue += "%02x" % (c)

        elif ( datatype in (hms.HMS_Datatypes.ABP_ENUM,
                          hms.HMS_Datatypes.ABP_UINT8) ):
            hexvalue = "%02x" % (value)

        elif ( datatype == hms.HMS_Datatypes.ABP_UINT16 ):
            hexvalue = "%04x" % (value)

        elif ( datatype == hms.HMS_Datatypes.ABP_UINT32 ):
            hexvalue = "%08x" % (int32_to_uint32(value))

        elif ( datatype == hms.HMS_Datatypes.ABP_UINT64 ):
            hexvalue = "%016x" % (value)

        elif ( datatype == hms.HMS_Datatypes.ABP_SINT8 ):
            if (value < 0 ):
                value = (-value ^ 0xff) +1
            hexvalue = "%02x" % (value)

        elif ( datatype == hms.HMS_Datatypes.ABP_SINT16 ):
            if (value < 0 ):
                value = (-value ^ 0xffff) +1
            hexvalue = "%04x" % (value)

        elif ( datatype == hms.HMS_Datatypes.ABP_SINT32 ):
            if (value < 0 ):
                value = (-value ^ 0xffffffff) +1
            hexvalue = "%08x" % (value)

        elif ( datatype == hms.HMS_Datatypes.ABP_SINT64 ):
            if (value < 0 ):
                value = (-value ^ 0xffffffffffffffff) +1
            hexvalue = "%016x" % (value)

        elif ( datatype == hms.HMS_Datatypes.ABP_BOOL ):
            hexvalue = "%02x" % (int(value))

        elif ( datatype == hms.HMS_Datatypes.ABP_CHAR ):
            reverse_data = False
            numelements = self.data[index]["numelements"]
            value = self.AdjustStringValue( value, numelements )

            hexvalue = ""
            for c in value:
                hexvalue += "%02x" % (ord(c))
        else:
            raise ApplicationError( "Unknown datatype %d" % datatype )

        if ( reverse_data ):
            return Reverse( hexvalue )
        else:
            return hexvalue

    def CheckResponse(self, r, method ):
        if ( not r.ok ):
            raise ApplicationError( "Calling requests self.session_%s( url=%r ) failed %s" % (method, r.url, Var("r") ) )
        elif ( method == "post" ):
            mob = self.rex_result.match( r.content )
            if ( mob ):
                rc = int( mob.group(1) )

                if ( rc == 0 ):  # ok
                    return
                else:
                    Error( f"post request failed. response: {r!r}" )
                    if ( rc == hms.HMS_ErrorCodes.ABP_ERR_ATTR_NOT_SETABLE ): # old error code used by firmware before 2020-01-30
                        raise InsufficientWriteRights()
                    if ( rc == hms.HMS_ErrorCodes.ABP_ERR_PROTECTED_ACCESS ): # new error code used by firmware after 2020-01-30
                        raise InsufficientWriteRights()
                    if ( rc == hms.HMS_ErrorCodes.ABP_ERR_CONTROLLED_FROM_OTHER_CHANNEL ):
                        raise ControlledFromOtherChannel()
                    if ( rc == hms.HMS_ErrorCodes.ABP_ERR_INV_MSG_FORMAT ):
                        raise ServiceNotAvailable()
                    if ( rc == hms.HMS_ErrorCodes.ABP_ERR_UNSUP_CMD ):
                        raise UnsupportedCommand()
            raise ApplicationError( "Calling requests self.session_%s( url=%r ) failed %s" % (method, r.url, r.content) )
        elif ( method == "get"  and  r.content == b'[]' ):
            raise ApplicationError( "Calling requests self.session_%s( url=%r ) failed %s" % (method, r.url, Var("r") ) )

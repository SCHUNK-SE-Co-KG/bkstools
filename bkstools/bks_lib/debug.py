# -*- coding: UTF-8 -*-
'''
Created on 21.11.2018

@author: Dirk Osswald

@brief: basic Debugging and logging functions
'''

import sys
import time, math
g_logmethod = None
g_show_debug = False

def Print( msg, logmethod=None, file=sys.stdout, end="\n" ):
    '''Print msg using print statement. Additionally
    call logmethod( msg ) if logmethod is None then the module level g_logmethod will be tried.
    To disable logging while g_logmethod is set call with logmethod=0 or logmethod=False.
    '''
    now = time.time()
    ms = str( math.modf( now )[0] )[1:5]
    msg = (time.strftime( "%H:%M:%S", time.localtime( now) )) + ms + " " + msg
    print ( msg, file=file, end=end ) ; file.flush()
    if ( logmethod ):
        logmethod( msg )
    elif ( logmethod is None and g_logmethod ):
        g_logmethod( msg )

def Error( msg, logmethod=None, file=sys.stdout, end="\n" ):
    Print( msg, logmethod, file, end=end )

def Debug( msg, logmethod=None, file=sys.stdout, end="\n" ):
    global g_show_debug
    if ( g_show_debug ):
        Print( msg, logmethod, file, end=end )

def SetShowDebug( flag ):
    global g_show_debug
    g_show_debug = flag

def Var( *args ):
        '''
        Return a string with name and value of variables named in args. This will
        print NAME = VALUE pairs for all variables NAME in args. args
        is a list of strings where each string is the name of a
        variable in the context of the caller or args is a string with
        space separated names of variables in the context of the
        caller.

        v = 42
        s = "test"
        Var( "v", "s" )
        =>  "v = 42, s = test"
        Var( "v s" )
        =>  "v = 42, s = test"
        '''
        global_vars = sys._getframe(1).f_globals
        local_vars = sys._getframe(1).f_locals
        sep=u""
        s = u"%s: " % (sys._getframe(1).f_code.co_name)
        for arg in args:
            for a in arg.split():
                s += u"%s%s = %s" % (sep, a, repr(eval(a, global_vars, local_vars)))
                sep = u", "
        return s


class ApplicationError( Exception ):
    '''Class to represent application errors as exceptions.
    '''
    def __init__(self,args=None):
        Exception.__init__(self,args)

class InsufficientAccessRights( ApplicationError ):
    '''Class to represent an error for inusfficient access rights
    '''
    def __init__(self,args=None):
        ApplicationError.__init__(self,args)

class InsufficientReadRights( InsufficientAccessRights ):
    '''Class to represent an error for inusfficient read rights
    '''
    def __init__(self,args=None):
        InsufficientAccessRights.__init__(self,args)

class InsufficientWriteRights( InsufficientAccessRights ):
    '''Class to represent an error for inusfficient Write rights
    '''
    def __init__(self,args=None):
        InsufficientAccessRights.__init__(self,args)

class ControlledFromOtherChannel( InsufficientAccessRights ):
    '''Class to represent an error for ABP_ERR_CONTROLLED_FROM_OTHER_CHANNEL error
    '''
    def __init__(self,args=None):
        InsufficientAccessRights.__init__(self,args)

class ServiceNotAvailable( ApplicationError ):
    '''Class to represent an error for unimplemented services
    '''
    def __init__(self,args=None):
        ApplicationError.__init__(self,args)

class UnsupportedCommand( ApplicationError ):
    '''Class to represent an error for unsupported commands
    '''
    def __init__(self,args=None):
        ApplicationError.__init__(self,args)

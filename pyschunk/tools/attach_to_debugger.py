'''
Created on 2018-06-15

@author: Osswald2
'''

from __future__ import print_function

try:
    if ( "library.zip" in __file__ ):
        # We run as a py2exe generated exe. Debugging will not work, so don't even try
        pass
    else:
        import pydevd
        import pydevd_file_utils
except ImportError as e:
    import os
    if ( "PYDBG" in os.environ or "pydbg" in os.environ ):
        print( "Importing pydevd stuff failed. Connecting to debugger not possible. Running script undebugged anyway." )
except NameError:
    # __file__ could not be accessed, this also indicates that we run as a py2exe generated exe. Debugging will not work, so don't even try
    pass

import traceback
import sys
import re
import socket
import os

g_logmethod = None

def Print( msg, logmethod=None ):
    '''Print msg using print function. Additionally
    call logmethod( msg ) if logmethod is None then the module level g_logmethod will be tried.
    To disable logging while g_logmethod is set call with logmethod=0 or logmethod=False.
    '''
    print( msg, end='' )
    if ( logmethod ):
        logmethod( msg )
    elif ( logmethod is None and g_logmethod ):
        g_logmethod( msg )

def ModifyTraceback():
    """Modify traceback, so that eclipse recognizes the paths when running on Windows.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tbl = traceback.extract_tb( exc_traceback )
    sl = traceback.format_list( tbl )
    for l in sl:
        if ( "linux" in sys.platform ):
            # nothing to do on Linux
            pass
        else:
            mo = re.match( '\s*File "([^"]*)".*', l )
            if ( mo ):
                remote_path = mo.group(1)
                for (lp,rp) in pydevd_file_utils.PATHS_FROM_ECLIPSE_TO_PYTHON:
                    if ( remote_path.startswith(rp) ):
                        l = l.replace( rp, lp, 1 )
                        break
                l = l.replace( '/', '\\' )
        Print( l )
    Print( "%s: %s\n" % (exc_type.__name__, exc_value) )


def AttachToDebugger( func ):
    '''Attach to the pydev debugger (if requested) and run func().

    If the environment variable PYDBG or pydbg is set then try to attach to the debugger on host.
    The host defaults to "delfnn9501" but this can be overridden by the environment variable PYDBG_HOST

    All this is usefull when you want to start scripts from the command line
    but still want to be able to debug these from within eclipse. To do that
    modify the usuall script startup to:

      if __name__ == '__main__':
        from pyschunk.tools import attach_to_debugger
        attach_to_debugger.AttachToDebugger( main )

    Where main is the usual main() function of the script.

    To make this work you must then set PYDBG (and possibly PYDBG_HOST) in
    the environment. The pydevd module must be installed (pip install pydevd).
    '''
    host = "localhost" #"delfnn017886" # default is Dirks Laptop...
    if ( "PYDBG_HOST" in os.environ ):
        host = os.environ["PYDBG_HOST"]

    if ( ("PYDBG" in os.environ or "pydbg" in os.environ)  and  "pydevd" in sys.modules ):
        try:
            # Attach to (remote) debug server in eclipse:
            pydevd.settrace( host=host,
                             stdoutToServer=True,
                             stderrToServer=True,
                             suspend=False )

        except socket.timeout as e:
            Print( "Ignoring exception %r while connecting to pydev debugger.\nIgnored, starting anyway. Debugging is not available\n" % e )

        except socket.error as e:
            Print( "Ignoring exception %r while connecting to pydev debugger.\nIgnored, starting anyway. Debugging is not available\n" % e )

        try:
            # Start the program to debug:
            return func()

        except SystemExit as e:
            if ( e.code != 0 ):
                ModifyTraceback()
                sys.exit( e.code ) # preserve the exit code
            # silently ignore SystemExit(0) as it usually indicates normal exit
        except:
            # Catch all exceptions
            ModifyTraceback()

    else:
        # PYDBG environment variable not set or pydevd not available, so just start func()
        return func()

# -*- coding: UTF-8 -*-
#######################################################################
## \file
#  \section sdhlibrary_python_dbg_py_general General file information
#
#    \author   Dirk Osswald
#    \date     2006-04-08
#
#  \brief
#    Provides class tDBG, a class to print debug messges, see there.
#
#  \section sdhlibrary_python_dbg_py_copyright Copyright
#
#  - Copyright (c) 2007 SCHUNK GmbH & Co. KG
#
#  <HR>
#  \internal
#
#    \subsection sdhlibrary_python_dbg_py_details SVN related, detailed file specific information:
#      $LastChangedBy: Osswald2 $
#      $LastChangedDate: 2015-04-13 18:55:26 +0200 (Mon, 13 Apr 2015) $
#      \par SVN file revision:
#        $Id$
#
#  \subsection sdhlibrary_python_dbg_py_changelog Changelog of this file:
#      \include dbg.py.log
#
#######################################################################
#
"""dbg.py:    This is a python module. It is meant to be imported by other modules and scripts.
Brief:        Provides class tDBG, a class to print debug messges, see there.
Author:       Dirk Osswald <dirk_osswald@web.de>
Date:         2006-04-08
SVN-revision: $Id$

"""
#
##########################################################################

import sys
from . import util

_debug_objects = []
def GetDebugObjects():
    '''\return a list of all tDBG objects created so far.
    Usefull e.g. for interactive enabling/disabling of debug outputs.
    \see pyschunk.guistiff.ci.cTLDebugSelect and pyshcunk.guistuff.ci.cInfo
    '''
    global _debug_objects
    #print( "GetDebugObjects has %d elements" % (len(_debug_objects)) )
    #print( "id(_debug_objects) = %r" % (id(_debug_objects)) )
    #print( "id(sys.modules[\"pyschunk.tools.dbg\"]) = %r" % (id(sys.modules["pyschunk.tools.dbg"])) )
    return _debug_objects

class tDBG(object):
    '''A class to print debug messages.
    - The printing can be switched on or off so the debug code can remain in the
    code. (default is off)
    - The messages can be colorized (default is red).
    - The output can be redirected. (default is sys.stderr)
    - Debug messages can be printed in a functional way or in C++ stream like way
    - tDBG objects are automatically appended to a list, e.g. for later interactive usage, see pyschunk.guistuff.ci.cTLDebugSelect

    Example:
    from pyschunk.tools.dbg import tDBG
    d = tDBG( True )
    g = tDBG( True, "green" )

    d.PDM( "This message is printed in default color red" )
    g << "and this one in a nice green "

    g << "of course you can debug print any objects that have a string representation: " << 08 << 15 << True

    g << "Messages can be turned of and on, e.g. selected by command line options"
    g.SetFlag(False)
    g << "This messages is not printed"
    '''
    def __init__(self, flag = False, color = 'red', fd = None, description="" ):
        self.debug_flag     = flag
        self.color_code     = util.GetColor(color)
        self.normal_code    = util.GetColor("normal")
        if ( fd is None ):
            self.output     = sys.stderr
        else:
            self.output     = fd
        self.do_add_newline = True
        self.description    = description
        GetDebugObjects().append( self )

    def Remove(self):
        '''Remove the tDBG object from the global list of debug objects
        '''
        GetDebugObjects().remove( self )

    def GetDescription(self):
        return self.description

    def SetFlag(self, flag):
        '''Set debug_flag of this tDBG object to flag. After setting
        the flag to True debug messages are printed, else not.
        '''
        self.debug_flag  = flag

    def GetFlag(self):
        '''Get debug_flag of this tDBG object.
        '''
        return self.debug_flag

    def SetColor(self, color):
        '''Set debug_color of this tDBG object to color.
        color is a string like "red", see util.py for valid names.
        if \a color is None then no color is used
        '''
        if ( color is None ):
            self.color_code     = u""
            self.normal_code    = u""
        else:
            self.color_code     = util.GetColor(color)

    def SetOutput(self, fd):
        '''Set output of this tDBG object to fd, which must be a file like object like sys.stderr
        '''
        self.output = fd

    def GetOutput(self):
        '''Get output of this tDBG object, which is a file like object like sys.stderr
        '''
        return self.output

    def SetAddNewline(self, flag):
        '''Set the do_add_newline flag of this tDBG object to flag.
        If True then a newline is automatically printed after each
        printed debug message (like in std python print), else not
        (like in C/C++).
        '''
        self.do_add_newline = flag

    def PDM(self, *msgs ):
        '''Print debug messages "msgs" in the color set
        with SetColor, but only if self.debug_flag is True.
        '''
        if self.debug_flag:
            # compose message
            allmsgs = self.color_code
            for msg in msgs:
                allmsgs += str(msg)
            allmsgs += self.normal_code

            if self.do_add_newline:
                self.output.write( allmsgs+'\n' )
            else:
                self.output.write( allmsgs )
            self.flush() # required to actually see the output in some situations when running on a cygwin console (rxvt)

    def __lshift__(self, msg):
        '''C++ stream like printing:
        d = tDBG( True )
        d << "bla" << "blu %s %d" % (bli,42) << True << 0815
        '''
        old_do_add_newline = self.do_add_newline
        self.do_add_newline = False
        self.PDM(msg)
        self.do_add_newline = old_do_add_newline
        return self

    def __repr__(self):
        return u""

    def var( self, *args ):
        '''
        Print name and value of variables named in args. This will
        print NAME = VALUE pairs for all variables NAME in args. args
        is a list of strings where each string is the name of a
        variable in the context of the caller or args is a string with
        space separated names of variables in the context of the
        caller.

        d = tDBG( True )
        v = 42
        s = "test"
        d.var( "v", "s" )
        d.var( "v s" )

        Both lines will print "v = 42, s = test"
        '''
        if self.debug_flag:
            global_vars = sys._getframe(1).f_globals
            local_vars = sys._getframe(1).f_locals
            sep=u""
            for arg in args:
                for a in arg.split():
                    self << u"%s%s = %s" % (sep, a, repr(eval(a, global_vars, local_vars)))
                    sep = u", "
            self << u"\n"

    def flush(self):
        self.output.flush()

    def WhereAmI(self):
        '''Print "filename:line-number:function-name" of caller

        Example use:
        d = tDBG( True )

        d.WhereAmI()
        '''
        import inspect
        (frame, filename, line_number, function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]  # @UnusedVariable
        self << u"%s:%d:%s\n" % (filename,line_number,function_name)
        self.flush()

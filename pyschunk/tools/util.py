# -*- coding: UTF-8 -*-
#######################################################################
## \file
#  \section sdhlibrary_python_util_py_general General file information
#
#    \author   Dirk Osswald
#    \date     2006-04-07
#
#  \brief
#    Some basic utilities, see also util.__doc__
#
#  \section sdhlibrary_python_util_py_copyright Copyright
#
#  - Copyright (c) 2007 SCHUNK GmbH & Co. KG
#
#  <HR>
#  \internal
#
#    \subsection sdhlibrary_python_util_py_details SVN related, detailed file specific information:
#      $LastChangedBy: Osswald2 $
#      $LastChangedDate: 2015-04-30 19:04:52 +0200 (Thu, 30 Apr 2015) $
#      \par SVN file revision:
#        $Id$
#
#  \subsection sdhlibrary_python_util_py_changelog Changelog of this file:
#      \include util.py.log
#
#######################################################################

# pylint: disable-msg=W0622
## The docstring describing the purpose of the script:
__doc__ =  '''
util.py:      This is a python module. It is meant to be imported by other modules and scripts.
Brief:        A collection of generally usefull python functions and classes:
              - GetColor    : return console color code
              - Beep        : beep on console
              - GetClipboard: Return content of clipboard (on cygwin/Windows)
              - SetClipboard: Set content of clipboard to content (on cygwin/Windows)
              - WinpathToCygpath: return cygwin path from windows path
              - tMyOptionParser: OptionParser with some defaults set (like -d -v)
              - error          : print on stderr
              - Ziplen         : return a list containing tuples of elements and indexes of these elements
              - call           : call function with 0,1,n arguments
              - sgn            : return signum of numeric value
              - GetDefineOrVariable : extract value of define from header file or variable from python file
              - GetProjectName      : extract value of PROJECT_NAME from header file or variable from python file
              - GetProjectRelease   : extract value of PROJECT_RELEASE from header file or variable from python file
              - RangeDefToList      : convert a range definition description to a list of indices, like "1-3,5" => [1,2,3,5]
              - cPrinter            : class to print log messages to stdout and/or file with time prefix and flush
              - enum                : class for C/C++ enum like enumerations
              - ConfirmExit / EnableConfirmExit / DisableConfirmExit : Confirm exit of calling script (disabled by default)
              - read target of a windows shortcut (.lnk file)
              - GetPersistantDict : for storing program parameters persistently
              - MultilineFormatter : for formatting argparse help texts with explicit newlines

Author:       Dirk Osswald <dirk_osswald@web.de>
Date:         2006-04-07
CVS-revision: $Id$
'''
#
######################################################################

# cannot use dbg here since that uses util module

import sys
import os
import time
import re
import argparse

# To be able to output colors in windows console we need colorama.
# This might slow down output, so we only want to import it if
# required.
if (    ('TERM' in list(os.environ.keys()) and os.environ['TERM'] == "eclipse")
     or ('SDH_NO_COLOR' in list(os.environ.keys())) ):
    # colors explicitly disabled
    #print( "No colors available since explicitly disabled" )
    _colors_available = False
else:
    # colors implicitly requested:
    if (    ('OS' in list(os.environ.keys()) and 'WIN' in os.environ['OS'] and (not 'OSTYPE' in list(os.environ.keys()) or not 'cygwin' in os.environ['OSTYPE'] ) )
         or ('USE_COLORAMA' in list(os.environ.keys()) and os.environ['USE_COLORAMA'] == "YES") ):
        # for native windows consoles or when explicitly requested colorama:
        try:
            import colorama
            colorama.init()
            _colors_available = True
            #print( "Colors available via colorama" )
            # with colorama colored output works in windows consoles even
        except ImportError:
            _colors_available = False
            #print( "No colors available since colorama not available" )
    else:
        #print( "Colors natively available" )
        _colors_available = True



######################################################################
#

# Color name to ANSI color code mapping. Define once and for all
_colors={ "normal" : "\x1b[0m",
         "bold" : "\x1b[1m",       # works in windows native console, but in cygwin mintty this renders to "Bright" not bold...
         "red" : "\x1b[31m",
         "green" : "\x1b[32m",
         "yellow" : "\x1b[33m",
         "blue" : "\x1b[34m",
         "magenta" : "\x1b[35m",
         "cyan" : "\x1b[36m",
         "white" : "\x1b[37m",
         "black" : "\x1b[39m",
         "black_back" : "\x1b[40m",
         "red_back" : "\x1b[41m",
         "green_back" : "\x1b[42m",
         "yellow_back" : "\x1b[43m",
         "blue_back" : "\x1b[44m",
         "cyan_back" : "\x1b[45m",
         "magenta_back" : "\x1b[46m",
         "white_back" : "\x1b[47m" }


def GetColor(c):
    '''return a string that when printed sets the color to c, where c must be in
    normal, bold, red, green, yellow, blue, magenta, cyan, white, black, for normal color or
    black_back, red_back, green_back, yellow_back, blue_back, cyan_back, magenta_back, white_back for reverse color
    If the environment variable "TERM" is set to "eclipse" then no color string is returned.
    If the environment variable "SDH_NO_COLOR" is set then "" is returned.
    If the environment variable "OS" is WIN* and "OSTYPE" is not "cygwin"
    then "" is returned. (to prevent color output on windows consoles which cannot handle it).
    If the color is not found in the list of known colors then the string "" is returned.
    '''
    global _colors, _colors_available

    # no coloring when run within a non color aware console like windows
    if ( _colors_available ):
        return _colors[c]
    else:
        return ""
#
######################################################################

######################################################################
#
def Beep( n = 1, delay = 0.2 ):
    '''Do n console beeps with a delay of delay seconds.
    '''
    while n >= 1:
        console = open("/dev/console", "w")
        console.write( "\a" )
        console.close()
        n = n-1
        if n >= 1:
            time.sleep( delay )
#
######################################################################

######################################################################
#
def GetClipboard():
    '''Return content of clipboard (on cygwin/Windows)
    '''

    cb = open( "/dev/clipboard", "r" )
    result = cb.read(-1)
    cb.close()
    return result
#
######################################################################

######################################################################
#
def SetClipboard(content):
    """Set content of clipboard to content (on cygwin/Windows)
    """

    cb = open( "/dev/clipboard", "w" )
    cb.write(content)
    cb.close()
#
######################################################################

######################################################################
#
from optparse import OptionParser

class tMyOptionParser(OptionParser):
    '''OptionParser with some default options already set:
    -d | --debug turn on debug (set options.debug flag)
    -v | --version print version and exit
    '''
    def ShowVersion(self, option, opt, value, parser):  # @UnusedVariable
        print(self.version)
        sys.exit()

    def __init__(self, usage = "", version = "" ):
        '''Create a tMyOptParser instance.

        usage has the usual meaning and version is the string that is printed
        when -v | --version option is set
        '''
        OptionParser.__init__( self, usage )
        self.version = version

        # add common options:
        self.add_option( "-d", "--debug",
                         action="store_true", dest="debug", default=False,
                         help="Print debug messages while processing.")
        self.add_option( "-v", "--version",
                         #action="store_true", dest="print_version", default=False,
                         action="callback", callback=self.ShowVersion,
                         help="Print the version and exit.")
#
######################################################################

######################################################################
#
def WinpathToCygpath(winpath):
    '''Return the cygwin path of the file with the windows path winpath

    Will convert "c:\\bla\\blu.bli" to "/cygdrive/c/bla/blu.bli"
    '''
    if (winpath[1] != ':'):
        if ( winpath.startswith( "/") and not "\\" in winpath ):
            # already a cygpath!
            return winpath
        raise Exception( "WinpathToCygpath(): %r is not an absolute path, donnow what to do!" % (winpath) )

    result = "/cygdrive/"
    for c in winpath:
        if (c==":"):
            pass
        elif (c=="\\"):
            result += "/"
        else:
            result += c
    return result
#
######################################################################

######################################################################
#
def error( *args ):
    for arg in args:
        print(arg, end=' ', file=sys.stderr)
    print(file=sys.stderr)
#
######################################################################

######################################################################
#
def Ziplen( l ):
    '''return a list containing tuples of elements and indexes of these elements
    Remark: this is like the std enumerate(l) with the elements in the tuples reversed
    '''
    return list(zip( l, list(range(len(l))) ))
#
######################################################################

######################################################################
#
def Call(fun,pars):
    '''call function fun with arguments pars.
    - pars = None : call fun()
    - pars = SomeType : call fun(pars)
    - pars = tuple    : call fun(*pars)
    '''
    if ( type( pars ) == type(None) ):
        fun()
    elif ( type( pars ) == tuple ):
        fun(*pars)
    else:
        fun(pars)
#
######################################################################

######################################################################
#
def sgn(v):
    '''
    return signum of v
    '''
    if   (v>0.0): return  1.0
    elif (v<0.0): return -1.0
    else:         return  0.0
#
######################################################################

#######################################################################
#
def GetDefineOrVariable( ifile, name ):
    '''
    Return value of C/C++ define "name" in header file "ifile" or of
    python variable "name" in python module "ifile".

    \internal The regular expression works on lines formed like:
    - #define NAME "A-Name"
    - NAME = "A-Name"
    where "NAME" is the value of name
    '''
    pattern = re.compile( '^\s*(#\s*define\s+%s|%s\s*=)\s+"([^"]*)"' % (name,name) )
    f = open( ifile, "r" )
    for l in f.readlines():
        m = pattern.match( l )
        if m:
            #print( "extracted %s <%s>" % (name, m.group(2)) )
            return m.group(2)
    raise Exception( '%s is not defined in FILE "%s"!' % (name,ifile) )
#
#######################################################################

#######################################################################
#
def GetProjectName( release_file ):
    '''
    Return name of project (extracted from header file release_file).
    The code below uses a regular expression to extracts the value of the C preprocessor
    macro define or the definition of a variable named PROJECT_NAME.
    The extracted value can be:
    - Used by doxygen as project name.
    - Used as base name of the generated pdf documentation files.
    - Used as name of project directory when installing.

    \internal The regular expression works on lines formed like:
    - #define PROJECT_NAME "A-Name"
    - PROJECT_NAME = "A-Name"
    '''
    try:
        return GetDefineOrVariable( release_file, "PROJECT_NAME" )
    except Exception as e:
        error( 'Caught exception "%s", returning default "PROJECT_NAME"', str(e) )
        return "PROJECT_NAME"
#
#######################################################################


#######################################################################
#
def GetProjectRelease( release_file ):
    '''
    Return release of project (extracted from header file release_file).
    The code below uses a regular expression to extracts the value of the C preprocessor
    macro define or the definition of a variable named PROJECT_RELEASE.
    The extracted value can be:
    - Used by doxygen as project release.
    - Used as name of release directory when installing.

    \internal The regular expression works on lines formed like:
    - #define PROJECT_RELEASE "1.0.0.0-dev"
    - PROJECT_RELEASE = "1.0.0.0-dev"
    '''
    try:
        return GetDefineOrVariable( release_file, "PROJECT_RELEASE" )
    except Exception as e:
        error( 'Caught exception "%s", returning default "PROJECT_RELEASE"', str(e) )
        return "PROJECT_RELEASE"
#
#######################################################################

#######################################################################
#
def RangeDefToList( range_definition, max_no=1000 ):
    '''return a list of indexes according to a range definition string
    e.g.  "1" => [1], "1,2,4" => [1,2,4], "3-6" => [3,4,5,6])
    '''
    # determine the indices of the plots to use:
    if ( range_definition in "all" ):
        index_to_use = list(range( 0, max_no))  # should be large enough
    else:
        index_to_use = []
        # split comma separated parts
        parts = range_definition.split(",")
        parts = [ p.strip()  for p in parts ]
        re_number = re.compile("^[0-9]+$")
        re_range  = re.compile("^([0-9]+) *- *([0-9]+)$")
        for p in parts:
            n = re_number.match( p )
            r = re_range.match( p )
            if ( n ):
                index_to_use.append( eval( p ) )

            elif ( r ):
                for i in range( int(r.groups()[0]), int(r.groups()[1])+1 ):
                    index_to_use.append( i )
            else:
                raise ValueError( "illegal pattern '%s' in range_definition '%s'" % (p,range_definition) )

    #dbg << "index_to_use =" << repr( index_to_use) << "\n" # pylint: disable-msg=W0104
    return index_to_use
#
#######################################################################

#######################################################################
#
import math
_DefaultGetTime2_start = None
class cPrinter( object ):
    '''Class to handle printing of messages.
    - messages can be prepended with the current time
    - messages can be written to several outputs simultaneously (e.g. stdout and a logfile)
    - output is flushed (Needed since windows python needs flush() when called from cygwin)
    '''
    @staticmethod
    def DefaultGetTime( now ):
        '''Default value for \a GetTime parameter of CTor.
        Return a time string in format HOUR:MINUTE:SECONDS.MILLISECONDS corresponding to \a now

        \remark
          If run on windows by a native windows python and the environment
          variable TZ is set then the localtimes are reported incorrectly.
          To avoid that you could unset the timezone prior to importing time.
          > if os.getenv("TZ"):
          >     os.unsetenv("TZ")
        '''
        return "%s.%03d " % (time.strftime( "%H:%M:%S", time.localtime( now ) ), int( math.modf(now)[0] * 1000 ) )

    @staticmethod
    def DefaultGetTime2( now ):
        '''Alternative value for \a GetTime parameter of CTor.
        Return a time string in format SECONDS.MILLISECONDS corresponding to the duration from the first call to this function to \a now

        '''
        global _DefaultGetTime2_start
        if (_DefaultGetTime2_start is None):
            _DefaultGetTime2_start = time.time()
        return "%.3f " % (time.time()-_DefaultGetTime2_start)

    @staticmethod
    def DefaultGetDate( now ):
        '''Alternative value for \a GetTime parameter of CTor.
        Return a time string in format YEAR-MONTH-DATE_HOUR:MINUTE:SECONDS corresponding to \a now
        '''
        return time.strftime( "%Y-%m-%d_%H:%M:%S", time.localtime( now ) )

    start = 0
    @staticmethod
    def DefaultGetDate2( now ):
        '''Alternative value for \a GetTime parameter of CTor.
        Return a time string in format YEAR-MONTH-DATE; HOUR:MINUTE:SECONDS; SECONDSSINCESTART corresponding to \a now
        '''
        return time.strftime( "%Y-%m-%d; %H:%M:%S; ", time.localtime( now ) ) + "%.3f" % (time.time() - cPrinter.start)

    @staticmethod
    def DefaultGetDate3( now ):
        '''Alternative value for \a GetTime parameter of CTor.
        Return a time string in format YEAR-MONTH-DATE; HOUR:MINUTE:SECONDS; SECONDSSINCESTART corresponding to \a now
        with SECONDSSINCESTART printed with ',' to separate the fractional part.
        '''
        seconds_since_start = "%.3f" % (time.time() - cPrinter.start)
        seconds_since_start = seconds_since_start.replace(".",",")
        return time.strftime( "%Y-%m-%d; %H:%M:%S; ", time.localtime( now ) ) + seconds_since_start

    def __init__( self, mindelay_s, outputs, GetTime=None ):
        '''CTor.
        \param mindelay_s : minimum delay in seconds. If more than this many
               seconds have passed since the last message then the current
               time is printed first. If 0 then every message is prepended with
               the current time
        \param outputs : a list of file like objects. Messages are written to all these
        \param GetTime : a function taking a time.time() value as parameter and returning
                         a corresponding string. This function is called to generate the
                         prepended time. If not given or None the default DefaultGetTime()
                         will be used.
        '''
        self.lasttime = time.time() - 2*mindelay_s # make sure time is printed on first call
        self.mindelay_s = mindelay_s
        self.outputs = outputs
        if ( GetTime is None ):
            self.GetTime = self.DefaultGetTime
        else:
            self.GetTime = GetTime
        cPrinter.start = time.time()

    def Print( self, msg, overrideprefix=None ):
        '''Generate output on all self.outputs according to \a msg.
        (Needed since windows python needs flush() when called from cygwin)
        \param msg - the string message to print on self.outputs
        \param overrideprefix - a prefix to print before \a msg instead of the standard time prefix
        '''
        now = time.time()
        t = self.GetTime( now )
        if ( self.mindelay_s == 0.0 ):
            if ( overrideprefix is None ):
                msg = t + msg
            else:
                msg = overrideprefix + msg
        elif ( time.time() - self.lasttime > self.mindelay_s ):
            msg = "---%s---\n" % (t) + msg
        for f in self.outputs:
            if ( f ):
                #f.write( repr(msg)+'\n' )
                f.write( msg )
                f.flush()
        self.lasttime = time.time()
#
##########################################################################

##########################################################################
#
class enum(dict):
    '''class for a C/C++ enum like object
    \see http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python

    Best way of usage (with pydev code completion and no pydev code analysis problems:
    \example
    \code
        >>> eNo = enum()
        >>> eNo.null = 0
        >>> eNo.eins = 1
        >>> eNo.zwei = 2
        >>> eNo.eins
        1
        >>> eNo.GetName( 2 )
        zwei
    \endcode


    \example
    \code
        >>> Numbers = enum('ZERO', 'ONE', 'TWO')
        >>> Numbers.ZERO
        0
        >>> Numbers.ONE
        1
    \endcode

    Additionally you can assign specific values
    and reverse look up the name of a value using GetName
    or add key=value pairs later (overwriting will raise a KeyError

    \example
    \code
        >>> Nummern = enum( zwei=2, drei=3, fuenf=5)
        >>> Nummern.zwei
        2
        >>> Nummern.GetName( 3 )
        drei
        >>> Nummern.Add( "sechs", 6 )
        >>> Nummern.sechs
        6
    \endcode

    \example
    \code
        >>> auto = enum()
        >>> auto.bla = auto.Next()
        >>> auto.blu = auto.Next()
        >>> auto.bli = auto.Next()
        >>> auto.bla
        0
        >>> auto.GetName( 1 )
        blu
    \endcode

    (Disable "Undefined variable from import" code-analysis errors according to
    http://pydev.org/manual_adv_code_analysis.html
    DOES NOT WORK)
    *@DynamicAttrs*
    '''
    def __init__( self, *sequential, **named ):
        dict.__init__( self, list(zip(sequential, list(range(len(sequential))))), **named)
        for (k,v) in list(self.items()):
            setattr(self, k, v )
        self._last = -1
        #FIXME: calling self.values() will include _last!


    def Next(self):
        self._last += 1
        return self._last

    def __setattr__(self, k, v):
        dict.__setattr__(self, k, v)
        if ( not k in self ):
            self[ k ] = v

    def GetName(self, v, default_name=None ):
        '''\return the key of value \a v in self or raise ValueError if not present and default_name is None.
        If no present and default_name is not None then default_name is returned
        '''
        for (kk,vv) in list(self.__dict__.items()):
            if ( vv == v ):
                return kk
        if ( default_name is None ):
            raise ValueError( "Value %r not in enum" % v )
        return default_name

    def Add( self, k, v ):
        '''Add the k=v to the enum
        '''
        if ( k in list(self.__dict__.keys()) ):
            raise KeyError( "Key %r already in enum" % k )
        self[ k ] = v
        setattr(self, k, v )

##########################################################################

##########################################################################
#
def SetExitHandler( func, remove=False ):
    '''Add or remove a handler to call \a func when script ends.
    This even works for console applications in Windows if their command console window is closed!

    Example usage:

    def CalledOnExit(sig, func=None):
        # ... do your stuff

        # Remove ourself from the list of exit handlers
        SetExitHandler( CalledOnExit, remove = True )

        # either:
        return False # => other registered handlers are called on exit as well
        # or:
        return True  # => no more handlers are called on exit

    SetExitHandler( CalledOnExit )
    '''
    if os.name == "nt":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(func, not remove)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception("pywin32 not installed for Python " + version)
    else:
        import signal
        signal.signal(signal.SIGTERM, func)

eExitState = enum('RUNNING', 'EXITING', 'EXITED')
_exit_state = None

def GetExitState():
    """
    Return one of the eExitState enums, e.g. so that (sub)threads can determine when to stop:

    - Before CTRL-C is pressed (normal operation) RUNNING is returned
    - After CTRL-C is pressed and the ConfirmExit() exit handler waits for user confirmation EXITING is returned
    - After CTRL-C is pressed and the user has confirmed the exit or the confirmation was not requested then EXITED is returned
    """
    global _exit_state
    return _exit_state

def SetExitState( new_state ):
    """
    Sets the exit state to be returned by GetExitState().

    \remark This is called by the ConfirmExit exit handler and should not be called by you, unless you know exactly what you are doing.
    """
    global _exit_state
    #print( "SetExitState %r" % (new_state) )
    _exit_state = new_state

SetExitState( eExitState.RUNNING )

_do_confirm_exit = False
def ConfirmExit(sig=None, func=None):  # @UnusedVariable
    '''To be able to read final error messages on exit when called from windows
    user has to confirm the exit.
    '''
    #print( "ConfirmExit start" )

    # Tell subthreads that we are exiting, but still waiting for user confirmation:
    global _keep_running
    SetExitState( eExitState.EXITING )

    global _do_confirm_exit
    if ( _do_confirm_exit ):
        print("\n(Finished: Press return to exit this program)", end=' ')
        try:
            sys.stdout.flush()
        except AttributeError:
            pass # to avoid: Tee instance has no attribute 'flush'
        try:
            sys.stderr.flush()
        except AttributeError:
            pass # to avoid: Tee instance has no attribute 'flush'
        try:
            # Ask for confirmation to exit:
            input("")
        except EOFError as e:  # @UnusedVariable
            #print( "caught eoferror %r" % e )
            # in the py2exe generated exes EOFError is thrown on the final return...
            pass
        except Exception as e:  # @UnusedVariable
            #print( "caught Exception %r" % e )
            pass


    #print( "ConfirmExit ending returning true" )
    SetExitHandler( ConfirmExit, True )

    # Tell subthreads that we are finally exited:
    SetExitState( eExitState.EXITED )

    return False

def EnableConfirmExit():
    global _do_confirm_exit
    _do_confirm_exit = True

def DisableConfirmExit():
    global _do_confirm_exit
    _do_confirm_exit = False

#import atexit
#atexit.register(ConfirmExit)
SetExitHandler( ConfirmExit )

#
##########################################################################

def Bitify(v):
    '''\return 1 if \a v convertet to a boolean yields True, else 0
    '''
    if (v):
        return 1
    else:
        return 0

def GetTargetOfLnk( filename_lnk ):
    import win32com.client

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut( filename_lnk )
    return shortcut.Targetpath

def GetPersistantDict( name=None, path=None, cdbg=None ):
    '''Dictionary that stores objects persistently using shelve

    If you want to be able to generate standalone exes with py2exe
    you must add the following lines to your script
    \code
      # The following module must be imported explicitly to be able to generate
      # standalone exes with py2exe on Python 3
      import dbm.dumb  # @UnusedImport
    \endcode
    '''
    import shelve
    if ( path is None ):
        path = os.path.expanduser("~")
    path = os.path.normpath(path)

    if ( name is None ):
        name = ".pypersistent"

    if ( not os.path.exists(path) ):
        if ( cdbg ): cdbg << "Given path %r does not exist. Using '.' instead\n" % (path)
        path="."

    db_name = os.path.join( path, name )
    persistent_dict = shelve.open( db_name )
    if ( cdbg ):
        #dbg.var( "db_name persistent_dict")
        cdbg.var( "db_name" )
        cdbg << "persistent_dict:\n"
        for (k,v) in list(persistent_dict.items()):
            cdbg << "  %r:%r\n" % (k,v)
    return persistent_dict


class Struct(object):
    """Create an instance with argument=value slots.
    This is for making a lightweight object whose class doesn't matter."""
    def __init__(self, **entries):
        self.__dict__.update(entries)

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
        args = ['%s=%s' % (k, repr(v)) for (k, v) in list(vars(self).items())]
        return 'Struct(%s)' % ', '.join(args)


class MultilineFormatter(argparse.HelpFormatter):
    """A formatter to be used in argparse argument parser.
    Allows to explicitly state where newlines have to be insterted by setting |n in the text.

    Use formatter_class=pyschunk.tools.util.MultilineFormatter in constructor of argparse.ArgumentParser

    """
    def _fill_text(self, text, width, indent):
        import textwrap as _textwrap

        text = self._whitespace_matcher.sub(' ', text).strip()
        paragraphs = text.split('|n ')
        multiline_text = ''
        for paragraph in paragraphs:
            formatted_paragraph = _textwrap.fill(paragraph, width, initial_indent=indent, subsequent_indent=indent) + '\n'
            multiline_text = multiline_text + formatted_paragraph
        return multiline_text

    def _split_lines(self, text, width):
        #return argparse.HelpFormatter._split_lines(self, text, width)
        r = []
        for text_part in text.split( "|n" ):
            r += argparse.HelpFormatter._split_lines(self, text_part, width)
        return r

if __name__ == "__main__":
    p=cPrinter(0,[sys.stdout])
    p.Print( "this is cPrinter.Print with default time prefix\n" )


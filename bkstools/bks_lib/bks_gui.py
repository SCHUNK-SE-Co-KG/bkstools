# -*- coding: UTF-8 -*-
'''
Created on 26.07.2019

@author: Dirk Osswald

@brief Provides some common gui stuff
'''

from tkinter import Frame
from bkstools.bks_lib.debug import ControlledFromOtherChannel
import sys
import traceback

class cAppWithExceptionHandler(Frame):
    '''Intermediate base class for tkinter application apps that have an exception handler

    Requires that the derived class overloads self.SetStatusLine()
    '''
    def __init__(self, master, class_ ):
        Frame.__init__(self, master=master, class_=class_ )
        self.master = master
        master.report_callback_exception = self.report_callback_exception

    def report_callback_exception(self, *args):
        '''Exception handler to make exceptions appear in status line
        See https://stackoverflow.com/questions/4770993/how-can-i-make-silent-exceptions-louder-in-tkinter

        *args is (exc, val, tb)
        '''
        (exc,val,tb) = args  # @UnusedVariable
        if ( exc is ControlledFromOtherChannel ):
            self.SetStatusline( "No control authority! Gripper is controlled from another channel!", True )
            return
        else:
            err = traceback.format_exception(*args)
            sys.stderr.write( "report_callback_exception( %r ):\n" % (args,) )
            for l in err:
                sys.stderr.write( l )

            self.SetStatusline( "Ignoring exception %r!" % (exc), True )
            return

        # normal handling would be:

    def SetStatusline( self, msg, is_error ):
        """Default implementation. Will be overloaded in derived classes
        """
        print(("%s,%r" % (msg, is_error)))

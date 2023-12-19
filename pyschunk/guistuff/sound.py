# -*- coding: UTF-8 -*-
'''
Created on 19.08.2013

@author: Osswald2
'''

try:
    from winsound import *  # @UnusedWildImport
except ImportError:
    MB_ICONASTERISK = 0
    MB_ICONEXCLAMATION = 1
    MB_ICONHAND = 2
    MB_ICONQUESTION = 3
    MB_OK = 4
    import sys
    def MessageBeep( btype=MB_OK ):  # @UnusedVariable
        '''Translate any request for a message beep into a ASCII "alarm" on sys.stdout
        (This works as expected even on a remote xterm - unless stdout is redirected)
        '''
        sys.stdout.write("\a")
        sys.stdout.flush()

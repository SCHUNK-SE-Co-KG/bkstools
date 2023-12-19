# -*- coding: UTF-8 -*-
'''
Python module for peeking on input from stdin

Inspired by https://stackoverflow.com/a/19655992/6098953

Created on 2018-05-03

@author: Dirk Osswald
'''
import sys
import threading
import queue as Queue

_g_input_queue = Queue.Queue()
_g_input_thread = None

def _Reader():
    global _g_input_queue
    while True:
        _g_input_queue.put( sys.stdin.read(1) )


def Start():
    """Call this once befor you want to use any of the functions below
    """
    _g_input_thread = threading.Thread(target=_Reader)
    _g_input_thread.daemon = True
    _g_input_thread.start()


def Clear():
    """Clear available input
    """
    while InputAvailable():
        Getch()

def InputAvailable():
    """Return True if input is available on stdin.
    But will only return True if the input was terminated by 'Return'
    """
    return not _g_input_queue.empty()

def Getch( block=True, timeout=None):
    """Remove and return a character from stdin. This may include the
    trailing newline character.

    If optional args 'block' is true and 'timeout' is None (the default),
    block if necessary until an item is available. If 'timeout' is
    a non-negative number, it blocks at most 'timeout' seconds and raises
    the Empty exception if no item was available within that time.
    Otherwise ('block' is false), return an item if one is immediately
    available, else raise the Empty exception ('timeout' is ignored
    in that case).
    """
    return _g_input_queue.get( block, timeout )

def RawInput( prompt ):
    """The standard raw_input() does not work when peek is used.
    This is the alternative which works the same way as the standard,
    i.e. it prints the prompt, then waits for input ended by 'Return'.
    The final newline is not part of the returned string.
    """
    Clear()

    print( prompt, end="" )
    sys.stdout.flush()

    result = ""
    while True:
        c = Getch()
        if ( c == "\n" ):
            return result
        result += c

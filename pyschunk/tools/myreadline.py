# -*- coding: UTF-8 -*-
"""readline.py -- Readline Alternative for Windows
Copyright 2001, Chris Gonnerman and Alex Martelli
"""
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and its
# associated documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appears in all
# copies, and that both that copyright notice and this permission notice
# appear in supporting documentation.
#
# THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS.  IN NO
# EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF
# USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

# CREDITS:
#
# Small additions for history-file stuff by Alex Martelli
#
# Completer by Jürgen Hermann

__version__ = "1.7"

import sys
import  os
import  msvcrt
import  _rlsetup

_history = []

def DPrint( msg ):
    pass
    #sys.stderr.write( msg + "\n" )

def set_history_length(n):
    global _history_length
    if n < 0:
        _history_length = sys.maxint
    else:
        _history_length = n

def get_history_length():
    if _history_length == sys.maxint:
        return -1
    return _history_length

set_history_length(int(os.getenv('PYHISTMAX','-1')))

def read_history_file(filename):
    def clean(s, p=['']):
        if s==p[0]:
            return 0
        p[0]=s
        return s
    fp = open(filename)
    all_lines = fp.read().splitlines()
    #DPrint( "all_lines:===" )
    #DPrint( all_lines )
    #DPrint( "===========" )
    _history[:] = filter(clean, all_lines)[:_history_length]
    #DPrint( "History:===" )
    #DPrint( _history )
    #DPrint( "===========" )
    fp.close()

def write_history_file(filename):
    fp = open(filename, "w")
    fp.write('\n'.join(_history+['']))
    fp.close()
    DPrint( "wrote %r to history file %r" % (_history,filename) )

_pyhistfile = os.getenv('PYHISTFILE', sys.prefix+'\\pyhist.txt')

try:
    DPrint( "Reading from history file %r" % _pyhistfile )
    ##raw_input()
    read_history_file(_pyhistfile)
except IOError:
    pass

input = sys.stdin  # @ReservedAssignment
output = sys.stderr

_step = 10
_maxlen = 70

_kstable = {
    'BackSpace':    '\010',
    'Delete':       '!S',
    'Home':         '!G',
    'End':          '!O',
    'Ctrl-Home':    '!w',
    'Ctrl-End':     '!u',
    'Right':        '!M',
    'Left':         '!K',
    'Tab':          '\011',
    'Up':           '!H',
    'Down':         '!P',
    'Ctrl-R':       '\x12',
}

_completer = None

class _NullOutput:
    def write(self, s):
        pass

debug = _NullOutput()
# debug = open("debug.txt", "w")

def BS(n):
    debug.write("BS(%d)\n" % n)
    output.write('\x08' * n)

class ReadlineBuffer:

    def __init__(self):
        self.s = ""
        self.p = 0
        self.o = 0

    def home_cursor(self):
        debug.write("home_cursor() p = %d, o = %d\n" % (self.p, self.o))
        BS(self.p - self.o)
        if self.o > 0:
            BS(1)

    def paint_tail(self):
        debug.write("paint_tail()\n")
        tail = self.s[self.p:min(len(self.s), self.maxlen + self.o)]
        output.write(tail)
        output.write("  \x08\x08")
        if len(self.s) > (self.maxlen + self.o):
            output.write(">\x08")
        BS(len(tail))

    def rewrite_buffer(self):
        debug.write("rewrite_buffer()\n")
        debug.write("self.o = %d\n" % self.o)
        if self.o > 0:
            output.write("<")
        win = self.s[self.o:self.maxlen+self.o]
        clr = max(self.maxlen - len(win), 0)
        debug.write("win = " + win + "\n")
        debug.write("clr = %d\n" % clr)
        output.write(win+(" "*(clr + 2)))
        BS(2)
        if len(self.s) > (self.maxlen + self.o):
            output.write(">\x08")
        BS(max(self.maxlen - (self.p - self.o), 0))

    def correct_offset(self):
        new_o = self.o
        while new_o and self.p < (new_o + self.step):
            new_o = new_o - self.step
        while self.p > (self.maxlen + new_o - self.step):
            new_o = new_o + self.step
        if new_o == self.o:
            return
        self.home_cursor()
        self.o = new_o
        self.rewrite_buffer()

    def new_line(self):
        debug.write("new_line()\n")
        self.p = len(self.s)
        if len(self.s) > (self.maxlen - self.step):
            self.o = (((len(self.s) - self.maxlen) // self.step) + 1) * self.step
        else:
            self.o = 0
        self.rewrite_buffer()

# dummy functions

def set_completer(function=None):
    global _completer
    _completer = function

def parse_and_bind(line):
    pass

def read_init_file(filename=None):
    pass


# This makes it easier to tell if this code loaded correctly.
# Python "hides" any errors loading readline.
# Change to a true value to hide.
_issued = None

def readline(step = _step, maxlen = _maxlen,
    history = _history, histfile = _pyhistfile):
    """readline(step, maxlen, history, histfile)
    Read a line from the console.

    step:      Number of columns to side-scroll per step.
    maxlen:    Maximum length of string to read.
    history:   List of strings comprising the current history.
    histfile:  History file name (for saving history), None to disable.
    """

    global _issued

    if not _issued:
        output.write("\x08\x08\x08\x08Alternative ReadLine " + \
                    __version__ + \
                    " -- Copyright 2001, Chris Gonnerman\n>>> ")
        _issued = 1
    #DPrint( "readline(step=%r,maxlen=%r,history=%r,histfile=%r)" % (step,maxlen,history,histfile) )
    DPrint( "readline(step=%r,maxlen=%r,...,histfile=%r)" % (step,maxlen,histfile) )
    buf = ReadlineBuffer()
    buf.maxlen = maxlen
    buf.step = step

    pos = len(history)

    c_state = 0
    c_save = None

    while 1:
        c_new_state = 0

        buf.p = max(min(buf.p, len(buf.s)), 0)

        buf.correct_offset()

        c = msvcrt.getch()

        #print( "Received c=%r" % c )###

        if c == '\0' or c == '\xe0':
            c = "!" + msvcrt.getch()

        if c == '\r' or c == '\n':
        #    buf.s = buf.s + '\n'
            break

        elif c == '\x1b':
            buf.s = ""

        elif c == '\x04' or c == '\x1a': # CTRL-D or CTRL-Z
            buf.s = ""
            break

        elif c == "\x03": # CTRL-C
            DPrint( "readline caught CTRL-C" )
            raise KeyboardInterrupt()


        elif c == _kstable["BackSpace"]:
            if c_state:
                buf.home_cursor()
                buf.s, buf.p = c_save
                buf.rewrite_buffer()
            elif buf.s:
                buf.s = buf.s[:buf.p-1] + buf.s[buf.p:]
                buf.p = buf.p - 1
                BS(1)
                buf.paint_tail()

        elif c == _kstable["Delete"]:
            if buf.s:
                buf.s = buf.s[:buf.p] + buf.s[buf.p+1:]
                buf.paint_tail()

        elif c == _kstable["Up"]:
            if pos:
                pos = pos - 1
                buf.home_cursor()
                buf.s = history[pos]
                buf.new_line()

        elif c == _kstable["Ctrl-Home"]:
            if pos:
                pos = 0
                buf.home_cursor()
                buf.s = history[pos]
                buf.new_line()

        elif c == _kstable["Down"]:
            if pos < len(history):
                pos = pos + 1
                buf.home_cursor()
                if pos < len(history):
                    buf.s = history[pos]
                else:
                    buf.s = ""
                buf.new_line()

        elif c == _kstable["Ctrl-End"]:
            if pos < len(history):
                pos = len(history)
                buf.home_cursor()
                buf.s = ""
                buf.p = 0

        elif c == _kstable["Home"] or c == '\001':
            buf.home_cursor()
            buf.p = 0
            buf.o = 0
            buf.paint_tail()

        elif c == _kstable["End"] or c == '\005':
            buf.home_cursor()
            debug.write("END buf.p = %d, buf.o = %d\n" % (buf.p, buf.o))
            buf.new_line()
            debug.write("END\n")

        elif c == _kstable["Left"] or c == '\002':
            buf.p = buf.p - 1
            if buf.p >= 0:
                BS(1)

        elif c == _kstable["Right"] or c == '\006':
            if buf.s[buf.p:]:
                output.write(buf.s[buf.p])
                buf.p = buf.p + 1

        elif (c == _kstable["Tab"] or c == '\011') and _completer:
            if c_state == 0:
                c_save = (buf.s, buf.p)
                c_pos = buf.p
                while c_pos > 0 and (buf.s[c_pos-1].isalnum()
                        or buf.s[c_pos-1] in '_.'):
                    c_pos -= 1
                c_text = buf.s[c_pos:buf.p]

            try:
                c_result = _completer(c_text, c_state)
            except:
                c_result = None

            if c_result:
                buf.home_cursor()
                c_new_state = c_state + 1
                buf.s = c_save[0][:c_pos] + c_result + c_save[0][c_save[1]:]
                buf.p = c_pos + len(c_result)
                buf.rewrite_buffer()

        elif ( c == _kstable["Ctrl-R"] ):
            pass
            # TODO: implement search in history

        elif len(c) == 1 and c >= " ":
            output.write(c)
            buf.s = buf.s[:buf.p] + c + buf.s[buf.p:]
            buf.p = buf.p + len(c)
            buf.paint_tail()


        c_state = c_new_state

    output.write("\n")

    if buf.s != "\n":
        if not history or history[-1] != buf.s:
            #DPrint( "appending l %r h-1=%r b.s=%r != = %r\n" % (buf.s,history[-1],buf.s[:-1],history[-1] != buf.s[:-1] ))
            history.append(buf.s)
        history = history[-1*_history_length:]
        if histfile and type(histfile) is type(""):
            fp = open(histfile, "w")
            for line in history:
                if line:
                    fp.write(line + "\n")
            fp.close()

    return buf.s

_rlsetup.install_readline(readline)

# end of file.

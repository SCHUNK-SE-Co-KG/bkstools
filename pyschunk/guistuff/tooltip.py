# -*- coding: UTF-8 -*-
'''
Created on 07.08.2013

@author: Osswald2
'''

from tkinter import * #@UnusedWildImport
from idlelib import tooltip as ToolTip
import sys

class cMyToolTip( ToolTip.Hovertip ):
    '''Tooltip base class with improved tooltip placement
    '''
    def __init__(self, button, text):
        ToolTip.Hovertip.__init__(self, button, text)
        self.button = button

    def GetApp(self):
        '''Return the top level widget of the widget that we are the tooltip for
        '''
        master = self.button
        try:
            while (master.master.__class__ != Tk ):
                master = master.master
        except AttributeError:
            pass
        return master

    def showtip(self):
        if self.tipwindow:
            return
        self.tipwindow = tw = Toplevel(self.button)
        tw.wm_overrideredirect(1)

        self.showcontents()
        tw.update_idletasks()
        # now the width and height of the tooltip window is known

        # The tip window must be completely outside the button;
        # otherwise when the mouse enters the tip window we get
        # a leave event and it disappears, and then we get an enter
        # event and it reappears, and so on forever :-(
        #
        # Additionally the tooltip should be placed completely within the application.
        # (Placing within the screen is difficult to achieve in multi monitor setups
        #  as winfo_screenheight() and winfo_vrootheight() do not work as expected)

        app = self.GetApp()
        xmin = app.winfo_rootx()
        xmax = xmin + app.winfo_width()
        ymin = app.winfo_rooty()
        ymax = ymin + app.winfo_height()

        if ( self.button.winfo_rootx() + 20 + tw.winfo_width() < xmax ):
            x = self.button.winfo_rootx() + 20
            #print( "1:x=%r" % x )
        else:
            x = xmax - tw.winfo_width() - 10
            #print( "2:x=%r" % x )
        if ( self.button.winfo_rooty() + self.button.winfo_height() + tw.winfo_height() + 1 < ymax ):
            y = self.button.winfo_rooty() + self.button.winfo_height() + 1
            #print( "3:y=%r" % y )
        else:
            y = self.button.winfo_rooty() - tw.winfo_height() - 1
            #print( "4:y=%r" % y )
        #print( "winfo_vrootheight=%r" % tw.winfo_vrootheight() )
        #print( "winfo_screenheight=%r" % tw.winfo_screenheight() )
        #print( "GetApp()=%r" % (self.GetApp()) )
        sys.stdout.flush()
        tw.wm_geometry("+%d+%d" % (x, y))



class cImageTooltip( cMyToolTip ):
    '''class to display tooltips using an image
    '''
    def __init__(self, button, image):
        '''Add image as tooltip for button
        '''
        cMyToolTip.__init__(self, button, "")
        self.image = image

    def showcontents(self):
        # Overridden from base class
        label = Label(self.tipwindow, image=self.image,
                      background="#ffffe0", relief=SOLID, borderwidth=1)
        label.pack()

class cSelectiveToolTip( cMyToolTip ):
    '''class to display tooltips using a callback to determine actual tool tip text
    '''
    def __init__(self, button, callback):
        '''Add image as tooltip for button
        '''
        cMyToolTip.__init__(self, button, "")
        self.callback = callback

    def showcontents(self):
        # Overridden from base class
        label = Label(self.tipwindow, text=self.callback(self.button), justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1)
        label.pack()
        #ToolTip.TooltipBase.showcontents(self, self.callback(self.button) )
        #pass

class cSelectiveImageToolTip( cMyToolTip ):
    '''class to display tooltips using a callback to determine actual tool tip image
    '''
    def __init__(self, button, callback):
        '''Add image as tooltip for button
        '''
        cMyToolTip.__init__(self, button, "")
        self.callback = callback

    def showcontents(self):
        # Overridden from base class
        label = Label(self.tipwindow, image=self.callback(self.button),
                      background="#ffffe0", relief=SOLID, borderwidth=1)
        label.pack()

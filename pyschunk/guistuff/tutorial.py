# -*- coding: UTF-8 -*-
'''
Created on 07.08.2013

@author: Osswald2
'''

from tkinter import * #@UnusedWildImport

from . import colors
from . import fonts
import math
from . import unisymbols  # @UnresolvedImport

g_tutorials = dict()
g_tutorial_step = 1
g_app = None

def GetSortedTutorials():
    global g_tutorials
    return sorted( g_tutorials.values(), key=lambda t : t.order )


def StartTutorial(event=None):  # @UnusedVariable
    try:
        g_tutorials[g_tutorial_step].Show()
    except KeyError:
        g_tutorials[GetSortedTutorials()[0].order].Show()

def sign( v ):
    if ( v < 0 ):
        return -1
    elif ( v == 0 ):
        return 0
    return 1



class cTutorial( object ):
    '''Class to show up info to teach users the usage of the program

    You can limit the shown tool tip to be shown within the area of the application by
    setting the g_app module global variable here.

    \param masters - a single widget or a list of widgets for which this is the tutorial step
    \param placement - one of N S E W NE NW SE SW or "C". The turial window is placed in that direction of the masters
                       "C" means center: the tutorial windows is centered over the masters
    \param text - the tutorial text to show. The line delimiters "\n" must be placed manually.
    \param order - the order of this tutorial step. Must be a unique integer.
                   Consecutive steps may be use non consecutive order numbers
                   (to simplify later insertion of further tutorial steps).
    \param before_callback - callback that is called before showing the tutorial step
    \param after_callback - callback that is called after hiding the tutorial step
    '''
    def __init__( self, masters, placement, text, order, before_callback=None, after_callback=None ):
        if ( type( masters ) in [tuple,list] ):
            self.masters = masters
        else:
            self.masters = [masters]
        self.placement = placement
        self.text = text
        self.order = order
        self.tl  = None
        self.tl2 = None
        self.before_callback = before_callback
        self.after_callback = after_callback

        self.AddTutorialStep()

    def AddTutorialStep(self):
        global g_tutorials
        if ( self.order in g_tutorials ):
            raise ValueError( "Tutorial with order %d already exists!" % self.order )
        g_tutorials[self.order] = self

    def GetTutorialStepNumber(self):
        for (i,t) in enumerate( GetSortedTutorials() ):
            if ( t == self ):
                return i
        raise ValueError( "self not in g_tutorials???")

    def cbPrevious(self,event=None):  # @UnusedVariable
        global g_tutorial_step
        previous = self
        for t in GetSortedTutorials():
            if ( t == self ):
                if  ( previous != self ):
                    g_tutorial_step = previous.order
                    self.Hide()
                    previous.Show()
                return
            previous = t
        raise ValueError( "self not in g_tutorials???")

    def cbNext(self,event=None):  # @UnusedVariable
        global g_tutorial_step
        previous = None
        for t in GetSortedTutorials():
            if ( previous == self ):
                g_tutorial_step = t.order
                self.Hide()
                t.Show()
                return
            previous = t
        #already at end, nothing more to do


    def ShowContents(self):
        self.tl.config(background=colors.tutorial_background)
        if ( self.placement == S ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_up,justify=CENTER,background=colors.tutorial_background)
            l_arrow.pack(side=TOP)
        if ( self.placement == SW ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_up_right,justify=RIGHT,background=colors.tutorial_background)
            l_arrow.pack(side=TOP,anchor=NE)
        if ( self.placement == SE ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_up_left,justify=LEFT,background=colors.tutorial_background)
            l_arrow.pack(side=TOP,anchor=NW)
        if ( self.placement == E ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_left,justify=CENTER,background=colors.tutorial_background)
            l_arrow.pack(side=LEFT)
        f = Frame( self.tl, background=colors.tutorial_background, padx=10, pady=10 )
        step = self.GetTutorialStepNumber()+1
        nb_steps = len(g_tutorials)
        l_title = Label( f, text="Tutorial step %d/%d:" % (step,nb_steps),
                         font = fonts.tutorial_title,
                         justify=LEFT,
                         background=colors.tutorial_background, relief=SOLID, borderwidth=0)
        l_title.pack(side=TOP,anchor=W)

        separator = Frame(f,height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=0, pady=5, side=TOP)

        l_text = Label( f, text=self.text,
                        font = fonts.tutorial_text,
                        justify=LEFT,
                        background=colors.tutorial_background, relief=SUNKEN, borderwidth=0)
        l_text.pack(side=TOP,anchor=W)

        separator = Frame(f,height=2, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=0, pady=5, side=TOP)

        g = Frame( f, background=colors.tutorial_background )
        b_previous = Button( g, text = unisymbols.triangle_left + "   Previous step",
                             command = self.cbPrevious,
                             padx=10, pady=5, font=fonts.header,
                             foreground=colors.white,                  # foreground for active and inactive, unpressed and pressed
                             background=colors.tutorial_button_bg,      # background for active, unpressed
                             activebackground=colors.tutorial_button_ab, # background for active, pressing
                             activeforeground=colors.tutorial_button_bg,# foreground for active, pressing
                             disabledforeground=colors.grey50 )        # foreground for inactive
        b_previous.pack(side=LEFT,padx=10)
        if ( step == 1 ):
            b_previous.config(state=DISABLED)
        b_next =     Button( g, text = "Next step   " + unisymbols.triangle_right,
                             command = self.cbNext,
                             padx=10, pady=5, font=fonts.header,
                             foreground=colors.white,                  # foreground for active and inactive, unpressed and pressed
                             background=colors.tutorial_button_bg,      # background for active, unpressed
                             activebackground=colors.tutorial_button_ab, # background for active, pressing
                             activeforeground=colors.tutorial_button_bg,# foreground for active, pressing
                             disabledforeground=colors.grey50 )        # foreground for inactive
        b_next.pack(side=LEFT,padx=10)
        if ( step == nb_steps ):
            b_next.config(state=DISABLED)
        b_cancel =   Button( g, text = unisymbols.cross_diagonal + "   Stop tutorial",
                             command = self.cbCancel,
                             padx=10, pady=5, font=fonts.header,
                             foreground=colors.white,                  # foreground for active and inactive, unpressed and pressed
                             background=colors.tutorial_button_bg,      # background for active, unpressed
                             activebackground=colors.tutorial_button_ab, # background for active, pressing
                             activeforeground=colors.tutorial_button_bg,# foreground for active, pressing
                             disabledforeground=colors.grey50 )        # foreground for inactive
        b_cancel.pack(side=LEFT,padx=10)
        g.pack(side=TOP)
        if ( self.placement in (S,SW,SE,"C") ):
            f.pack(side=BOTTOM)
        elif ( self.placement in (W) ):
            f.pack(side=LEFT)
        elif ( self.placement in (E) ):
            f.pack(side=RIGHT)
        if ( self.placement in (N,NW,NE) ):
            f.pack(side=TOP)

        if ( self.placement == N ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_down,justify=CENTER,background=colors.tutorial_background)
            l_arrow.pack(side=BOTTOM)
        if ( self.placement == NW ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_down_right,justify=RIGHT,background=colors.tutorial_background)
            l_arrow.pack(side=BOTTOM,anchor=SE)
        if ( self.placement == NE ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_down_left,justify=LEFT,background=colors.tutorial_background)
            l_arrow.pack(side=BOTTOM,anchor=SW)
        if ( self.placement == W ):
            l_arrow = Label( self.tl, text=unisymbols.triangle_right,justify=CENTER,background=colors.tutorial_background)
            l_arrow.pack(side=RIGHT)

        self.tl.bind('<Prior>', self.cbPrevious )
        self.tl.bind('<Next>', self.cbNext )
        self.tl.bind('<Escape>', self.cbCancel )

    def cbCancel(self,event=None):  # @UnusedVariable
        self.Hide()

    def Hide(self):
        tw = self.tl
        tw2 = self.tl2
        self.tl  = None
        self.tl2 = None
        if tw:
            tw.destroy()
        if tw2:
            tw2.destroy()
        if ( self.after_callback ):
            self.after_callback()

    def GetApp(self):
        return g_app

    def Masters_winfo_rootx(self):
        masters_rootx =  min( [m.winfo_rootx() for m in self.masters ] )

        if ( self.GetApp() ):
            app_rootx= self.GetApp().winfo_rootx()
            return max( masters_rootx, app_rootx )
        return masters_rootx

    def Masters_winfo_rooty(self):
        masters_rooty = min( [m.winfo_rooty() for m in self.masters ] )

        if ( self.GetApp() ):
            app_rooty = self.GetApp().winfo_rooty()
            return max( masters_rooty, app_rooty )
        return masters_rooty

    def Masters_winfo_width(self):
        masters_max_rootx = max( [(m.winfo_rootx() + m.winfo_width()) for m in self.masters ] )

        if ( self.GetApp() ):
            app_max_rootx = self.GetApp().winfo_rootx() + self.GetApp().winfo_width()
            return abs(min( masters_max_rootx, app_max_rootx ) - self.Masters_winfo_rootx())
        return abs(masters_max_rootx -  self.Masters_winfo_rootx())

    def Masters_winfo_height(self):
        masters_max_rooty = max( [(m.winfo_rooty() + m.winfo_height()) for m in self.masters ] )

        if ( self.GetApp() ):
            app_max_rooty = self.GetApp().winfo_rooty() + g_app.winfo_height()
            return abs(min( masters_max_rooty, app_max_rooty ) - self.Masters_winfo_rooty())
        return abs(masters_max_rooty - self.Masters_winfo_rooty())

    def Show(self):
        if self.tl:
            return
        if ( self.before_callback ):
            self.before_callback()

        self.tl2 = tw2 = Toplevel()#self.masters)
        tw2.wm_overrideredirect(1)
        tw2.wm_attributes("-topmost", 1)
        tw2.config(background=colors.tutorial_background)
        tw2.wm_geometry("%dx%d+%d+%d" % (self.Masters_winfo_width(),self.Masters_winfo_height(),
                                         self.Masters_winfo_rootx(),self.Masters_winfo_rooty()))
        tw2.attributes("-alpha", 0.70 )

        self.tl  = tw  = Toplevel()#self.masters)
        tw.wm_overrideredirect(1)
        tw.wm_attributes("-topmost", 1)

        self.ShowContents()
        tw.update_idletasks()

        self.d = 5
        if ( self.placement == N ):
            self.x = self.Masters_winfo_rootx() + self.Masters_winfo_width()//2 - tw.winfo_width()//2
            self.y = self.Masters_winfo_rooty() - tw.winfo_height() - self.d
            self.dx=0
            self.dy=-100
        elif ( self.placement == S ):
            self.x = self.Masters_winfo_rootx() + self.Masters_winfo_width()//2 - tw.winfo_width()//2
            self.y = self.Masters_winfo_rooty() + self.Masters_winfo_height() + self.d
            self.dx=0
            self.dy=100
        elif ( self.placement == W ):
            self.x = self.Masters_winfo_rootx() - tw.winfo_width() - self.d
            self.y = self.Masters_winfo_rooty() + self.Masters_winfo_height()//2 - tw.winfo_height()//2
            self.dx=-100
            self.dy=0
        elif ( self.placement == E ):
            self.x = self.Masters_winfo_rootx() + self.Masters_winfo_width() + self.d
            self.y = self.Masters_winfo_rooty() + self.Masters_winfo_height()//2 - tw.winfo_height()//2
            self.dx=100
            self.dy=0
        elif ( self.placement == NW ):
            self.x = self.Masters_winfo_rootx() - tw.winfo_width()
            self.y = self.Masters_winfo_rooty() - tw.winfo_height()
            self.dx=-100
            self.dy=-100
        elif ( self.placement == NE ):
            self.x = self.Masters_winfo_rootx() + self.Masters_winfo_width()
            self.y = self.Masters_winfo_rooty() - tw.winfo_height()
            self.dx=100
            self.dy=-100
        elif ( self.placement == SW ):
            self.x = self.Masters_winfo_rootx() - tw.winfo_width()
            self.y = self.Masters_winfo_rooty() + self.Masters_winfo_height()
            self.dx=-100
            self.dy=100
        elif ( self.placement == SE ):
            self.x = self.Masters_winfo_rootx() + self.Masters_winfo_width()
            self.y = self.Masters_winfo_rooty() + self.Masters_winfo_height()
            self.dx=100
            self.dy=100
        elif ( self.placement == "C" ):
            self.x = self.Masters_winfo_rootx() + self.Masters_winfo_width()//2 - tw.winfo_width()//2
            self.y = self.Masters_winfo_rooty() + self.Masters_winfo_height()//2 - tw.winfo_height()//2
            self.dx=0
            self.dy=0

        tw.wm_geometry("+%d+%d" % (self.x+self.dx, self.y+self.dy))
        tw.after( 20, self.Animate )
        tw.after( 40, self.tl.focus_set ) # required to make key bindings work without extra clicking in tutorial window

        self.t=0.0

    def Animate(self):
        T0 = 0.3
        T1 = 0.5
        self.T2 = 0.7
        if ( self.t < T0 ):
            f = -1.0/T0 * self.t + 1.0
        elif ( self.t < T1 ):
            f = 0.2/(T1-T0) * (self.t-T0) + 0.0
        elif ( self.t < self.T2 ):
            f = -0.2/(self.T2-T1) * (self.t-T1) + 0.2
        else:
            f = 0.0
        #self.tl.attributes("-alpha", 1.0-f)
        self.tl.wm_geometry("+%d+%d" % (int(self.x+f*self.dx), int(self.y+f*self.dy)))
        self.t += 0.020
        if (self.t < self.T2):
            self.tl.after( 20, self.Animate )
        else:
            self.tl2.after( 20, self.Animate2 )

    def Animate2(self):
        self.t += 0.020
        alpha = 0.35 * (math.cos(5.0*(self.t-self.T2))+1.0)
        self.tl2.attributes("-alpha", alpha )
        self.tl2.after( 20, self.Animate2 )

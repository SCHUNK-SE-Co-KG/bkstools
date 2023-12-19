'''
Created on 08.08.2013

@author: Osswald2

Corporate identity stuff
'''

from tkinter import * #@UnusedWildImport
import time

import pyschunk.tools.util

from . import colors
from . import tooltip
from . import fonts
from . import widgets
import pyschunk.tools.dbg

class cTLDebugSelect(Toplevel):
    '''Debug enable/disable toplevel window

    (e.g. shown for doubleclick with middle button on logo)
    '''
    def __init__(self, title="" ):
        Toplevel.__init__( self, background=colors.schunk_background )
        self.title( "Debug output selector for %s" % title )

        asf = widgets.cAutoScrollFrame(self,background=colors.schunk_background )
        #f = asf.content
        f = Frame(asf.content,height=2, bd=1, relief=GROOVE, background=colors.schunk_background)
        def cbMousewheel(event):
            # TODO: check if we're the ones to scroll
            try:
                asf.canvas.yview_scroll(-1*(event.delta//120), "units")
            except TclError:
                pass
        widgets.BindMouseWheel( asf.canvas, cbMousewheel )


        def cbSet( debug_object, anivar ):
            #print( "cbSet d=%s ivar=%r" % (debug_object.GetDescription(),anivar.get()) )
            debug_object.SetFlag( anivar.get() )
        row=0
        for d in pyschunk.tools.dbg.GetDebugObjects():
            Label( f, text=d.GetDescription(),
                   anchor=W, justify=LEFT, font=fonts.small,
                   background=colors.schunk_background, foreground=colors.schunk_dark_blue ).grid( column=0, row=row, sticky=W )
            ivar = IntVar()
            ivar.set( int(d.GetFlag()) )
            Checkbutton( f,
                         command=lambda dd=d, iivar=ivar: cbSet( debug_object=dd, anivar=iivar ),
                         variable=ivar, onvalue=1, offvalue=0,
                         background=colors.schunk_verylight_blue      # background for active, unpressed
                         ).grid(column=1, row=row )        # foreground for inactive
            row += 1
        f.pack(fill=BOTH, padx=5, pady=5, side=TOP)
        asf.ShowContent()
        asf.pack(side=TOP)

class cInfo(object):
    '''Info widget to display text info like a status bar.
    Previous info messages are logged with time and displayed as tooltip

    To the right this includes the SCHUNK logo with a configurable double-click callback and tooltip.
    '''
    def __init__( self, master, logo_callback=None, logo_tooltip_msg=None, cb_logo_popup=None, title="" ):
        '''CTor: create widgets
        '''
        self.master = master
        self.v_info = StringVar()

        self.f_info_logo = Frame( master, height=5, bd=0, background=colors.schunk_dark_blue )
        self.l_info = Label( self.f_info_logo, background=colors.schunk_dark_blue, foreground=colors.white, textvariable=self.v_info, anchor=W, justify=LEFT, font=fonts.big)
        self.l_info.pack( side=LEFT, fill=X, expand=YES)
        self.tt_info = tooltip.cMyToolTip(self.l_info, "Log info of the program:" )

        #image = PhotoImage(data=schunk_logo,format="gif")
        image = widgets.cPathedPhotoImage(file="schunk_logo.gif",format="gif")
        self.l_logo = Label( self.f_info_logo, bd=0, image=image, anchor=E, justify=RIGHT )
        self.l_logo.image = image # keep a reference!
        self.l_logo.pack( side=RIGHT )
        if ( logo_callback ):
            self.l_logo.bind('<Double-Button-1>',logo_callback)
        if ( logo_tooltip_msg ):
            tooltip.cMyToolTip( self.l_logo, logo_tooltip_msg )
        #self.l_logo.bind('d',self.cbDebug)                    # does not work (callback is not called)
        #self.f_info_logo.bind('d',self.cbDebug )              # does not work either (callback is not called)
        #self.f_info_logo.bind('<Control-Key-d>',self.cbDebug) # nor does this
        self.l_logo.bind('<Double-Button-2>',self.cbDebug)

        self.f_extra = Frame( self.f_info_logo, background=colors.schunk_dark_blue  )
        self.f_extra.pack(side=RIGHT,expand=NO)

        self.f_info_logo.pack( side=TOP, fill=X, expand=YES, anchor=N )

        if ( cb_logo_popup ):
            self.l_logo.bind("<Button-3>", cb_logo_popup )
        self.title = title
        self.tl_debug_selector = None

    def Add( self, msg ):
        '''Add \a msg for direct display, possibly overwriting older messages.
        '''
        old = self.v_info.get()
        self.v_info.set( old.split("\n")[-1] + "\n" + msg )#
        self.AddLog(msg)
        self.master.update_idletasks()

    def AddLog( self, msg ):
        '''Add \a msg for logged display with time in tooltip.
        '''
        the_time = pyschunk.tools.util.cPrinter.DefaultGetTime(time.time())
        self.tt_info.text += "\n" + the_time + ": " + msg

    def Replace( self, msg ):
        '''Add \a msg for direct display, overwriting older messages.
        '''
        self.v_info.set(msg)
        self.AddLog(msg)
        self.master.update_idletasks()

    def cbDebug(self,event):
        '''Callback for doubleclick with middle button on logo. opens up a toplevel window to enable/disable debug messages
        '''
        print(("event=%r" % event))
        if ( self.tl_debug_selector is None ):
            self.tl_debug_selector= cTLDebugSelect( title=self.title )
            self.tl_debug_selector.protocol("WM_DELETE_WINDOW", self.DestroyToplevelDebugSelector )

    def DestroyToplevelDebugSelector( self ):
        if ( self.tl_debug_selector ):
#             try:
#                 self.t_enter_pos_geometry = self.t_enter_pos.geometry()
#                 dbg<< "remember node %d t_enter_pos_geometry=%r\n" % (self.node_no, self.t_enter_pos_geometry)
#             except TclError:
#                 # sometimes reading the geometry yields "tclError: bad window path name ".45000104"
#                 pass
            self.tl_debug_selector.destroy()
        self.tl_debug_selector = None


class cCI(object):
    '''The SCHUNK corporate identity symbol
    '''
    def __init__(self,master):
        '''CTor: create widgets
        '''
        self.f_ci1 = Frame(master, bd=0, background=colors.schunk_dark_blue )
        self.f_ci1l = Frame(self.f_ci1, bd=0, background=colors.schunk_dark_blue )
        self.f_ci1l.pack( side=LEFT, fill=BOTH, expand=YES, anchor=E )
        image = widgets.cPathedPhotoImage(file="ci1.gif",format="gif")
        self.l_ci1 = Label( self.f_ci1, bd=0, image=image, anchor=E )
        self.l_ci1.image = image # keep a reference!
        self.l_ci1.pack( side=LEFT )
        self.f_ci1r = Frame(self.f_ci1, width=50, bd=0, background=colors.schunk_light_blue )
        self.f_ci1r.pack( side=LEFT, fill=BOTH, expand=NO, anchor=E )
        self.f_ci1.pack( side=TOP, fill=X, expand=NO, anchor=N )

        self.f_ci2 = Frame(master, height=20, bd=0, background=colors.schunk_light_blue )
        self.f_ci2.pack( side=TOP, fill=X, expand=NO, anchor=N )

        self.f_ci3 = Frame(master, bd=0, background=colors.schunk_dark_blue )
        ##--- FIXed: remove this debug spinner to show hangs
        #self.v_spinner = IntVar()
        #Label(self.f_ci3,textvariable=self.v_spinner).pack( side=LEFT, anchor=W )
        #def cbSpinner():
        #    self.v_spinner.set( self.v_spinner.get() +1 )
        #    self.f_ci3.after(200,cbSpinner)
        #self.f_ci3.after( 5000, cbSpinner )
        #--
        self.f_ci3l = Frame(self.f_ci3, bd=0, background=colors.schunk_light_blue )
        self.f_ci3l.pack( side=LEFT, fill=BOTH, expand=YES, anchor=E )
        image = widgets.cPathedPhotoImage(file="ci2.gif",format="gif")
        self.l_ci3 = Label( self.f_ci3, bd=0, image=image, anchor=E )
        self.l_ci3.image = image # keep a reference!
        self.l_ci3.pack( side=LEFT )
        self.f_ci3r = Frame(self.f_ci3, bd=0, background=colors.schunk_background )
        self.f_ci3r.pack( side=LEFT, fill=BOTH, expand=YES, anchor=E )
        self.f_ci3.pack( side=TOP, fill=X, expand=NO, anchor=N )


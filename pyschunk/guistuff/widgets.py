'''
Created on 08.08.2013

@author: Osswald2

Custom widget stuff
'''

import platform
import re  # @UnusedImport
import sys
import pkg_resources
from tkinter import * #@UnusedWildImport

from pyschunk.tools.dbg import tDBG
from . import colors, fonts, tooltip, unisymbols  # @UnresolvedImport
import os.path
import collections
dbg = tDBG( False, "cyan", description="pyschunk.guistuff.widgets" )
#dbg = tDBG( True, "cyan", description="pyschunk.guistuff.widgets" )

def RunGUI( app_class, title, options, icon_file_name="schunk_dark.ico" ):
    '''Convenience function to create application, run mainloop, set icon, clean up.
    '''
    root = Tk()
    try:
        if ( platform.system() == 'Windows' ):
            icon_name =  FindFileInPaths( icon_file_name, cPathedPhotoImage.path )
            root.wm_iconbitmap( icon_name, default=icon_name )
        else:
            # On linux icons can only be xbm format, which is black and white only.
            # (Really - there is no way to get colored icons. Fullstop)
            # (Plus: no one seems to know why the extra '@' is needed...)
            icon_name = FindFileInPaths( "schunk_dark.xbm", cPathedPhotoImage.path )
            root.wm_iconbitmap( "@" + icon_name )
    except TclError as e:
        dbg << "Ignoring tkinter.TclError %r\n" % e
        pass # ignore error
    app = app_class( root, options )
    app.master.title( title )
    dbg << "Entering mainloop\n"
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # try to call normal cleanup, if available
        dbg << "Caught CTRL-C from mainloop, cleaning up\n"
        try:
            app.CBQuit()
        except AttributeError as e:
            pass
    dbg << "after mainloop\n"

    try:
        root.destroy()  # required to delete GUI while waiting in util.ConfirmExit()
    except:
        pass
    dbg << "after destroy\n"

class cDataGroup(object):
    '''Class to display tabular data which can be shown/hidden interactively
    '''
    def __init__(self, master, group_name, with_header, header_width, hide_data, row, cb_show_data=None):
        self.master = master
        self.group_name = group_name
        self.with_header = with_header
        self.header_width = header_width
        self.hide_data = hide_data
        self.row = row
        self.cb_show_data = cb_show_data

        separator = Frame(self.master, bd=1, relief=SUNKEN)
        separator.grid( row=self.row, column=0, columnspan=2, padx=0, pady=2, sticky=W+E)
        #self.row += 1

        if (with_header):
            self.l_group = Label( self.master, text=unisymbols.triangle_down + group_name, anchor=W, justify=LEFT, width=header_width, font=fonts.header, background=colors.group_header_column_background )
            self.l_group.grid( row=self.row, column=0, sticky=W+E+S+N )
            self.l_group.bind('<Double-Button-1>', self.cbHideGroupName)
            tooltip.cMyToolTip(self.l_group, "Double click in header column to expand and show data." )
        self.l_dummy = Label( self.master, text=unisymbols.triangle_down, anchor=W, justify=LEFT, width=header_width, font=fonts.header, background=colors.white )
        self.l_dummy.default_background=colors.white
        self.l_dummy.grid( row=self.row, column=1, sticky=W+E+S+N )
        self.l_dummy.bind('<Double-Button-1>', self.cbHideGroupName)
        tooltip.cMyToolTip(self.l_dummy, "Double click in header column to expand and show data." )
        if ( not self.hide_data ):
            if ( self.with_header ):
                self.l_group.grid_remove()
            self.l_dummy.grid_remove()
        self.row += 1
        self.values  = dict()
        self.headers = dict()
        self.master.groups[group_name] = self
        self.background=colors.data0_column_background
        # should call cb_show_data here if not hidden, but the callback might
        # want to use ressources that are only available after the caller has
        # made its additions via self.Add() after this CTor has finished.
        # So the caller has to do that at the appropriate time himself

    def ChangeDataBackground(self):
        if ( self.background == colors.data0_column_background ):
            self.background = colors.data1_column_background
        else:
            self.background = colors.data0_column_background

    def GetApp(self):
        return self.master.master.master.master.master.master.master

    def cbHideData(self,event):
        dbg << "Hiding data of %r\n" % self.group_name
        for v in list(self.values.values()):
            v.grid_remove()
        for v in list(self.headers.values()):
            v.grid_remove()
        if ( self.with_header ):
            self.l_group.grid()
        self.l_dummy.grid()
        if ( not event is None ):
            for m in self.GetApp().cop_modules:
                if ( m.groups[self.group_name] != self ):
                    m.groups[self.group_name].cbHideData(None)
            self.GetApp().asf_content.AdjustSize()
        self.hide_data = True

    def cbHideGroupName(self,event):
        dbg << "Hiding group name of %r\n" % self.group_name
        if ( not self.cb_show_data is None ):
            self.cb_show_data( event )

        for v in list(self.values.values()):
            v.grid()
        for v in list(self.headers.values()):
            v.grid()
        if ( self.with_header ):
            self.l_group.grid_remove()
        self.l_dummy.grid_remove()
        if ( not event is None ):
            for m in self.GetApp().cop_modules:
                if ( m.groups[self.group_name] != self ):
                    m.groups[self.group_name].cbHideGroupName(None)
        self.GetApp().asf_content.AdjustSize()
        self.hide_data = False

    def Add(self, header, value, tooltip_msg=None ):
        '''Add the next header value pair to the table
        '''
        #lately Hashable has moved from collections to collections.abc. So try either:
        try:
            Hashable = collections.abc.Hashable   # @UndefinedVariable
        except AttributeError:
            Hashable = collections.Hashable       # @UndefinedVariable

        if ( isinstance( header, Hashable  ) ):
            header_index = header
        else:
            header_index = id( header )

        if (self.with_header):
            if ( len( self.headers ) == 0 ):
                self.headers[header_index] = Frame( self.master, width=self.header_width, background=self.background )
                l1 = Label( self.headers[header_index], text=unisymbols.triangle_up, anchor=W, justify=LEFT, font=fonts.header, background=self.background )
                l1.pack(side=LEFT)
                if ( isinstance(header,Variable) ):
                    l2 = Label( self.headers[header_index], textvariable=header, anchor=E, justify=RIGHT, font=fonts.header, background=self.background )
                else:
                    l2 = Label( self.headers[header_index], text=header, anchor=E, justify=RIGHT, font=fonts.header, background=self.background )
                l2.pack(side=RIGHT)
                l1.bind('<Double-Button-1>', self.cbHideData)
                l2.bind('<Double-Button-1>', self.cbHideData)
            else:
                if ( isinstance(header,Variable) ):
                    self.headers[header_index] = Label( self.master, textvariable=header, anchor=E, justify=RIGHT, width=self.header_width, font=fonts.header, background=self.background )
                else:
                    self.headers[header_index] = Label( self.master, text=header, anchor=E, justify=RIGHT, width=self.header_width, font=fonts.header, background=self.background )
            self.headers[header_index].grid( row=self.row, column=0, sticky=W+E+S+N )
            self.headers[header_index].bind('<Double-Button-1>', self.cbHideData)
            tooltip.cMyToolTip(self.headers[header_index], "Double click in header column to collapse category and hide data." )

        if ( type(value) in (str,int,int,float) ):
            self.values[header_index] = Label( self.master, text=value, anchor=E, justify=LEFT, font=fonts.value, background=self.background )
        elif ( isinstance(value,Variable) ):
            self.values[header_index] = Label( self.master, textvariable=value, anchor=E, justify=RIGHT, font=fonts.value, background=self.background )
        else:
            self.values[header_index] = value
        self.values[header_index].default_background = self.background
        self.values[header_index].grid( row=self.row, column=1, sticky=W+E )
        if ( not tooltip_msg is None ):
            tooltip.cMyToolTip( self.values[header_index], tooltip_msg )
        if ( self.hide_data ):
            self.values[header_index].grid_remove()
            if (self.with_header):
                self.headers[header_index].grid_remove()
        self.row += 1
        self.ChangeDataBackground()
        return self.values[header_index]

#-----------------------------------------------------------------
class cButtonBox(Frame):
    '''A simple box for buttons
    '''
    def __init__(self, master=None):
        '''CTor
        '''
        Frame.__init__(self, master, class_="cButtonBox" )
        self.buttons = []
        self.nb_buttons = 0

    #def AddButton( self, text=None, image=None, image_file=None, image_format=None, command=None, underline=None, ipadx=None, ipady=None, padx=None, pady=None, bg=None, fg=None, tooltip_msg=None, background=None ):
    def AddButton( self, *args, **kwargs ):
        '''Add a button to the button box, layout int auto-grid horizontally
        \return the created button/checkbutton widget.
        All standard button constructor arguments can be used plus:
        - image_file / image_format which will automatically create an image for the button
        - padding parameters will be forwareded to the grid layouter
        - tooltip_msg will trigger generation of a tool tip
        - button_class to specify a different widget class, e.g. Checkbutton
        '''
        image = None
        tooltip_msg = None
        if ( "image_file" in list(kwargs.keys()) ):
            image = cPathedPhotoImage( file=kwargs["image_file"], format=kwargs["image_format"] )
            kwargs["image"] = image
            del kwargs["image_file" ]
            del kwargs["image_format" ]

        grid_kwargs=dict()
        for kw in [ "padx", "pady", "ipadx", "ipady" ]:
            if kw in list(kwargs.keys()):
                grid_kwargs[kw] = kwargs[kw]
                del kwargs[kw]

        if "tooltip_msg" in list(kwargs.keys()):
            tooltip_msg = kwargs["tooltip_msg"]
            del kwargs["tooltip_msg"]

        button_class = Button
        if ( "button_class" in list(kwargs.keys()) ):
            button_class = kwargs["button_class"]
            del kwargs["button_class"]

        b = button_class( self, *args, **kwargs )
        b.grid( row=0, column=self.nb_buttons, **grid_kwargs )
        if ( not image is None ):
            b.image = image # keep a reference!

        if ( not tooltip_msg is None ):
            tooltip.cMyToolTip( b, tooltip_msg )

        self.buttons.append( b )
        self.nb_buttons += 1

        return b

class StatusBar(Frame):
    '''A status bar to display text messages.
    '''
    def __init__( self, master, text="" ):
        Frame.__init__( self, master )
        self.label = Label( self, bd=1, text=text, relief=SUNKEN, anchor=W, font=fonts.header, background=colors.schunk_background )
        self.label.pack(fill=X)
        self.id_after = None

    def Set(self, msg, clear_after_ms=5000 ):
        '''Set the status bar text to \a msg. Remove the text after \a clear_after_ms ms
        If \a clear_after_ms is 0 then the \a msg will remain and not be cleared.
        '''
        self.label.config( text=msg )
        self.label.update_idletasks()
        if ( not self.id_after is None ):
            self.after_cancel(self.id_after)
        if (clear_after_ms>0):
            self.id_after = self.after( clear_after_ms, self.Clear )

    def Clear(self):
        '''Clear previous message by setting text to display to "".
        '''
        self.label.config(text="")
        self.label.update_idletasks()
        self.id_after = None

def GeometryToSizePosition( geometry ):
    '''Return a (size,positon) pair of string for the gemetry
    Example: return ("123x456","+100-500") for input "123x456+100-500"
             return ("835x880","+2341+-224")  for input "835x880+2341+-224"
    '''
    mo = re.match( "([+-]?\d+x[+-]?\d+)([+-]?[+-]\d+[+-]?[+-]\d+)", geometry )
    try:
        return (mo.group(1),mo.group(2))
    except AttributeError as e:
        dbg << "GeometryToSizePosition( %s ) failed %r\n" % (geometry,e)
        return ("","")

def EventToStr( ev ):
    '''Return a string describing ev
    '''
    res = ""
    for (k,v) in list(ev.__dict__.items()):
        res += "%s=%r\n" % (k,v)


class cAutoScrollbar(Scrollbar):
    '''A scrollbar that hides itself if it's not needed.  only
    works if you use the grid geometry manager.

    Source: http://effbot.org/zone/tkinter-autoscrollbar.htm
    '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")

class cAutoScrollFrame(Frame):
    '''A frame with automatic scroll bars.
    Use self.content member as master of your content.
    Call ShowContent() after you created your content
    '''
    def __init__(self,master,**kw):
        Frame.__init__(self,master,kw)
        vscrollbar = cAutoScrollbar(self) # Setting colors does not work
        vscrollbar.grid(row=0, column=1, sticky=N+S)
        hscrollbar = cAutoScrollbar(self, orient=HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky=E+W)

        self.canvas = Canvas(self,
                             bg=colors.schunk_background,
                             bd=0,
                             highlightthickness=0,
                             yscrollcommand=vscrollbar.set,
                             xscrollcommand=hscrollbar.set)
        self.canvas.grid(row=0, column=0, sticky=N+S+E+W)

        vscrollbar.config(command=self.canvas.yview)
        hscrollbar.config(command=self.canvas.xview)

        #--- Make the canvas expandable:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        #--- Create canvas contents:
        self.content = Frame(self.canvas)

    def ShowContent(self):
        self.canvas.create_window(0, 0, anchor=NW, window=self.content )
        self.content.update_idletasks()
        self.AdjustSize()

    def AdjustSize(self):
        self.content.update_idletasks()
        self.canvas.configure( width=self.content.winfo_width() )
        self.canvas.configure( height=self.content.winfo_height() )
        self.content.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

def FindFileInPaths( filename, path ):
    '''Helper function to find first \a filename in \a path (list of directories)
    \return filename with path if found, else None
    '''
    for p in path:
        f = os.path.join(p,filename)
        if ( os.path.isfile( f ) ):
            # found, so return in
            #print( "found file in path %r" % ( f ) )
            return f
        else:
            #print( "%r not in %r" % ( filename,p ) )
            pass

    return None


class cPathedPhotoImage(PhotoImage):
    """Improved PhotoImage to search for image files in a configurable path
    """

    # path is a static or class member variable and determines the directory
    # search path to look for image files. The default is to try the given
    # file name directly (so it can be an absolute path), to look in the
    # current directory and in the "pic" subdirectoy.
    # The module level below this class definition will add further
    # paths: The directory of the calling script and its pic subdirectory.
    #
    # In order to add a path for all subsequent cPathedPhotoImage creations
    # use something like this:
    #   cPathedPhotoImage.path.append("your-dir")
    # before creating the cPathedPhotoImage objects.
    #
    # In order to use a different path for one cPathedPhotoImage creation only
    # use the path=something keyword parameter of the constructor
    path = ["", ".", "pic", ]

    def __init__(self, name=None, cnf={}, master=None, **kw):
        """Create an image with NAME.

        Valid resource names: data, format, file, gamma, height, palette,
        width, path."""
        try:
            filename=kw["file"]
            if ( "path" in list(kw.keys()) ):
                path = kw["path"]
            else:
                path = cPathedPhotoImage.path

            f = FindFileInPaths( filename, path )
            if ( f ):
                kw["file"] = f
        except KeyError:
            pass #keyword argument "file" not given => nothing more to do
        PhotoImage.__init__(self, name, cnf, master, **kw)

#--- Make sure that the image files can be found:
# Add the the directory where the calling script is located (which is
# not necessarily the current dir) and its pic subdir to the
# image search path:

# Use setuptools to find package path:
try:
    package_path = pkg_resources.resource_filename(__name__, "pic" )  # @UndefinedVariable
    cPathedPhotoImage.path.append( package_path )
except NotImplementedError as e:
    # as of 2016-08-08 pkg_resources.resource_filename() only supported for .egg, not .zip
    pass

# Add other dirs as well (just in case):
script_dir         = os.path.dirname( sys.argv[0] )
script_dir_abs     = os.path.abspath( script_dir )
script_dir_abs_pic = os.path.join( script_dir_abs, "pic" )

cPathedPhotoImage.path.append( script_dir_abs )
cPathedPhotoImage.path.append( script_dir_abs_pic )

# Add the the directory where this package is located (which is
# not necessarily the current dir) and its pic subdir to the
# image search path:
package_dir         = os.path.dirname( __file__ )
package_dir_abs     = os.path.abspath( package_dir )
package_dir_abs_pic = os.path.join( package_dir_abs, "pic" )

cPathedPhotoImage.path.append( package_dir_abs )
cPathedPhotoImage.path.append( package_dir_abs_pic )


_mouse_wheel_callbacks = []
def cbMouseWheel( event ):
    global _mouse_wheel_callbacks
    for cb in _mouse_wheel_callbacks:
        cb(event)

def BindMouseWheel( master, callback ):
    '''Mouse wheel events can only be bound with bind_all.
    So if several different widgets need to handle mouse wheel events we need to dispatch these ourselves.
    \param master - the master widget, required to access bind_all
    \param callback - a callback function that will be called with the normal event parameter on a mouse wheel event.
                      if multiple callbacks are installed then these have to decide by themselves if they are applicable
    '''
    _mouse_wheel_callbacks.append( callback )
    master.bind_all("<MouseWheel>", cbMouseWheel)


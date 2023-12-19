'''
Created on 13.08.2013

@author: Osswald2
'''
import unittest
from . import widgets        # @UnresolvedImport
from tkinter import * #@UnusedWildImport


class Test_GeometryToSizePosition(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test1(self):
        s = "123x456"
        p = "+100-500"
        g = s+p
        self.assertEqual( widgets.GeometryToSizePosition( g ), (s,p) )

def main_cAutoScrollFrame():
    root = Tk()

    Label(root,text="adadfad adf ad").grid(row=0,column=0)#pack(side=TOP)
    auto_scroll_frame = widgets.cAutoScrollFrame( root )

    frame = auto_scroll_frame.content
    rows = 20
    for i in range(1,rows):
        for j in range(1,30):
            button = Button(frame, padx=7, pady=7, text="[%d,%d]" % (i,j))
            button.grid(row=i, column=j, sticky='news')
    auto_scroll_frame.ShowContent()
    auto_scroll_frame.grid(row=1,column=0, sticky=N+S+E+W)#pack(side=TOP,expand=YES,fill=BOTH)
    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)
    auto_scroll_frame.AdjustSize()
    s=widgets.StatusBar(root)
    s.Set( "a message in a status bar", 0)
    s.grid(row=3,column=0)#pack(side=TOP,expand=YES,fill=X)
    root.mainloop()

def main_cAutoScrollBars():
    # original example without cAutoScrollFrame:
    #
    # create scrolled canvas
    root = Tk()

    vscrollbar = widgets.cAutoScrollbar(root)
    vscrollbar.grid(row=0, column=1, sticky=N+S)
    hscrollbar = widgets.cAutoScrollbar(root, orient=HORIZONTAL)
    hscrollbar.grid(row=1, column=0, sticky=E+W)

    canvas = Canvas(root,
                    yscrollcommand=vscrollbar.set,
                    xscrollcommand=hscrollbar.set)
    canvas.grid(row=0, column=0, sticky=N+S+E+W)

    vscrollbar.config(command=canvas.yview)
    hscrollbar.config(command=canvas.xview)

    # make the canvas expandable
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    #
    # create canvas contents

    frame = Frame(canvas)
    frame.rowconfigure(1, weight=1)
    frame.columnconfigure(1, weight=1)

    rows = 5
    for i in range(1,rows):
        for j in range(1,10):
            button = Button(frame, padx=7, pady=7, text="[%d,%d]" % (i,j))
            button.grid(row=i, column=j, sticky='news')

    canvas.create_window(0, 0, anchor=NW, window=frame)

    frame.update_idletasks()

    canvas.config(scrollregion=canvas.bbox("all"))

    root.mainloop()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

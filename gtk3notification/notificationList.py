#!/usr/bin/env python3

# V. 0.9.70

import os, shutil, sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf, GObject, Pango

from notListCfg import *

_curr_dir = os.getcwd()

NOT_DIR = os.path.join(_curr_dir, "notifications")
if not os.path.exists(NOT_DIR):
    sys.exit()

_display = Gdk.Display.get_default()
display_type = GObject.type_name(_display.__gtype__)
is_wayland = display_type=="GdkWaylandDisplay"
if is_wayland:
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import GtkLayerShell
    ret = GtkLayerShell.is_supported()
    if ret == False:
        print("Error, layershell required.")
        is_wayland = None

class MainApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Notwin")
        # self.set_icon_from_file(icon_dir+"/menu.svg")
        self.connect("delete-event", self._to_close)
        #self.connect('hide', self.on_hide)
        #self.connect('show', self.on_show)
        self.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key-press-event', self.on_key_pressed)
        if CLOSE_FOCUS_LOST:
            self.connect('focus-out-event', self.on_lost_focus)
        #
        self.set_border_width(4)
        self.set_resizable(True)
        # # vertical box for all the widgets
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.set_homogeneous(False)
        self.add(self.main_box)
        #
        if is_wayland:
            GtkLayerShell.init_for_window(self)
            # GtkLayerShell.auto_exclusive_zone_enable(self)
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
            self.WX = 0
            self.WY = 0
            if WIN_POSITION != "":
                try:
                    self.WX,self.WY = WIN_POSITION.split(":")
                    GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, 1)
                    GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
                    GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, int(self.WX))
                    GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, int(self.WY))
                except:
                    self.WX = 0
                    self.WY = 0
            self.set_size_request(WWIDTH, WHEIGHT)
        else:
            self.set_default_size(WWIDTH, WHEIGHT)
            if WIN_POSITION != "":
                try:
                    self.WX,self.WY = WIN_POSITION.split(":")
                    self.move(int(self.WX),int(self.WY))
                except:
                    self.WX = 0
                    self.WY = 0
            else:
                self.set_position(Gtk.WindowPosition.CENTER)
            self.set_skip_pager_hint(True)
            self.set_keep_above(True)
            # self.set_skip_taskbar_hint(True)
            self.set_decorated(False)
            # self.set_focus(self)
            # self.set_focusable(True)
            # self.main_box.grab_focus()
            # self.set_state_flags(Gtk.StateFlags.FOCUSED, True)
        ## NOTIFICATIONS
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        # self.list_box.connect('row-activated', self.on_row_activated)
        _scrolledwin0 = Gtk.ScrolledWindow()
        # _scrolledwin0.set_property("propagate-natural-width", True)
        _scrolledwin0.set_overlay_scrolling(True)
        _scrolledwin0.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_box.pack_start(_scrolledwin0, True, True, 6)
        _scrolledwin0.add(self.list_box)
        # separator
        separator = Gtk.Separator()
        separator.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(separator, False, False, 0)
        # # remove all the notifications stored at once
        # self.remove_all_nots = Gtk.Button(label="Remove all")
        # self.main_box.pack_start(self.remove_all_nots, False, False, 0)
        # self.remove_all_nots.connect('clicked', self.on_remove_all_nots)
        #
        self.dnd_btn = Gtk.ToggleButton(label=DONOTDISTURBOFF)
        self.main_box.pack_start(self.dnd_btn, False, False, 0)
        if os.path.exists(os.path.join(_curr_dir,"notificationdonotuse_3")):
            self.dnd_btn.set_active(True)
            self.dnd_btn.set_label(DONOTDISTURBON)
        self.dnd_btn.connect('toggled', self.on_dnd_btn)
        #
        self._clip_dir = os.path.join(_curr_dir,"notifications")
        self._not_list = sorted(os.listdir(self._clip_dir), reverse=True)
        self._my_nots = {}
        #
        self.on_add_nots()
        
        
        ###
        self.show_all()
    
    def on_add_nots(self):
        for el in self._not_list:
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            row = Gtk.ListBoxRow()
            row.set_name("notrow")
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            # row.add(hbox)
            row.add(vbox)
            vbox.add(hbox)
            
            row.iid = el
            
            _image_path = os.path.join(self._clip_dir,el,"image.png")
            if os.path.exists(_image_path):
                _pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(_image_path,NOTIMGSIZE,NOTIMGSIZE,True)
                _img = Gtk.Image.new_from_pixbuf(_pix)
                hbox.pack_start(_img,False,False,0)
            
            _not_text = ""
            with open(os.path.join(self._clip_dir,el,"notification"),"r") as _f:
                _not_text = _f.read()
            
            try:
                (_app,_summ,_body) = _not_text.split("\n\n\n@\n\n\n")
            except:
                _app = ""
                _summ = ""
                _body = ""
            if _app == "" and _summ == "" and _body == "":
                continue
            
            self._my_nots[el] = _body.encode()
            
            _summ_lbl = Gtk.Label()
            _summ_lbl.set_single_line_mode(False)
            _summ_lbl.set_line_wrap(True)
            _summ_lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            _summ_lbl.set_use_markup(True)
            _summ_lbl.set_markup(_app+"\n"+f"<b>{_summ}</b>")
            _summ_lbl.set_xalign(0)
            _summ_lbl.set_selectable(True)
            _summ_lbl.set_name("summlbl")
            hbox.pack_start(_summ_lbl,True,True,4)
            
            _remove_btn = Gtk.Button()
            try:
                pixbuf = Gtk.IconTheme().load_icon("gtk-delete", 24, Gtk.IconLookupFlags.FORCE_SVG)
                _img = Gtk.Image.new_from_pixbuf(pixbuf)
                _remove_btn.set_image(_img)
            except:
                _remove_btn.set_label("X")
            
            _remove_btn.connect('clicked', self.on_remove_btn, el, row)
            hbox.pack_start(_remove_btn,False,False,0)
            
            if _body != "":
                _exp = Gtk.Expander.new()
                _body_lbl = Gtk.Label(label=_body)
                _body_lbl.set_use_markup(True)
                _body_lbl.set_single_line_mode(False)
                _body_lbl.set_line_wrap(True)
                _body_lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                _body_lbl.set_xalign(0)
                _body_lbl.set_selectable(True)
                _body_lbl.set_name("bodlbl")
                _exp.add(_body_lbl)
                vbox.add(_exp)
            
            self.list_box.add(row)
    
    def on_remove_btn(self, btn, el, row):
        try:
            _path = os.path.join(_curr_dir,"notifications",el)
            shutil.rmtree(_path)
            del self._my_nots[el]
            _selected_row = self.list_box.get_selected_row()
            self.list_box.remove(row)
            if _selected_row == row:
                self.body_lbl.set_markup(" ")
        except:
            pass
    
    # # remove all the notifications stored at once
    # def on_remove_all_nots(self, w):
    #     try:
    #         _not_dir = os.path.join(_curr_dir, "notifications")
    #         for el in self._not_list:
    #             print(el)
    #             shutil.rmtree(os.path.join( _not_dir, el))
    #             del self._my_nots[el]
    #         self.list_box.unselect_all()
    #         self.list_box.remove_all()
    #     except:
    #         pass
    
    def on_dnd_btn(self, w):
        _dnd = os.path.join(_curr_dir,"notificationdonotuse_3")
        if w.get_active():
            try:
                _f = open(_dnd, "w")
                _f.close()
                if not os.path.exists(_dnd):
                    w.set_active(False)
                else:
                    w.set_label(DONOTDISTURBON)
            except:
                pass
        else:
            try:
                os.remove(_dnd)
                if os.path.exists(_dnd):
                    w.set_active(True)
                else:
                    w.set_label(DONOTDISTURBOFF)
            except:
                pass
    
    # press esc to hide
    def on_key_pressed(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == "Escape":
            # self.hide()
            Gtk.main_quit()
    
    def _to_close(self, w, e):
        Gtk.main_quit()
        
    # close when lost focus
    def on_lost_focus(self, w, e):
        #if self.not_hide == 1:
        #    return
        #self.hide()
        Gtk.main_quit()

if __name__ == '__main__':
    _app = MainApp()
    Gtk.main()

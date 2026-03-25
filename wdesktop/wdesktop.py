#!/usr/bin/env python3

# V. 0.1

import sys, os, shutil, signal
import gi
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk4LayerShell as GtkLayerShell
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Graphene, Gsk, Gio, Pango, GObject
from subprocess import Popen
import datetime


def _error_log(msg):
    print(msg)

_display = Gdk.Display.get_default()
display_type = GObject.type_name(_display.__gtype__)

is_wayland = display_type=="GdkWaylandDisplay"
if not is_wayland:
    _error_log("Wayland required.")
    sys.exit()
# if is_wayland:
    # ret = GtkLayerShell.is_supported()
    # if ret == False:
        # _error_log("Gtk layer shell support required.")
        # sys.exit()

_curr_dir = os.getcwd()
_HOME = os.path.expanduser("~")

WIDTH = 1280
HEIGHT = 720

############### SETTINGS
# BORDER MARGINS
TOP_MARGIN = 0
BOTTOM_MARGIN = 0
LEFT_MARGIN = 0
RIGHT_MARGIN = 0

X_PAD = 0
Y_PAD = 0

# space between icon and text
ICON_TEXT_SEPARATOR = 10
# space between items - do not change
ITEM_MARGIN = 8
ITEM_MARGIN_V = 8
# item placement: 0 top to bottom - 1 left to right
ITEM_PLACEMENT = 0
# widget width and height and space between items
widget_size_w = 148+ITEM_MARGIN
widget_size_h = 148+ITEM_MARGIN_V
# icon size - square
w_icon_size = 64
# font family
_fm = "Sans"
# item font size - 0 to disable
_font_size = 0
# corner radius of the text
ROUNDED_CORNER = 3
# number of lines of each item text
NUMBER_OF_TEXT_LINES = 2
# the text colour
TEXT_NORMAL_COLOR = "#000000"
TEXT_HIGHLIGHT_COLOR = "#000000"
# normal text background colour
TEXT_BACKGROUND_NORMAL = "#aaaaaaaa"
# highlight text background colour
TEXT_BACKGROUND_HIGHLIGHT = "#88ccffaa"
# track changes in the recycle bin
USE_TRASH = 1
TRASH_NAME = "Recycle bin"
# application to launch to open the trashcan
TRASH_APP = "yad"
TRASH_PATH = os.path.join(os.path.expanduser("~"), ".local/share/Trash/files")
TRASH_INFO = os.path.join(os.path.expanduser("~"), ".local/share/Trash/info")
# thumbnails
USE_THUMBS = 1
#
XDG_CACHE_LARGE = os.path.join(_curr_dir,"sh_thumbnails/large/")
# removable devices
USE_MEDIA = 1
# list of device do not track
MEDIA_SKIP = []
# appliation to launch to open the file manager
DEVICE_APP = "yad"

## rubberband
# the border width
R_LINE_WIDTH = 1
# the border color
R_BORDER_COLOR = "#00000088"
# the inside color
R_COLOR = "#88ccff20"
# corner radius
R_RADIUS = 6

# background: 0 image - 1 colour
USE_BACKGROUND_COLOR = 0
BACKGROUND_COLOR = "#777777"

###################

if USE_TRASH == 1:
    if not os.path.exists(TRASH_PATH):
        try:
            os.makedirs(TRASH_PATH)
        except:
            USE_TRASH = 0

    if not os.path.exists(TRASH_INFO):
        try:
            os.makedirs(TRASH_INFO)
        except:
            USE_TRASH = 0

if USE_THUMBS == 1:
    # create the dir if it doesnt exist
    if not os.path.exists(XDG_CACHE_LARGE):
        try:
            os.makedirs(XDG_CACHE_LARGE)
        except:
            USE_THUMBS = 0

if USE_THUMBS == 1:
    from pythumb import create_thumbnail

if USE_MEDIA == 1:
    import dbus, psutil

# the desktop folder
DESKTOP_PATH = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)
DESKTOP_FILES = os.listdir(DESKTOP_PATH)
for el in DESKTOP_FILES[:]:
    if el[0] == ".":
        DESKTOP_FILES.remove(el)

def convert_size(fsize2):
    if fsize2 == 0 or fsize2 == 1:
        sfsize = str(fsize2)+" byte"
    elif fsize2//1024 == 0:
        sfsize = str(fsize2)+" bytes"
    elif fsize2//1048576 == 0:
        sfsize = str(round(fsize2/1024, 3))+" KB"
    elif fsize2//1073741824 == 0:
        sfsize = str(round(fsize2/1048576, 3))+" MB"
    elif fsize2//1099511627776 == 0:
        sfsize = str(round(fsize2/1073741824, 3))+" GiB"
    else:
        sfsize = str(round(fsize2/1099511627776, 3))+" GiB"
    return sfsize 


class trashItem(Gtk.Widget):
    def __init__(self, _parent, _w, _h, _iw, _fm, _fs, _itext, _type):
        super().__init__()
        self._parent = _parent
        self._w = _w
        self._h = _h
        self._iw = _iw
        self._fm = _fm
        self._fs = _fs
        self._itext = _itext
        self._type = _type
        self._ci = 0
        self._img = "e" # "e" empty - "f" full
        self._state = 0
        self._v = 0
        #
        self.set_size_request(self._w, self._h)
        # mouse click - left
        gesture1 = Gtk.GestureClick.new()
        gesture1.set_button(1) # left
        gesture1.connect("pressed", self.on_pressed_left)
        self.add_controller(gesture1)
        # mouse click - right
        gesture2 = Gtk.GestureClick.new()
        gesture2.set_button(3) # right
        gesture2.connect("pressed", self.on_pressed_right)
        self.add_controller(gesture2)
        #
        self._snapshot = None
        
    def on_pressed_left(self, o,n,x,y):
        if n == 2:
            try:
                Popen(TRASH_APP.split(" "))
            except Exception as E:
                itemWindow(self._parent, "Error", str(E))
        
    def on_pressed_right(self, o,n,x,y):
        self._parent.context_menu_trash(x,y)
    
    def find_icon_thumb(self):
        img = None
        if self._type == "R":
            if len(os.listdir(TRASH_PATH)) > 0:
                img = "trashcan_full"
                self._img = "f"
            else:
                img = "trashcan_empty"
        return img
    
    # _obj is snapshot
    def do_snapshot(self, _obj):
        if self._snapshot == None:
            self._snapshot = _obj
        ######### icon
        img = self.find_icon_thumb()
        if self._type == "R":
            display = Gdk.Display.get_default()
            icon_theme = Gtk.IconTheme.get_for_display(display)
            if icon_theme.has_icon(img):
                icon_paintable = icon_theme.lookup_icon(
                    img,
                    None, 
                    self._iw,
                    1,
                    Gtk.TextDirection.NONE,
                    Gtk.IconLookupFlags.NONE
                    )
                icon_file_path = icon_paintable.get_file().get_path()
                texture = Gdk.Texture.new_from_filename(icon_file_path)
            else:
                icon_file_path = os.path.join(_curr_dir,"icons", img+".svg")
                texture = Gdk.Texture.new_from_filename(icon_file_path)
        # ICON rect
        # 1
        size_rect = Graphene.Rect()
        gx = int((self._w-self._iw)/2)+LEFT_MARGIN+int(X_PAD/2) # relative x to this widget left
        gy = int(ITEM_MARGIN/2)+int(Y_PAD/2) #+TOP_MARGIN # relative y to this widget top 
        size_rect.init(gx, gy, self._iw, self._iw)
        # LINEAR= 0 NEAREST= 1 TRILINEAR= 2
        _obj.append_scaled_texture(texture, 0, size_rect)
        #
        ######### text
        colour = Gdk.RGBA()
        if self._v in [1,2] or self._state == 1:
            colour.parse(TEXT_HIGHLIGHT_COLOR)
        else:
            colour.parse(TEXT_NORMAL_COLOR)
        
        font = Pango.FontDescription.new()
        font.set_family(self._fm)
        if self._fs > 6:
            font.set_size(self._fs * Pango.SCALE)
        #
        context = self.get_pango_context()
        layout = Pango.Layout(context)
        layout.set_font_description(font)
        #
        if self._itext == "" or self._itext == None:
            self._itext = "(None)"
        #
        new_text = ""
        tmp_text = self._itext[0]
        _lines = 1
        for _c in self._itext[1:]:
            tmp_text += _c
            layout.set_text(tmp_text)
            #
            if layout.get_pixel_size().width > (self._w-ITEM_MARGIN*2):
                new_text += tmp_text[:-1]+"\n"
                tmp_text = tmp_text[-1]
                _lines += 1
                # set a limit to the text height
                if _lines > 10:
                    tmp_text += "\n(...)"
                    break
        #
        if _lines == 1:
            new_text = self._itext
        elif _lines == NUMBER_OF_TEXT_LINES:
            new_text += tmp_text
        elif _lines > (NUMBER_OF_TEXT_LINES-1) and (self._state == 0 and self._v == 0):
            new_text_tmp = new_text.split("\n")
            new_text = ""
            i = 0
            while i < (NUMBER_OF_TEXT_LINES-1):
                new_text += (new_text_tmp[i]+"\n")
                i += 1
            else:
                new_text += new_text_tmp[i][:-3]+"..."
        elif tmp_text != "":
            new_text += tmp_text
        else:
            new_text = new_text.split("\n")[0][:-3]+"..."
        ##
        _th = layout.get_pixel_size().height
        ######## TEXT BACKGROUND
        _ac = Gdk.RGBA()
        _ac.parse(TEXT_BACKGROUND_NORMAL)
        _ac.to_string()
        # ##
        # _ac = Gdk.RGBA()
        # if self._v == 0:
            # _ac.parse(TEXT_BACKGROUND_NORMAL)
            # _ac.to_string()
        # else:
            # _ac.parse(TEXT_BACKGROUND_HIGHLIGHT)
            # _ac.to_string()
        ### calculate the text size
        # calculate the text size
        layout.set_text(new_text)
        _ttw = self._w-ITEM_MARGIN
        _tth = layout.get_pixel_size().height
        #
        # 2 - text background
        # text background rect
        r = Graphene.Rect()
        _pad = int(((self._w-ITEM_MARGIN*2)-_ttw)/2)
        _tbx = ITEM_MARGIN+_pad-1+LEFT_MARGIN
        _tby = self._iw+ICON_TEXT_SEPARATOR+int(Y_PAD/2) #+TOP_MARGIN
        _tbw = _ttw+1
        _tbh = _tth
        r.init(_tbx, _tby, _tbw, _tbh)
        ########
        _rounded_r = Gsk.RoundedRect()
        _rounded_r.init_from_rect(r, ROUNDED_CORNER)
        _rounded_r.normalize()
        _obj.push_rounded_clip(_rounded_r)
        _obj.append_color(_ac, r)
        _obj.pop()
        #
        #### item name
        # starting height
        _text_height = 0
        list_text = new_text.split("\n")
        for _t in list_text:
            if _t[-1] == " ":
                _t = _t[:-1]
            layout.set_text(_t)
            text_width = layout.get_pixel_size().width
            # 3 - text
            point = Graphene.Point()
            point.x = int((self._w - text_width)/2)
            point.y = ITEM_MARGIN_V + int(Y_PAD/2) + self._iw + _text_height #+TOP_MARGIN
            #
            _obj.save()
            _obj.translate(point)
            _obj.append_layout(layout, colour)
            _obj.restore()
            #
            _text_height += layout.get_pixel_size().height
    
    # def do_measure(self, orientation, for_size):
        # return self._w, self._w, -1, -1
    

class deviceItem(Gtk.Widget):
    def __init__(self, _parent, _w, _h, _iw, _fm, _fs, _itext, _type, _icon):
        super().__init__()
        self._parent = _parent
        self._w = _w
        self._h = _h
        self._iw = _iw
        self._fm = _fm
        self._fs = _fs
        self._itext = _itext
        self._type = _type
        self._ci = 0
        self._icon = _icon
        self._state = 0
        self._v = 0
        #
        self.set_size_request(self._w, self._h)
        # mouse motion
        event_controller = Gtk.EventControllerMotion.new()
        event_controller.connect("enter", self.on_enter)
        event_controller.connect("leave", self.on_leave)
        self.add_controller(event_controller)
        # mouse click - left
        gesture1 = Gtk.GestureClick.new()
        gesture1.set_button(1) # left
        gesture1.connect("pressed", self.on_pressed_left)
        self.add_controller(gesture1)
        # mouse click - right
        gesture2 = Gtk.GestureClick.new()
        gesture2.set_button(3) # right
        gesture2.connect("pressed", self.on_pressed_right)
        self.add_controller(gesture2)
        #
        self._snapshot = None
        
    def on_enter(self, _c, _x, _y) -> bool:
        self._v = 1
        self.queue_draw()
        return True

    def on_leave(self, _c) -> bool:
        self._v = 0
        self.queue_draw()
        return True
    
    def on_pressed_left(self, o,n,x,y):
        if n == 2:
            try:
                # file manager to open
                Popen(DEVICE_APP.split(" "))
            except Exception as E:
                itemWindow(self._parent, "Error", str(E))
        
    def on_pressed_right(self, o,n,x,y):
        self._parent.context_menu_device(self, x,y)
    
    # _obj is snapshot
    def do_snapshot(self, _obj):
        if self._snapshot == None:
            self._snapshot = _obj
        ######### icon
        if self._type == "D":
            display = Gdk.Display.get_default()
            icon_theme = Gtk.IconTheme.get_for_display(display)
            img = os.path.basename(self._icon).split(".")[0]
            if icon_theme.has_icon(img):
                icon_paintable = icon_theme.lookup_icon(
                    img,
                    None, 
                    self._iw,
                    1,
                    Gtk.TextDirection.NONE,
                    Gtk.IconLookupFlags.NONE
                    )
                icon_file_path = icon_paintable.get_file().get_path()
                texture = Gdk.Texture.new_from_filename(icon_file_path)
            else:
                icon_file_path = os.path.join(_curr_dir,self._icon)
                texture = Gdk.Texture.new_from_filename(icon_file_path)
        # 1
        size_rect = Graphene.Rect()
        gx = int((self._w-self._iw)/2)+LEFT_MARGIN+int(X_PAD/2) # relative x to this widget left
        gy = int(ITEM_MARGIN/2)+int(Y_PAD/2) #+TOP_MARGIN # relative y to this widget top 
        size_rect.init(gx, gy, self._iw, self._iw)
        _obj.append_scaled_texture(texture, 0, size_rect)
        #
        ######### text
        colour = Gdk.RGBA()
        if self._v in [1,2] or self._state == 1:
            colour.parse(TEXT_HIGHLIGHT_COLOR)
        else:
            colour.parse(TEXT_NORMAL_COLOR)
        
        font = Pango.FontDescription.new()
        font.set_family(self._fm)
        if self._fs > 6:
            font.set_size(self._fs * Pango.SCALE)
        #
        context = self.get_pango_context()
        layout = Pango.Layout(context)
        layout.set_font_description(font)
        #
        if self._itext == "" or self._itext == None:
            self._itext = "(None)"
        #
        new_text = ""
        tmp_text = self._itext[0]
        _lines = 1
        for _c in self._itext[1:]:
            tmp_text += _c
            layout.set_text(tmp_text)
            #
            if layout.get_pixel_size().width > (self._w-ITEM_MARGIN*2):
                new_text += tmp_text[:-1]+"\n"
                tmp_text = tmp_text[-1]
                _lines += 1
                # set a limit to the text height
                if _lines > 10:
                    tmp_text += "\n(...)"
                    break
        #
        if _lines == 1:
            new_text = self._itext
        elif _lines == NUMBER_OF_TEXT_LINES:
            new_text += tmp_text
        elif _lines > (NUMBER_OF_TEXT_LINES-1) and (self._state == 0 and self._v == 0):
            new_text_tmp = new_text.split("\n")
            new_text = ""
            i = 0
            while i < (NUMBER_OF_TEXT_LINES-1):
                new_text += (new_text_tmp[i]+"\n")
                i += 1
            else:
                new_text += new_text_tmp[i][:-3]+"..."
        elif tmp_text != "":
            new_text += tmp_text
        else:
            new_text = new_text.split("\n")[0][:-3]+"..."
        ##
        _th = layout.get_pixel_size().height
        ######## TEXT BACKGROUND
        _ac = Gdk.RGBA()
        _ac.parse(TEXT_BACKGROUND_NORMAL)
        _ac.to_string()
        ### calculate the text size
        layout.set_text(new_text)
        _ttw = self._w-ITEM_MARGIN
        _tth = layout.get_pixel_size().height
        # 2
        r = Graphene.Rect()
        _pad = int(((self._w-ITEM_MARGIN*2)-_ttw)/2)
        _tbx = ITEM_MARGIN+_pad-1+LEFT_MARGIN
        _tby = self._iw+ICON_TEXT_SEPARATOR+int(Y_PAD/2) #+TOP_MARGIN
        _tbw = _ttw+1
        _tbh = _tth
        r.init(_tbx, _tby, _tbw, _tbh)
        ########
        _rounded_r = Gsk.RoundedRect()
        _rounded_r.init_from_rect(r, ROUNDED_CORNER)
        _rounded_r.normalize()
        _obj.push_rounded_clip(_rounded_r)
        _obj.append_color(_ac, r)
        _obj.pop()
        #
        #### item name
        # starting height
        _text_height = 0
        list_text = new_text.split("\n")
        for _t in list_text:
            if _t[-1] == " ":
                _t = _t[:-1]
            layout.set_text(_t)
            text_width = layout.get_pixel_size().width
            # 3
            point = Graphene.Point()
            point.x = int((self._w - text_width)/2)
            point.y = ITEM_MARGIN_V + int(Y_PAD/2) + self._iw + _text_height #+TOP_MARGIN
            #
            _obj.save()
            _obj.translate(point)
            _obj.append_layout(layout, colour)
            _obj.restore()
            #
            _text_height += layout.get_pixel_size().height
    
    # def do_measure(self, orientation, for_size):
        # return self._w, self._w, -1, -1
    

class customItem(Gtk.Widget):
    def __init__(self, _parent, _w, _h, _iw, _fm, _fs, _itext):
        super().__init__()
        self._parent = _parent
        self._w = _w # width
        self._h = _h # height
        self._iw = _iw # icon width and height
        self._fm = _fm # font family
        self._fs = _fs # font size
        self._itext = _itext # label
        self._ci = 0 # custom image
        ####################
        
        self._file = Gio.File.new_for_path(os.path.join(DESKTOP_PATH, self._itext))
        self._file_info = self._file.query_info("standard::*,owner::user", Gio.FileQueryInfoFlags.NONE,None)
        
        ################
        # 0 inactive - 1 active mouse over - 2 active mouse selected
        self._v = 0
        self._snapshot = None
        #
        self.set_size_request(self._w, self._h)
        #
        # 0 unselected - 1 selected
        self._state = 0
        # mouse motion
        event_controller = Gtk.EventControllerMotion.new()
        event_controller.connect("enter", self.on_enter)
        event_controller.connect("leave", self.on_leave)
        self.add_controller(event_controller)
        # mouse click - left
        gesture1 = Gtk.GestureClick.new()
        gesture1.set_button(1) # left
        gesture1.connect("pressed", self.on_pressed)
        gesture1.connect("released", self.on_released)
        self.add_controller(gesture1)
        #
        self.left_mouse_pressed = 0
        # mouse click - right
        gesture2 = Gtk.GestureClick.new()
        gesture2.set_button(3) # right
        gesture2.connect("pressed", self.on_pressed_right)
        self.add_controller(gesture2)
        #
        self.right_mouse_pressed = 0
        
    def on_enter(self, _c, _x, _y) -> bool:
        if self._parent.left_click_setted == 0 and self._state == 0:
            self._v = 1
            self.queue_draw()
        return True

    def on_leave(self, _c) -> bool:
        if self._parent.left_click_setted == 0 and self._state == 0:
            self._v = 0
            self.queue_draw()
        return True
    
    def on_pressed_right(self, o,n,x,y):
        # the item is not selected
        if self not in self._parent.selection_widget_found:
            # deselect all
            for item in self._parent.selection_widget_found[:]:
                self._parent.selection_widget_found.remove(item)
                item._state = 0
                item._v = 0
                item.queue_draw()
            
            self._state = 1
            self._v = 2
            self.queue_draw()
            self._parent.selection_widget_found.append(self)
            self._parent.context_menu(self,x,y,1)
        # the item was already selected
        elif len(self._parent.selection_widget_found) == 1:
            self._parent.context_menu(self,x,y,1)
        else:
            self._parent.context_menu(self,x,y,2)
    
    # left mouse button pressed
    def on_pressed(self, o,n,x,y):
        self.left_mouse_pressed = 1
        
        if len(self._parent.selection_widget_found) > 1 and self._parent.ctrl_pressed == 0:
            return
        
        ## deselect all and select the pointed item
        # ctrl is for multi selection
        if self._parent.ctrl_pressed == 0:
            if self._parent.selection_widget_found != []:
                for _wdg in self._parent.selection_widget_found[:]:
                    _wdg._state = 0
                    _wdg._v = 0
                    _wdg.queue_draw()
                self._parent.selection_widget_found = []
        
        self._parent.selection_widget_found.append(self)
        
        self._state = not self._state
        if self._state == 0:
            self._v = 0
        elif self._state == 1:
            self._v = 2
        self.queue_draw()
    
    def on_released(self, o,n,x,y):
        self.left_mouse_pressed = 0
        if len(self._parent.selection_widget_found) > 1 and self._parent.ctrl_pressed == 0:
            # deselet all and select the pointed item
            if self._parent.selection_widget_found != []:
                for _wdg in self._parent.selection_widget_found[:]:
                    _wdg._state = 0
                    _wdg._v = 0
                    _wdg.queue_draw()
                self._parent.selection_widget_found = []
            
            self._parent.selection_widget_found.append(self)
            
            self._state = not self._state
            if self._state == 0:
                self._v = 0
            elif self._state == 1:
                self._v = 2
            self.queue_draw()
    
    def find_icon_thumb(self, _mime):
        if _mime in ["application/x-zerosize", "inode/directory"]:
            return None
        md5 = create_thumbnail(self._itext,DESKTOP_PATH, _mime, XDG_CACHE_LARGE)
        if str(md5) != "Null":
            thumb_file = os.path.join(XDG_CACHE_LARGE, str(md5)+".png")
            if os.path.exists(thumb_file):
                return thumb_file
        return None
    
    # _obj is snapshot
    def do_snapshot(self, _obj):
        if self._snapshot == None:
            self._snapshot = _obj
        ######## ICON
        ret = None
        icon_mime = self._file_info.get_content_type()
        if USE_THUMBS == 1:
            ret = self.find_icon_thumb(icon_mime)
        if ret == None:
            display = Gdk.Display.get_default()
            icon_theme = Gtk.IconTheme.get_for_display(display)
            # Returns a GtkIconPaintable
            # icon_mime = self._file_info.get_content_type()
            icon_names = Gio.content_type_get_icon(icon_mime).get_names()
            for _ic in icon_names:
                if icon_theme.has_icon(_ic):
                    icon_paintable = icon_theme.lookup_icon(
                        _ic,
                        None, 
                        self._iw,
                        1,
                        Gtk.TextDirection.NONE,
                        Gtk.IconLookupFlags.NONE
                        )
                    break
            else:
                icon_paintable = icon_theme.lookup_icon(
                    'application-x-zerosize',
                    None, 
                    self._iw,
                    1,
                    Gtk.TextDirection.NONE,
                    Gtk.IconLookupFlags.NONE
                    )
            
            icon_file_path = icon_paintable.get_file().get_path()
            if not os.path.exists(icon_file_path):
                icon_file_path = os.path.join(_curr_dir, "icons", "icon.svg")
            texture = Gdk.Texture.new_from_filename(icon_file_path)
        else:
            icon_file_path = ret
            texture = Gdk.Texture.new_from_filename(icon_file_path)
            self._ci = 1 # custom icon
        #
        texture_w = texture.get_width()
        texture_h = texture.get_height()
        t_rx = 1
        t_ry = 1
        new_iw = self._iw
        new_ih = self._iw
        if texture_w > texture_h:
            t_rx = texture_h/texture_w
            if t_rx < 1:
                new_ih = self._iw*t_rx
        elif texture_w < texture_h:
            t_ry = texture_w/texture_h
            if t_ry < 1:
                new_iw = self._iw*t_ry
        # ICON rect
        size_rect = Graphene.Rect()
        # 1 - icon
        gx = int((self._w-new_iw)/2)+LEFT_MARGIN+int(X_PAD/2) # relative x to this widget left
        gy = int(ITEM_MARGIN/2)+int(Y_PAD/2) #+TOP_MARGIN # relative y to this widget top 
        size_rect.init(gx, gy, new_iw, new_ih)
        # LINEAR= 0 NEAREST= 1 TRILINEAR= 2
        _obj.append_scaled_texture(texture, 0, size_rect) # scale the image
        ########### end ICON
        ######### text
        colour = Gdk.RGBA()
        if self._v in [1,2] or self._state == 1:
            colour.parse(TEXT_HIGHLIGHT_COLOR)
        else:
            colour.parse(TEXT_NORMAL_COLOR)
        
        font = Pango.FontDescription.new()
        font.set_family(self._fm)
        if self._fs > 6:
            font.set_size(self._fs * Pango.SCALE)
        #
        context = self.get_pango_context()
        layout = Pango.Layout(context)
        layout.set_font_description(font)
        #
        if self._itext == "" or self._itext == None:
            self._itext = "(None)"
        #
        new_text = ""
        tmp_text = self._itext[0]
        _lines = 1
        #
        for _c in self._itext[1:]:
            tmp_text += _c
            layout.set_text(tmp_text)
            #
            if layout.get_pixel_size().width > (self._w-ITEM_MARGIN*2):
                new_text += tmp_text[:-1]+"\n"
                tmp_text = tmp_text[-1]
                _lines += 1
                # set a limit to the text height
                if _lines > 10:
                    tmp_text += "\n(...)"
                    break
        #
        if _lines == 1:
            new_text = self._itext
        elif _lines == NUMBER_OF_TEXT_LINES:
            new_text += tmp_text
        elif _lines > (NUMBER_OF_TEXT_LINES-1) and (self._state == 0 and self._v == 0):
            new_text_tmp = new_text.split("\n")
            new_text = ""
            i = 0
            while i < (NUMBER_OF_TEXT_LINES-1):
                new_text += (new_text_tmp[i]+"\n")
                i += 1
            else:
                new_text += new_text_tmp[i][:-3]+"..."
        elif tmp_text != "":
            new_text += tmp_text
        else:
            new_text = new_text.split("\n")[0][:-3]+"..."
        ##
        _th = layout.get_pixel_size().height
        ######### text background rect and rectangle
        _ac = Gdk.RGBA()
        if self._v == 0:
            _ac.parse(TEXT_BACKGROUND_NORMAL)
            _ac.to_string()
        else:
            _ac.parse(TEXT_BACKGROUND_HIGHLIGHT)
            _ac.to_string()
        ##### TEXT
        # calculate the text size
        layout.set_text(new_text)
        _ttw = self._w-ITEM_MARGIN
        _tth = layout.get_pixel_size().height
        #
        # 2 - text background
        # text background rect
        r = Graphene.Rect()
        _pad = int(((self._w-ITEM_MARGIN*2)-_ttw)/2)
        _tbx = ITEM_MARGIN+_pad-1+LEFT_MARGIN
        _tby = self._iw+ICON_TEXT_SEPARATOR+int(Y_PAD/2)#+TOP_MARGIN
        _tbw = _ttw+1
        _tbh = _tth
        r.init(_tbx, _tby, _tbw, _tbh)
        #
        ### text background - rectangle
        _rounded_r = Gsk.RoundedRect()
        _rounded_r.init_from_rect(r, ROUNDED_CORNER)
        _rounded_r.normalize()
        _obj.push_rounded_clip(_rounded_r)
        _obj.append_color(_ac, r)
        _obj.pop()
        #
        #### item name
        # starting height
        _text_height = 0
        list_text = new_text.split("\n")
        for _t in list_text:
            if _t[-1] == " ":
                _t = _t[:-1]
            layout.set_text(_t)
            text_width = layout.get_pixel_size().width
            # 3 - text
            point = Graphene.Point()
            point.x = int((self._w - text_width)/2)
            point.y = ITEM_MARGIN_V + int(Y_PAD/2) + self._iw + _text_height #+TOP_MARGIN
            #
            _obj.save()
            _obj.translate(point)
            _obj.append_layout(layout, colour)
            _obj.restore()
            #
            _text_height += layout.get_pixel_size().height
    
    # def do_measure(self, orientation, for_size):
        # return self._w, self._w, -1, -1
       
        
class itemWindow(Gtk.Window):
    def __init__(self, _parent, _msg1, _msg2):
        super().__init__()
        self._parent = _parent
        self.set_modal(True)
        self.set_transient_for(self._parent)
        self.set_destroy_with_parent(True)
        # self.set_decorated(False)
        self.set_transient_for(self._parent)
        self.connect("close-request", self._close)
        
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box1)
        lbl1 = Gtk.Label(label="<b>"+_msg1+"</b>")
        lbl1.set_use_markup(True)
        self.box1.append(lbl1)
        lbl2 = Gtk.Label(label=_msg2)
        self.box1.append(lbl2)
        btn_close = Gtk.Button(label="Close")
        btn_close.connect("clicked", self._close)
        self.box1.append(btn_close)
        
        self.connect("map", self.on_show)
        
        self.present()
        
    
    def on_show(self, _w=None):
        _w = self.get_surface()
    
    def _close(self, _w=None):
        self.close()
    

class operationWindow(Gtk.Window):
    def __init__(self, _parent, _msg1, _msg2):
        super().__init__()
        self._parent = _parent
        self.set_modal(True)
        self.set_transient_for(self._parent)
        self.set_destroy_with_parent(True)
        # self.set_decorated(False)
        self.set_transient_for(self._parent)
        self.connect("close-request", self._close)
        
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box1)
        lbl1 = Gtk.Label(label="<b>"+_msg1+"</b>")
        lbl1.set_use_markup(True)
        self.box1.append(lbl1)
        self.lbl2 = Gtk.Label(label=_msg2)
        self.lbl2.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.box1.append(self.lbl2)
        
        btn_cancel_op = Gtk.Button(label="Cancel")
        btn_cancel_op.connect("clicked", self._cancel)
        self.box1.append(btn_cancel_op)
        
        self.present()
        
    def _cancel(self, w):
        self._parent.cancel_op = 1
        self._close()
        
    def _close(self, _w=None):
        self.close()
    

class deviceProperty(Gtk.Window):
    def __init__(self, _parent, _data):
        super().__init__()
        self._parent = _parent
        self.set_modal(True)
        self.set_transient_for(self._parent)
        self.set_destroy_with_parent(True)
        # self.set_decorated(False)
        self.set_transient_for(self._parent)
        self.connect("close-request", self._close)
        self._data = _data
        
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box1)
        
        _grid = Gtk.Grid.new()
        self.box1.append(_grid)
        
        # data = [label, vendor, model, device_size, file_system, bool(read_only), mountpoint, ddevice, media_type]
        lbl_label = Gtk.Label(label="<b>Label</b>  ")
        lbl_label.set_use_markup(True)
        lbl_label.set_xalign(0)
        _grid.attach(lbl_label,0,0,1,1)
        lbl_label1 = Gtk.Label(label=self._data[0])
        lbl_label1.set_xalign(0)
        _grid.attach_next_to(lbl_label1,lbl_label,Gtk.PositionType.RIGHT,1,1)
        
        lbl_vendor = Gtk.Label(label="<b>Vendor</b>  ")
        lbl_vendor.set_use_markup(True)
        lbl_vendor.set_xalign(0)
        _grid.attach(lbl_vendor,0,1,1,1)
        lbl_vendor1 = Gtk.Label(label=self._data[1])
        lbl_vendor1.set_xalign(0)
        _grid.attach_next_to(lbl_vendor1,lbl_vendor,Gtk.PositionType.RIGHT,1,1)
        
        lbl_model = Gtk.Label(label="<b>Model</b>  ")
        lbl_model.set_use_markup(True)
        lbl_model.set_xalign(0)
        _grid.attach(lbl_model,0,2,1,1)
        lbl_model1 = Gtk.Label(label=self._data[2])
        lbl_model1.set_xalign(0)
        _grid.attach_next_to(lbl_model1,lbl_model,Gtk.PositionType.RIGHT,1,1)
        
        lbl_size = Gtk.Label(label="<b>Size</b>  ")
        lbl_size.set_use_markup(True)
        lbl_size.set_xalign(0)
        _grid.attach(lbl_model,0,3,1,1)
        lbl_size1 = Gtk.Label(label=self._data[3])
        lbl_size1.set_xalign(0)
        _grid.attach_next_to(lbl_size1,lbl_size,Gtk.PositionType.RIGHT,1,1)
        
        lbl_fs = Gtk.Label(label="<b>File system</b>  ")
        lbl_fs.set_use_markup(True)
        lbl_fs.set_xalign(0)
        _grid.attach(lbl_fs,0,4,1,1)
        lbl_fs1 = Gtk.Label(label=self._data[4])
        lbl_fs1.set_xalign(0)
        _grid.attach_next_to(lbl_fs1,lbl_fs,Gtk.PositionType.RIGHT,1,1)
        
        lbl_ro = Gtk.Label(label="<b>Read only</b>  ")
        lbl_ro.set_use_markup(True)
        lbl_ro.set_xalign(0)
        _grid.attach(lbl_ro,0,5,1,1)
        lbl_ro1 = Gtk.Label(label=self._data[5])
        lbl_ro1.set_xalign(0)
        _grid.attach_next_to(lbl_ro1,lbl_ro,Gtk.PositionType.RIGHT,1,1)
        
        lbl_mo = Gtk.Label(label="<b>Mount point</b>  ")
        lbl_mo.set_use_markup(True)
        lbl_mo.set_xalign(0)
        _grid.attach(lbl_mo,0,6,1,1)
        lbl_mo1 = Gtk.Label(label=self._data[6])
        lbl_mo1.set_xalign(0)
        _grid.attach_next_to(lbl_mo1,lbl_mo,Gtk.PositionType.RIGHT,1,1)
        
        lbl_dev = Gtk.Label(label="<b>Device</b>  ")
        lbl_dev.set_use_markup(True)
        lbl_dev.set_xalign(0)
        _grid.attach(lbl_dev,0,7,1,1)
        lbl_dev1 = Gtk.Label(label=self._data[7])
        lbl_dev1.set_xalign(0)
        _grid.attach_next_to(lbl_dev1,lbl_dev,Gtk.PositionType.RIGHT,1,1)
        
        lbl_mt = Gtk.Label(label="<b>Media type</b>  ")
        lbl_mt.set_use_markup(True)
        lbl_mt.set_xalign(0)
        _grid.attach(lbl_mt,0,8,1,1)
        lbl_mt1 = Gtk.Label(label=self._data[8])
        lbl_mt1.set_xalign(0)
        _grid.attach_next_to(lbl_mt1,lbl_mt,Gtk.PositionType.RIGHT,1,1)
        
        btn_close = Gtk.Button(label="Close")
        btn_close.connect("clicked", self._close)
        self.box1.append(btn_close)
        
        self.present()
        
    def _close(self, _w=None):
        self.close()

class myRubberBand(Gtk.Widget):
    def __init__(self, _parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = _parent
        self._snapshot = None
        self._w = 0
        self._h = 0
        
    # _obj is snapshot
    def do_snapshot(self, _obj):
        if self._snapshot == None:
            self._snapshot = _obj
        #
        _ac = Gdk.RGBA()
        _ac.parse(R_COLOR)
        _ac.to_string()
        #
        r = Graphene.Rect()
        r.init(0, 0, self._parent.end_x, self._parent.end_y)
        #
        _rounded_r = Gsk.RoundedRect()
        _rounded_r.init_from_rect(r, ROUNDED_CORNER)
        _rounded_r.normalize()
        
        border_width = R_LINE_WIDTH
        outline_color = Gdk.RGBA()
        outline_color.parse(R_BORDER_COLOR)
        outline_color.to_string()
        
        rounded_rect = Gsk.RoundedRect()
        rounded_rect.init_from_rect(r, R_RADIUS) 
    
        _obj.append_border(
                rounded_rect,
                [border_width, border_width, border_width, border_width],
                [outline_color, outline_color, outline_color, outline_color]
            )
        
        _obj.push_rounded_clip(_rounded_r)
        _obj.append_color(_ac, r)
        _obj.pop()
    
    
class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # self.set_default_size(WIDTH, HEIGHT)
        self.set_title("wdesktop")
        
        signal.signal(signal.SIGINT, self.sigtype_handler)
        signal.signal(signal.SIGTERM, self.sigtype_handler)
        
        self.connect("close-request", self._to_close)
        self.connect("destroy", self._to_close)
        
        #### SETTINGS
        # widget width and height and space between items
        self.widget_size_w = widget_size_w
        self.widget_size_h = widget_size_h
        # icon size - square
        self.w_icon_size = w_icon_size
        # font family
        self._fm = _fm
        # item font size - 0 to disable
        self._font_size = _font_size
        
        # num_monitor = self._display.get_n_monitors()
        self._display = _display
        _monitors = self._display.get_monitors()
        num_monitor = len(_monitors)
        if num_monitor:
            # self._monitor = Gdk.Display.get_default().get_monitor(0)
            self._monitor = _monitors[0]
            self.screen_width = self._monitor.get_geometry().width
            self.screen_height = self._monitor.get_geometry().height
            #
            self.set_size_request(self.screen_width,self.screen_height)
        else:
            sys.exit()
        #
        # icon theme change tracking
        display = Gdk.Display.get_default()
        icon_theme = Gtk.IconTheme.get_for_display(self._display)
        icon_theme.connect("changed", self.on_icon_theme_changed)
        # keyboard
        keycontroller = Gtk.EventControllerKey()
        keycontroller.connect('key-pressed', self.on_key_pressed)
        keycontroller.connect('key-released', self.on_key_released)
        self.add_controller(keycontroller)
        
        self.ctrl_pressed = 0
        self.shift_pressed = 0
        self.escape_pressed = 0
        
        ######## rows and columns
        global TOP_MARGIN
        global BOTTOM_MARGIN
        global LEFT_MARGIN
        global RIGHT_MARGIN
        global ITEM_MARGIN
        global X_PAD
        global Y_PAD
        #
        self.num_rows = int((self.screen_height-TOP_MARGIN-BOTTOM_MARGIN)/self.widget_size_h)
        self.num_columns = int((self.screen_width-LEFT_MARGIN-RIGHT_MARGIN)/self.widget_size_w)
        ret_row = self.screen_height-(self.num_rows*self.widget_size_h)
        ret_column = self.screen_width-(self.num_columns*self.widget_size_w)
        #
        X_PAD = int((ret_column/(self.num_columns+1)))
        if X_PAD > 0:
            if (X_PAD/2) != 0:
                X_PAD -= 1
            LEFT_MARGIN += X_PAD
            self.widget_size_w += X_PAD
            RIGHT_MARGIN += (ret_column-X_PAD*self.num_columns)
        #
        Y_PAD = int((ret_row/(self.num_rows+1)))
        if Y_PAD > 0:
            if (Y_PAD/2) != 0:
                Y_PAD -= 1
            TOP_MARGIN += Y_PAD
            self.widget_size_h += Y_PAD
            BOTTOM_MARGIN += (ret_row-Y_PAD*self.num_rows)
        #
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("mydesktop")
        
        ###
        if USE_BACKGROUND_COLOR == 1:
            css = ".mydesktop {background-color: "+BACKGROUND_COLOR+";}"
        else:
            image_path = os.path.join(_curr_dir,"wallpaper.png")
            if os.path.exists(image_path):
                css = ".mydesktop {background-image:url(file://"+"{}".format(image_path)+"); background-size: cover;}"
            else:
                css = ".mydesktop {background-color: grey;}"
        
        ###
        
        # layershell
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.auto_exclusive_zone_enable(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BACKGROUND)
        # GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        
        self.clipboard = Gdk.Display.get_default().get_clipboard()
        
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box1)
        
        ###########
        
        # rubberband
        self.rubberband = None
        
        self._fixed = Gtk.Fixed()
        self.box1.append(self._fixed)
        
        self.da = Gtk.DrawingArea()
        self._fixed.put(self.da, 0,0)
        self.da.set_size_request(self.screen_width,self.screen_height)
        
        self.da_style_context = self.da.get_style_context()
        self.da_style_context.add_class("myda")
        #
        css_da = ".myda {background-color: transparent;}"
        #
        self.da.set_hexpand(False)
        self.da.set_vexpand(False)
        self.da.set_draw_func(self.on_draw, None)
        #
        css += css_da
        self.css_provider.load_from_data(css.encode('utf-8'))
        
        #######
        # list of customItem
        self.WIDGET_LIST = []
        # each item: row,column
        self.WIDGET_LIST_POS = []
        # each item: name, row, column
        self.WIDGET_LIST_PATH_POS = []
        # items to be placed when free slots will be available
        self.WIDGET_TO_FUTURE_PLACE = []
        # items selected by rubberband or single/multi selection
        self.selection_widget_found = []
        # item to move around
        self._item_to_move_around = None
        #
        self.widget_selected = False
        ##
        # left button - drawing area
        self.da_gesture_l = Gtk.GestureClick.new()
        self.da_gesture_l.set_button(1)
        self.da.add_controller(self.da_gesture_l)
        self.da_gesture_l.connect('pressed', self.on_da_gesture_l, 1)
        self.da_gesture_l.connect('released', self.on_da_gesture_l, 0)
        self.left_click_setted = 0
        # # center button
        # self.da_gesture_c = Gtk.GestureClick.new()
        # self.da_gesture_c.set_button(2)
        # self.da.add_controller(self.da_gesture_c)
        # self.da_gesture_c.connect('pressed', self.on_da_gesture_c)
        # self.center_click_setted = 0
        # right button
        self.da_gesture_r = Gtk.GestureClick.new()
        self.da_gesture_r.set_button(3)
        self.da.add_controller(self.da_gesture_r)
        self.da_gesture_r.connect('pressed', self.on_da_gesture_r)
        self.right_click_setted = 0
        #
        self.da.set_focusable(False)
        self.da.set_focus_on_click(False)
        #
        ## drawing area - dragging
        self.da_gesture_d = Gtk.GestureDrag.new()
        self.da_gesture_d.set_button(1)
        self.da.add_controller(self.da_gesture_d)
        # the rubberband is in course
        self.isDragging = 0
        self.da_gesture_d.connect('drag-begin', self.on_da_gesture_d_b, self.da)
        self.da_gesture_d.connect('drag-update', self.on_da_gesture_d_u, self.da)
        self.da_gesture_d.connect('drag-end', self.on_da_gesture_d_e, self.da)
        #
        ## main - dragging
        drag_controller = Gtk.DragSource()
        drag_controller.connect("prepare", self.on_drag_prepare)
        # drag_controller.connect("drag-begin", self.on_drag_begin)
        # drag_controller.connect("drag-end", self.on_drag_end)
        self.add_controller(drag_controller)
        # drop
        self.drop_controller = Gtk.DropTarget.new(type=GObject.TYPE_NONE, actions=Gdk.DragAction.COPY)
        self.drop_controller.set_gtypes([self, Gdk.FileList, str])
        self.drop_controller.connect("drop", self.on_drop)
        self.add_controller(self.drop_controller)
        
        # starting values
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        
        # the trashcan
        if USE_TRASH == 1:
            self.trash_item = None
            #
            _r = self.num_rows - 1
            _c = self.num_columns -1
            _x, _y = self.convert_pos_to_px(_r,_c)
            _trash = self.on_populate_items(_x, _y, _r, _c, "Recycle Bin", "R")
            self.trash_item = _trash
            GLib.idle_add(self.fixed_op, ("put", _trash, _trash.x, _trash.y))
            self.WIDGET_LIST.append(_trash)
            self.WIDGET_LIST_POS.append((_trash.r,_trash.c))
            self.WIDGET_LIST_PATH_POS.append(("recyclebin",_trash.r,_trash.c))
        #
        # list of devices
        self.list_devices = []
        if USE_MEDIA == 1:
            from dbus.mainloop.glib import DBusGMainLoop
            #
            DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            #
            self.proxy = self.bus.get_object("org.freedesktop.UDisks2", "/org/freedesktop/UDisks2")
            #
            self.iface = dbus.Interface(self.proxy, "org.freedesktop.DBus.ObjectManager")
            #
            self.iface.connect_to_signal('InterfacesAdded', self.device_added_callback)
            self.iface.connect_to_signal('InterfacesRemoved', self.device_removed_callback)
            #
            self.on_pop_devices()
        
        # populate WIDGET_LIST_PATH_POS for initial item position
        try:
            _f = open(os.path.join(_curr_dir,"item_positions.cfg"), "r")
            _tmp_list_path_pos = _f.read()
            _f.close()
            _l1 = _tmp_list_path_pos.split("\n")
            for _ll in _l1:
                if _ll == '':
                    continue
                item, r, c = _ll.split("/")
                if r < self.num_rows and c < self.num_columns:
                    self.WIDGET_LIST_PATH_POS.append((item, int(r), int(c)))
                else:
                    self.WIDGET_TO_FUTURE_PLACE.append(item)
        except:
            pass
        # populate the program
        for item_name in DESKTOP_FILES:
            _tr = -1
            _tc = -1
            _tx = -1
            _ty = -1
            for el in self.WIDGET_LIST_PATH_POS:
                if el[0] == item_name:
                    _tr = el[1]
                    _tc = el[2]
                    _tx, _ty = self.convert_pos_to_px(_tr,_tc)
                    break
            if _tc == -1 and _tr == -1:
                _tr, _tc = self.find_item_new_pos()
            # nothing to do now
            if _tr == -1 and _tc == -1:
                custom = self.on_populate_items(-1, -1, -1, -1, el[0], "file")
                self.WIDGET_TO_FUTURE_PLACE.append(custom)
            else:
                _tx, _ty = self.convert_pos_to_px(_tr,_tc)
                self.populate_items(_tx,_ty, _tr, _tc, item_name, "file")
            
        #
        gdir = Gio.File.new_for_path(DESKTOP_PATH)
        self.monitor = gdir.monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
        self.monitor.connect("changed", self.on_directory_changed)
        #
        # recycle bin
        if USE_TRASH:
            gtrash = Gio.File.new_for_path(TRASH_PATH)
            self.monitor_trash = gtrash.monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
            self.monitor_trash.connect("changed", self.on_trash_changed)
        

############# devices
    
    # get all the partitions at start
    def on_pop_devices(self):
        mobject = self.iface.GetManagedObjects()
        for k in mobject:
            #
            if "loop" in k:
                continue
            if 'ram' in k:
                continue
            #
            for ky in  mobject[k]:
                kk = "org.freedesktop.UDisks2.Block"
                if  str(ky) == kk:
                    bd = self.bus.get_object('org.freedesktop.UDisks2', k)
                    file_system =  bd.Get('org.freedesktop.UDisks2.Block', 'IdType', dbus_interface='org.freedesktop.DBus.Properties')
                    if file_system:
                        self.on_add_partition(k, mobject[k])
                        break
    
    # add a new connected device
    def device_added_callback(self, *args):
        for k in args[1]:
            kk = "org.freedesktop.UDisks2.Filesystem"
            if k == kk:
                mobject = self.iface.GetManagedObjects()
                self.on_add_partition(args[0], mobject[args[0]])
    
    # the device is added to the view
    # def on_add_partition(self, k, bus, kmobject):
    def on_add_partition(self, k, kmobject):
        for ky in kmobject:
            kk = "org.freedesktop.UDisks2.Block"
            if  str(ky) == kk:
                bd = self.bus.get_object('org.freedesktop.UDisks2', k)
                #
                drive = bd.Get('org.freedesktop.UDisks2.Block', 'Drive', dbus_interface='org.freedesktop.DBus.Properties')
                #
                if str(drive) == "/":
                    continue
                # 
                if "org.freedesktop.UDisks2.PartitionTable" in kmobject.keys():
                    continue
                #
                pdevice = bd.Get('org.freedesktop.UDisks2.Block', 'Device', dbus_interface='org.freedesktop.DBus.Properties')
                pdevice_dec = bytearray(pdevice).replace(b'\x00', b'').decode('utf-8')
                # skip unwanted device
                if pdevice_dec in MEDIA_SKIP:
                    continue
                #
                # do not show the disk in which the OS has been installed, and the boot partition
                ret_mountpoint = self.get_device_mountpoint(str(pdevice_dec))
                if ret_mountpoint == "/" or ret_mountpoint[0:5] == "/boot" or ret_mountpoint[0:5] == "/home":
                    continue
                #
                label = bd.Get('org.freedesktop.UDisks2.Block', 'IdLabel', dbus_interface='org.freedesktop.DBus.Properties')
                #
                size = bd.Get('org.freedesktop.UDisks2.Block', 'Size', dbus_interface='org.freedesktop.DBus.Properties')
                #
                ### 
                bd2 = self.bus.get_object('org.freedesktop.UDisks2', drive)
                #
                media_type = bd2.Get('org.freedesktop.UDisks2.Drive', 'Media', dbus_interface='org.freedesktop.DBus.Properties')
                if not media_type:
                    media_type = "N"
                #
                is_optical = bd2.Get('org.freedesktop.UDisks2.Drive', 'Optical', dbus_interface='org.freedesktop.DBus.Properties')
                #
                media_available = bd2.Get('org.freedesktop.UDisks2.Drive', 'MediaAvailable', dbus_interface='org.freedesktop.DBus.Properties')
                #
                if media_available == 0:
                    if not is_optical:
                        continue
                #
                conn_bus = bd2.Get('org.freedesktop.UDisks2.Drive', 'ConnectionBus', dbus_interface='org.freedesktop.DBus.Properties')
                #
                vendor = bd2.Get('org.freedesktop.UDisks2.Drive', 'Vendor', dbus_interface='org.freedesktop.DBus.Properties')
                model = bd2.Get('org.freedesktop.UDisks2.Drive', 'Model', dbus_interface='org.freedesktop.DBus.Properties')
                #
                if str(label):
                    disk_name = str(label)
                else:
                    if str(vendor) and str(model):
                        disk_name = str(vendor)+" - "+str(model)+" - "+str(convert_size(size))
                    elif str(vendor):
                        disk_name = str(vendor)+" - "+str(convert_size(size))
                    elif str(model):
                        disk_name = str(model)+" - "+str(convert_size(size))
                    else:
                        disk_name = str(pdevice_dec)+" - "+str(convert_size(size))
                #
                if is_optical:
                    drive_type = 1 # 0 disk - 1 optical
                else:
                    drive_type = 0 # 0 disk - 1 optical
                #
                dicon = self.getDevice(media_type, drive_type, conn_bus)
                #
                ret = GLib.idle_add(self.on_add_device, (disk_name, str(pdevice_dec), k, drive, drive_type, dicon))
                
    def find_dev_pos(self):
        # in the last column
        for c in range(self.num_rows-1):
            if (c,self.num_columns-1) not in self.WIDGET_LIST_POS:
                return ((c,self.num_columns-1))
        # or the first free slot
        return self.find_item_new_pos()
    
    def on_add_device(self, _data):
        disk_name, pdevice_dec, k, drive, drive_type, dicon = _data
        _r, _c = self.find_dev_pos()
        _x, _y = self.convert_pos_to_px(_r,_c)
        _device = self.on_populate_items(_x, _y, _r, _c, disk_name, "D", dicon)
        _device.block_device = k
        _device.drive = drive
        _device.isoptical = drive_type
        _device.device = pdevice_dec
        self.list_devices.append(_device)
        GLib.idle_add(self.fixed_op, ("put", _device, _device.x, _device.y))
        self.WIDGET_LIST.append(_device)
        self.WIDGET_LIST_POS.append((_device.r,_device.c))
        self.WIDGET_LIST_PATH_POS.append((str(pdevice_dec),_device.r,_device.c))
        
    
    # mount - unmount the device
    def mount_device(self, mountpoint, ddevice):
        if mountpoint == "N":
            ret = self.on_mount_device(ddevice, 'Mount')
            if ret == -1:
                itemWindow(self, "Info", "The device cannot be mounted.")
                return 
        else:
            ret = self.on_mount_device(ddevice, 'Unmount')
            if ret == -1:
                itemWindow(self, "Info", "Device busy.")
                return -1
        #
        return ret
    
    # self.mount_device
    def on_mount_device(self, ddevice, operation):
        ddev = ddevice.split("/")[-1]
        progname = 'org.freedesktop.UDisks2'
        objpath = os.path.join('/org/freedesktop/UDisks2/block_devices', ddev)
        intfname = 'org.freedesktop.UDisks2.Filesystem'
        try:
            obj  = self.bus.get_object(progname, objpath)
            intf = dbus.Interface(obj, intfname)
            # return the mount point or None if unmount
            ret = intf.get_dbus_method(operation, dbus_interface='org.freedesktop.UDisks2.Filesystem')([])
            return ret
        except:
            return -1
    
    # eject the media
    def eject_media(self, ddrive, mountpoint, ddevice, _type=None):
        # first unmount if the case
        if mountpoint != "N":
            ret = self.mount_device(mountpoint, ddevice)
            if ret == -1:
                # itemWindow(self, "Info", "Device busy.")
                return
        # 
        bd2 = self.bus.get_object('org.freedesktop.UDisks2', ddrive)
        can_poweroff = bd2.Get('org.freedesktop.UDisks2.Drive', 'CanPowerOff', dbus_interface='org.freedesktop.DBus.Properties')
        # 
        ret = self.on_eject(ddrive)
        if ret == -1:
            itemWindow(self, "Info", "The device cannot be ejected.")
            return
        # do not turn the usb cd reader off
        if can_poweroff and _type != 1:
            try:
                ret = self.on_poweroff(ddrive)
                # if ret == -1:
                    # itemWindow(self, "Info", "The device cannot be turned off.")
            except:
                pass
    
    # self.eject_media
    def on_eject(self, ddrive):
        progname = 'org.freedesktop.UDisks2'
        objpath  = ddrive
        intfname = 'org.freedesktop.UDisks2.Drive'
        try:
            methname = 'Eject'
            obj  = self.bus.get_object(progname, objpath)
            intf = dbus.Interface(obj, intfname)
            ret = intf.get_dbus_method(methname, dbus_interface='org.freedesktop.UDisks2.Drive')([])
            return ret
        except:
            return -1
    
    # self.eject_media1
    def on_poweroff(self, ddrive):
        progname = 'org.freedesktop.UDisks2'
        objpath  = ddrive
        intfname = 'org.freedesktop.UDisks2.Drive'
        try:
            methname = 'PowerOff'
            obj  = self.bus.get_object(progname, objpath)
            intf = dbus.Interface(obj, intfname)
            ret = intf.get_dbus_method(methname, dbus_interface='org.freedesktop.UDisks2.Drive')([])
            return ret
        except:
            return -1
    
    # get the device mount point
    def get_device_mountpoint(self, ddevice):
        ddev = ddevice.split("/")[-1]
        mount_point = self.on_get_mounted(ddev)
        return mount_point
    
    # the device is ejectable
    def get_device_can_eject(self, drive):
        bd2 = self.bus.get_object('org.freedesktop.UDisks2', drive)
        can_eject = bd2.Get('org.freedesktop.UDisks2.Drive', 'Ejectable', dbus_interface='org.freedesktop.DBus.Properties')
        return can_eject
    
    # get the mount point or return N
    def on_get_mounted(self, ddev):
        path = os.path.join('/org/freedesktop/UDisks2/block_devices/', ddev)
        bd = self.bus.get_object('org.freedesktop.UDisks2', path)
        try:
            mountpoint = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
            if mountpoint:
                mountpoint = bytearray(mountpoint[0]).replace(b'\x00', b'').decode('utf-8')
                return mountpoint
            else:
                return "N"
        except:
            return "N"
    
    # get the device icon
    def getDevice(self, media_type, drive_type, connection_bus):
        if "flash" in media_type:
            return "icons/media-flash.svg"
        if "optical" in media_type:
            return "icons/media-optical.svg"
        if connection_bus == "usb" and drive_type == 0:
            return "icons/media-removable.svg"
        if drive_type == 0:
            return "icons/drive-harddisk.svg"
        elif drive_type == 5:
            return "icons/media-optical.svg"
        #
        return "icons/drive-harddisk.svg"
    
    # the device properties
    def media_property(self, k, mountpoint, ddrive, ddevice):
        bd = self.bus.get_object('org.freedesktop.UDisks2', k)
        label = bd.Get('org.freedesktop.UDisks2.Block', 'IdLabel', dbus_interface='org.freedesktop.DBus.Properties')
        bd2 = self.bus.get_object('org.freedesktop.UDisks2', ddrive)
        vendor = bd2.Get('org.freedesktop.UDisks2.Drive', 'Vendor', dbus_interface='org.freedesktop.DBus.Properties')
        model = bd2.Get('org.freedesktop.UDisks2.Drive', 'Model', dbus_interface='org.freedesktop.DBus.Properties')
        size = bd.Get('org.freedesktop.UDisks2.Block', 'Size', dbus_interface='org.freedesktop.DBus.Properties')
        file_system =  bd.Get('org.freedesktop.UDisks2.Block', 'IdType', dbus_interface='org.freedesktop.DBus.Properties')
        read_only = bd.Get('org.freedesktop.UDisks2.Block', 'ReadOnly', dbus_interface='org.freedesktop.DBus.Properties')
        ### 
        media_type = bd2.Get('org.freedesktop.UDisks2.Drive', 'Media', dbus_interface='org.freedesktop.DBus.Properties')
        if not media_type:
            conn_bus = bd2.Get('org.freedesktop.UDisks2.Drive', 'ConnectionBus', dbus_interface='org.freedesktop.DBus.Properties')
            if conn_bus:
                media_type = conn_bus
            else:
                media_type = "N"
        #
        if not label:
            label = "(Not set)"
        if mountpoint == "N":
            mountpoint = "(Not mounted)"
            device_size = str(convert_size(size))
        else:
            mountpoint_size = convert_size(psutil.disk_usage(mountpoint).used)
            device_size = str(convert_size(size))+" - ("+mountpoint_size+")"
        if not vendor:
            vendor = "(None)"
        if not model:
            model = "(None)"
        data = [label, vendor, model, device_size, file_system, bool(read_only), mountpoint, ddevice, media_type]
        deviceProperty(self, data)
    
    # remove the disconnected device
    def device_removed_callback(self, *args):
        for k in args[1]:
            kk = "org.freedesktop.UDisks2.Filesystem"
            if k == kk:
                for _dev in self.list_devices[:]:
                    if _dev.block_device == args[0]:
                        _r = _dev.r
                        _c = _dev.c
                        _device = _dev.device
                        try:
                            ret = GLib.idle_add(self.fixed_op, ("remove", _dev))
                        except Exception as E:
                            itemWindow(self, "Error", str(E))
                            return
                        # if ret == "True":
                        if (_r,_c) in self.WIDGET_LIST_POS:
                            self.WIDGET_LIST_POS.remove((_r,_c))
                        #
                        if (_device,_r,_c) in self.WIDGET_LIST_PATH_POS:
                            self.WIDGET_LIST_PATH_POS.remove((_device,_r,_c))
                        #
                        self.list_devices.remove(_dev)
                        break

####################### end devices
    
    def on_icon_theme_changed(self, icontheme):
        for el in self.WIDGET_LIST:
            if el._ci == 0:
                el.queue_draw()
    
    def on_drag_prepare(self, ctrl, _x, _y, data=None):
        # rubberband in action, do not select anything
        if self.isDragging == 1:
            return
        
        if len(self.selection_widget_found) > 0:
            _data = ""
            for el in self.selection_widget_found:
                file_path_tmp = os.path.join(DESKTOP_PATH,el._itext)
                _fg = Gio.File.new_for_path(file_path_tmp)
                file_path = _fg.get_uri()#[7:]
                del _fg
                
                _data += (file_path+"\n")
            _data = _data[:-1]+"\r\n"
            
            if self.shift_pressed == 1:
                ctrl.set_actions(Gdk.DragAction.MOVE)
            elif self.shift_pressed == 0:
                ctrl.set_actions(Gdk.DragAction.COPY)
            
            gbytes = GLib.Bytes.new(bytes(_data, 'utf-8'))
            _atom = "text/uri-list"
            content = Gdk.ContentProvider.new_for_bytes(_atom, gbytes)
            return content
            
    # def on_drag_begin(self, ctrl, drag):
        # # icon = Gtk.WidgetPaintable.new(self)
        # # ctrl.set_icon(icon, 0, 0)
        # pass
    
    # def on_drag_end(self, ctrl, drag, data=None):
        # pass
    
    def on_drop(self, ctrl, value, _x, _y):
        # supposing internal item moving
        if len(self.selection_widget_found) > 0:
            # only one item
            if len(self.selection_widget_found) > 1:
                return
            #
            i = 0
            for el in self.selection_widget_found:
                # do_not_place = 0
                _r,_c = self.convert_px_to_pos(_x,_y)
                if _r > self.num_rows-1 or _c > self.num_columns-1:
                    break
                # do not overlay the items
                if i == 0 and (_r,_c) in self.WIDGET_LIST_POS:
                    break
                    return
                #
                x,y = self.convert_pos_to_px(_r, _c)
                # remove old position
                if (el.r, el.c) in self.WIDGET_LIST_POS:
                    self.WIDGET_LIST_POS.remove((el.r, el.c))
                if (el._itext, el.r, el.c) in self.WIDGET_LIST_PATH_POS:
                    self.WIDGET_LIST_PATH_POS.remove((el._itext, el.r, el.c))
                #
                el.x = x
                el.y = y
                el.r = _r
                el.c = _c
                # self._fixed.move(el, x, y)
                GLib.idle_add(self.fixed_op, ("move", el))
                #
                i += 1
            #
            return
        #
        _operation = ""
        if  ctrl.get_actions() == Gdk.DragAction.COPY:
            _operation = "copy"
        elif ctrl.get_actions() == Gdk.DragAction.MOVE:
            _operation = "cut"
        
        if _operation == "":
            return
        
        if isinstance(value, Gdk.FileList):
            files = value.get_files()
            self.cancel_op = -1
            OW = None
            for ff in files:
                if self.cancel_op == -1:
                    self.cancel_op = 0
                    if _operation == "copy":
                        msg1 = "Copying files..."
                    elif _operation == "cut":
                        msg1 = "Moving files..."
                    msg2 = ""
                    OW = operationWindow(self, msg1, msg2)
                if self.cancel_op == 1:
                    OW._close()
                    itemWindow(self, "Info", "Operation interrupted by the user.")
                    self.cancel_op = -1
                    break
                    return
                #
                file_name_src = ff.get_path()
                item = os.path.basename(file_name_src)
                OW.lbl2.set_label(item)
                folder_source = os.path.dirname(file_name_src)
                if folder_source == DESKTOP_PATH:
                    return
                #
                file_name = os.path.join(DESKTOP_PATH,item)
                if _operation == "copy":
                    # _operation source destination
                    try:
                        GLib.idle_add(self.item_op, ("copy", file_name_src, file_name))
                    except Exception as E:
                        itemWindow(self, "Error", str(E))
                #
                elif _operation == "cut":
                    try:
                        GLib.idle_add(self.item_op, ("cut", file_name_src, file_name))
                    except Exception as E:
                        itemWindow(self, "Error", str(E))
            #
            if OW != None:
                GLib.timeout_add(600, OW._close)
    
    def find_suffix(self):
        commSfx = ""
        z = datetime.datetime.now()
        #dY, dM, dD, dH, dm, ds, dms
        commSfx = "_{}.{}.{}_{}.{}.{}".format(z.year, z.month, z.day, z.hour, z.minute, z.second)
        return commSfx
    
    def item_op(self, _data):
        _op = _data[0]
        if _op == "copy":
            try:
                file_name_src = _data[1]
                file_name = _data[2]
                if os.path.isdir(file_name_src) and not os.path.islink(file_name_src):
                    # make a copy - do not merge
                    if os.path.exists(file_name):
                        file_name += self.find_suffix()
                    shutil.copytree(file_name_src, file_name)
                else:
                    if os.path.exists(file_name):
                        file_name += self.find_suffix()
                    shutil.copy2(file_name_src, file_name)
            except Exception as E:
                itemWindow(self, "Error", str(E))
        elif _op == "cut":
            try:
                file_name_src = _data[1]
                file_name = _data[2]
                if os.path.isdir(file_name_src) and not os.path.islink(file_name_src):
                    # make a copy - do not merge
                    if os.path.exists(file_name):
                        file_name += self.find_suffix()
                    shutil.move(file_name_src, file_name)
                else:
                    if os.path.exists(file_name):
                        file_name += self.find_suffix()
                    shutil.move(file_name_src, file_name)
            except Exception as E:
                itemWindow(self, "Error", str(E))
    
    def on_key_pressed(self, event, keyval, keycode, state):
        if keyval == Gdk.KEY_Control_L or keyval == Gdk.KEY_Control_R:
            self.ctrl_pressed = 1
        elif keyval == Gdk.KEY_Shift_L or keyval == Gdk.KEY_Shift_R:
            self.shift_pressed = 1
        elif keyval == Gdk.KEY_Escape:
            self.escape_pressed = 1
            
    def on_key_released(self, event, keyval, keycode, state):
        self.ctrl_pressed = 0
        self.shift_pressed = 0
        self.escape_pressed = 0
    
    # convert position into pixel coordinates
    def convert_pos_to_px(self, r,c):
        y = r * self.widget_size_h+TOP_MARGIN
        x = c * self.widget_size_w+LEFT_MARGIN
        return (x,y)
        
    # convert pixel coordinates into position
    def convert_px_to_pos(self, x,y):
        c = int((x-LEFT_MARGIN)/self.widget_size_w)
        r = int((y-TOP_MARGIN)/self.widget_size_h)
        return (r,c)
        
    def find_item_new_pos(self):
        if ITEM_PLACEMENT == 1:
            # left to right
            for r in range(self.num_rows):
                for c in range(self.num_columns):
                    if (r,c) not in self.WIDGET_LIST_POS:
                        return (r,c)
        elif ITEM_PLACEMENT == 0:
            # top to bottom
            for c in range(self.num_columns):
                for r in range(self.num_rows):
                    if (r,c) not in self.WIDGET_LIST_POS:
                        return (r,c)
        #
        return (-1,-1)
        
    def fixed_op(self, _data):
        _type = _data[0]
        if _type == "put":
            custom, custom.x, custom.y = _data[1:]
            self._fixed.put(custom, custom.x, custom.y)
        elif _type == "move":
            item = _data[1]
            # add the new position
            self.WIDGET_LIST_POS.append((item.r, item.c))
            self.WIDGET_LIST_PATH_POS.append((item._itext, item.r, item.c))
            #
            self._fixed.move(item, item.x, item.y)
        elif _type == "remove":
            item = _data[1]
            self._fixed.remove(item)
            self.WIDGET_LIST.remove(item)
        
    def populate_items(self, _x, _y, _r, _c, _name, _type):
        custom = self.on_populate_items(_x, _y, _r, _c, _name, _type)
        # self._fixed.put(custom, custom.x, custom.y)
        GLib.idle_add(self.fixed_op, ("put", custom, custom.x, custom.y))
        self.WIDGET_LIST.append(custom)
        self.WIDGET_LIST_POS.append((custom.r,custom.c))
        self.WIDGET_LIST_PATH_POS.append((_name,custom.r,custom.c))
        
    def on_populate_items(self, _x, _y, _r, _c, _name, _type, _icon=None):
        if _type == "file":
            custom = customItem(self, self.widget_size_w,self.widget_size_h, self.w_icon_size, self._fm, self._font_size, _name)
        elif _type == "R":
            custom = trashItem(self, self.widget_size_w,self.widget_size_h,self.w_icon_size,self._fm,self._font_size,_name,"R")
        elif _type == "D":
            custom = deviceItem(self, self.widget_size_w,self.widget_size_h,self.w_icon_size,self._fm,self._font_size,_name,"D",_icon)
        custom.x = _x
        custom.y = _y
        custom.r = _r
        custom.c = _c
        custom.__type = _type
        return custom
    
    def on_trash_changed(self, monitor, _file1, _file2, event):
        _l = os.listdir(TRASH_PATH)
        if len(_l) > 0:
            if self.trash_item._img == "e":
                self.trash_item._img = "f"
                self.trash_item.queue_draw()
        else:
            if self.trash_item._img == "f":
                self.trash_item._img = "e"
                self.trash_item.queue_draw()
    
    def on_directory_changed(self, monitor, _file1, _file2, event):
        if event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            if USE_THUMBS == 0:
                return
            item = os.path.basename(_file1.get_path())
            for el in self.WIDGET_LIST[:]:
                if el._itext == item:
                    if el._ci == 1:
                        el.queue_draw()
                        break
        elif event == Gio.FileMonitorEvent.DELETED or event == Gio.FileMonitorEvent.MOVED_OUT: # done
            item = os.path.basename(_file1.get_path())
            for el in self.WIDGET_LIST[:]:
                if el._itext == item:
                    GLib.idle_add(self.fixed_op, ("remove", el))
                    break
            #
            _r = -1
            _c = -1
            for ell in self.WIDGET_LIST_PATH_POS[:]:
                if ell[0] == item:
                    _r = ell[1]
                    _c = ell[2]
                    self.WIDGET_LIST_PATH_POS.remove(ell)
                    break
            for ell in self.WIDGET_LIST_POS[:]:
                if (_r,_c) in self.WIDGET_LIST_POS:
                    self.WIDGET_LIST_POS.remove((_r,_c))
                    break
            for ell in self.WIDGET_TO_FUTURE_PLACE[:]:
                if ell == item:
                    self.WIDGET_TO_FUTURE_PLACE.remove(ell)
                    break
        
        elif event == Gio.FileMonitorEvent.CREATED or event == Gio.FileMonitorEvent.MOVED_IN: # done
            item = os.path.basename(_file1.get_path())
            _tr, _tc = self.find_item_new_pos()
            if _tr == -1 and _tc == -1:
                custom = self.on_populate_items(-1, -1, -1, -1, item, "file")
                self.WIDGET_TO_FUTURE_PLACE.append(custom)
            else:
                _tx, _ty = self.convert_pos_to_px(_tr,_tc)
                self.populate_items(_tx,_ty, _tr, _tc, item, "file")
            
        elif event == Gio.FileMonitorEvent.RENAMED: # done
            # old name - new name
            for el in self.WIDGET_LIST:
                if el._itext == os.path.basename(_file1.get_path()):
                    el._itext = os.path.basename(_file2.get_path())
                    el.queue_draw()
                    #
                    for ell in self.WIDGET_LIST_PATH_POS[:]:
                        if ell[0] == os.path.basename(_file1.get_path()):
                            self.WIDGET_LIST_PATH_POS.remove(ell)
                            self.WIDGET_LIST_PATH_POS.append((_file2.get_path(),ell[1],ell[2]))
                            break
                        break
    
    # _type: 1 one item - 2 multi selection
    def context_menu(self, _item, _x, _y, _type):
        if _type == 1:
            popover = Gtk.Popover()
            popover.set_has_arrow(False)
            popover.set_halign(Gtk.Align.START)
            popover.set_parent(self._fixed)
            popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            button_open = Gtk.Button(label="Open")
            self.align_label(button_open)
            button_open.connect("clicked", self.on_button_clicked, "open", popover)
            popover_box.append(button_open)
            # style_context_open = button_open.get_style_context()
            # style_context_open.add_class("ctxbtnbg")
            
            _exp1 = Gtk.Expander.new(label="Open with...")
            _exp1.set_resize_toplevel(True)
            popover_box.append(_exp1)
            box_exp1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            _exp1.set_child(box_exp1)
            #
            button2 = Gtk.Button(label="Click Me 2")
            self.align_label(button2)
            button2.connect("clicked", self.on_button_clicked, "non so 2", _item, popover)
            box_exp1.append(button2)
            # style_context_btn2 = button2.get_style_context()
            # style_context_btn2.add_class("ctxbtnbg")
            
            button_copy = Gtk.Button(label="Copy")
            self.align_label(button_copy)
            button_copy.connect("clicked", self.on_button_clicked, "copy", _item, popover)
            popover_box.append(button_copy)
            # style_context_copy = button_copy.get_style_context()
            # style_context_copy.add_class("ctxbtnbg")
            
            button_cut = Gtk.Button(label="Cut")
            self.align_label(button_cut)
            button_cut.connect("clicked", self.on_button_clicked, "cut", _item, popover)
            popover_box.append(button_cut)
            # style_context_cut = button_cut.get_style_context()
            # style_context_cut.add_class("ctxbtnbg")
            
            button_trash = Gtk.Button(label="Trash")
            self.align_label(button_trash)
            button_trash.connect("clicked", self.on_button_clicked, "trash", _item, popover)
            popover_box.append(button_trash)
            # style_context_trash = button_trash.get_style_context()
            # style_context_trash.add_class("ctxbtnbg")
            
            button_delete = Gtk.Button(label="Delete")
            self.align_label(button_delete)
            button_delete.connect("clicked", self.on_button_clicked, "delete", _item, popover)
            popover_box.append(button_delete)
            # style_context_delete = button_delete.get_style_context()
            # style_context_delete.add_class("ctxbtnbg")
            
            button_rename = Gtk.Button(label="Rename")
            self.align_label(button_rename)
            button_rename.connect("clicked", self.on_button_clicked, "rename", _item, popover)
            popover_box.append(button_rename)
            # style_context_rename = button_rename.get_style_context()
            # style_context_rename.add_class("ctxbtnbg")
            
            button_property = Gtk.Button(label="Property")
            self.align_label(button_property)
            button_property.connect("clicked", self.on_button_clicked, "property", _item, popover)
            popover_box.append(button_property)
            # style_context_property = button_property.get_style_context()
            # style_context_property.add_class("ctxbtnbg")
            
            # css_provider = Gtk.CssProvider()
            # Gtk.StyleContext.add_provider_for_display(
                # Gdk.Display.get_default(),
                # css_provider,
                # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            # # css = ".ctxbtnbg {background:white; color: blue; border: 0px; frame: 0px;}"
            # css = ".ctxbtnbg {border: 0px;}"
            # css_provider.load_from_data(css.encode('utf-8'))
            #
            popover.set_child(popover_box)
            #
            _rect = Gdk.Rectangle()
            _rect.x = _item.x + _x + 1
            _rect.y = _item.y + _y + 1
            _rect.width = 1
            _rect.height = 1
            popover.set_pointing_to(_rect)
            popover.popup()
        elif _type == 2:
            _iteml = self.selection_widget_found
            #
            popover = Gtk.Popover()
            popover.set_has_arrow(False)
            popover.set_halign(Gtk.Align.START)
            popover.set_parent(self._fixed)
            popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            button_copy = Gtk.Button(label="Copy")
            self.align_label(button_copy)
            button_copy.connect("clicked", self.on_button_clicked, "copy", _iteml, popover)
            popover_box.append(button_copy)
            # style_context_copy = button_copy.get_style_context()
            # style_context_copy.add_class("ctxbtnbg")
            
            button_cut = Gtk.Button(label="Cut")
            self.align_label(button_cut)
            button_cut.connect("clicked", self.on_button_clicked, "cut", _iteml, popover)
            popover_box.append(button_cut)
            # style_context_cut = button_cut.get_style_context()
            # style_context_cut.add_class("ctxbtnbg")
            
            button_trash = Gtk.Button(label="Trash")
            self.align_label(button_trash)
            button_trash.connect("clicked", self.on_button_clicked, "trash", _iteml, popover)
            popover_box.append(button_trash)
            # style_context_trash = button_trash.get_style_context()
            # style_context_trash.add_class("ctxbtnbg")
            
            button_delete = Gtk.Button(label="Delete")
            self.align_label(button_delete)
            button_delete.connect("clicked", self.on_button_clicked, "delete", _iteml, popover)
            popover_box.append(button_delete)
            # style_context_delete = button_delete.get_style_context()
            # style_context_delete.add_class("ctxbtnbg")
            
            button_property = Gtk.Button(label="Property")
            self.align_label(button_property)
            button_property.connect("clicked", self.on_button_clicked, "property", _iteml, popover)
            popover_box.append(button_property)
            # style_context_property = button_property.get_style_context()
            # style_context_property.add_class("ctxbtnbg")
            
            # css_provider = Gtk.CssProvider()
            # Gtk.StyleContext.add_provider_for_display(
                # Gdk.Display.get_default(),
                # css_provider,
                # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            # css = ".ctxbtnbg {border: 0px;}"
            # css_provider.load_from_data(css.encode('utf-8'))
            #
            popover.set_child(popover_box)
            #
            _rect = Gdk.Rectangle()
            _rect.x = _item.x + _x + 1
            _rect.y = _item.y + _y + 1
            _rect.width = 1
            _rect.height = 1
            popover.set_pointing_to(_rect)
            popover.popup()
            
    def context_menu_device(self,_device,x,y):
        popover = Gtk.Popover()
        popover.set_has_arrow(False)
        popover.set_halign(Gtk.Align.START)
        popover.set_parent(self)
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        #
        button_open = Gtk.Button(label="Open")
        self.align_label(button_open)
        button_open.connect("clicked", self.open_device, popover)
        popover_box.append(button_open)
        #
        ddev = _device.block_device
        # "N" or mount point
        is_mounted = self.on_get_mounted(ddev)
        if is_mounted == "N":
            _mount_lbl = "Mount"
        else:
            _mount_lbl = "Umount"
        btn_mount = Gtk.Button(label=_mount_lbl)
        self.align_label(btn_mount)
        btn_mount.connect("clicked", self.on_dev_mount, _device.device, is_mounted, popover)
        popover_box.append(btn_mount)
        #
        drive = _device.drive
        _can_eject = self.get_device_can_eject(drive)
        if _can_eject:
            btn_eject = Gtk.Button(label="Eject")
            self.align_label(btn_eject)
            btn_eject.connect("clicked", self.on_dev_eject, _device, popover)
            popover_box.append(btn_eject)
        #
        btn_prop = Gtk.Button(label="Property")
        self.align_label(btn_prop)
        btn_prop.connect("clicked", self.on_device_properties, _device, popover)
        popover_box.append(btn_prop)
        #
        # style_context_open = button_open.get_style_context()
        # style_context_open.add_class("ctxbtnbg")
        # css_provider = Gtk.CssProvider()
        # Gtk.StyleContext.add_provider_for_display(
            # Gdk.Display.get_default(),
            # css_provider,
            # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # css = ".ctxbtnbg {border: 0px;}"
        # css_provider.load_from_data(css.encode('utf-8'))
        #
        popover.set_child(popover_box)
        #
        _rect = Gdk.Rectangle()
        _rect.x = _device.x + x + 1
        _rect.y = _device.y + y + 1
        _rect.width = 1
        _rect.height = 1
        popover.set_pointing_to(_rect)
        popover.popup()
        
    # open the setted application for the bin
    def open_device(self, btn, popover):
        popover.popdown()
        try:
            Popen(DEVICE_APP.split(" "))
        except Exception as E:
            itemWindow(self, "Error", str(E))
    
    def on_dev_mount(self, btn, device, mountpoint, popover):
        popover.popdown()
        self.mount_device(mountpoint, device)
    
    def on_dev_eject(self, btn, _device, popover):
        popover.popdown()
        ddev = _device.block_device
        is_mounted = self.on_get_mounted(ddev)
        ddevice = _device.device
        ddrive = _device.drive
        self.eject_media(ddrive, is_mounted, ddevice, None)
        
    def on_device_properties(self, btn, _device, popover):
        popover.popdown()
        k = _device.block_device
        mountpoint = self.on_get_mounted(_device.block_device)
        ddrive = _device.drive
        ddevice = _device.device
        self.media_property(k, mountpoint, ddrive, ddevice)
        
    def context_menu_trash(self,x,y):
        popover = Gtk.Popover()
        popover.set_has_arrow(False)
        popover.set_halign(Gtk.Align.START)
        popover.set_parent(self)
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        button_open = Gtk.Button(label="Open")
        self.align_label(button_open)
        button_open.connect("clicked", self.open_trash, popover)
        popover_box.append(button_open)
        button_empty = Gtk.Button(label="Empty the Recycle Bin")
        self.align_label(button_empty)
        button_empty.connect("clicked", self.on_button_R_clicked, popover)
        popover_box.append(button_empty)
        if len(os.listdir(TRASH_PATH)) == 0:
            button_empty.set_sensitive(False)
        # style_context_open = button_open.get_style_context()
        # style_context_open.add_class("ctxbtnbg")
        # css_provider = Gtk.CssProvider()
        # Gtk.StyleContext.add_provider_for_display(
            # Gdk.Display.get_default(),
            # css_provider,
            # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # css = ".ctxbtnbg {border: 0px;}"
        # css_provider.load_from_data(css.encode('utf-8'))
        #
        popover.set_child(popover_box)
        #
        _rect = Gdk.Rectangle()
        _rect.x = self.trash_item.x + x + 1
        _rect.y = self.trash_item.y + y + 1
        _rect.width = 1
        _rect.height = 1
        popover.set_pointing_to(_rect)
        popover.popup()
    
    # open the setted application for the bin
    def open_trash(self, btn, popover):
        popover.popdown()
        try:
            Popen(TRASH_APP.split(" "))
        except Exception as E:
            itemWindow(self, "Error", str(E))
    
    def on_button_R_clicked(self, btn, popover):
        popover.popdown()
        try:
            GLib.idle_add(self.item_op_R, ("empty",))
        except exception as E:
            itemWindow(self, "Error", str(E))
    
    # empty the trashcan
    def item_op_R(self, _data):
        _op = _data[0]
        if _op == "empty":
            try:
                folder = TRASH_PATH
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                folder = TRASH_INFO
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
            except Exception as E:
                itemWindow(self, "Error", str(E))
            self.trash_item.queue_draw()
    
    # send items to trash
    def on_trash(self, _wdg, _item, _popover):
        if isinstance(_item, list):
            for el in _item:
                file_name = el._itext
                _f = Gio.File.new_for_path(os.path.join(DESKTOP_PATH,file_name))
                _f.trash()
            _popover.popdown()
        else:
            file_name = _item._itext
            _f = Gio.File.new_for_path(os.path.join(DESKTOP_PATH,file_name))
            _f.trash()
            _popover.popdown()
    
    def align_label(self, btn):
        _ch = btn.get_child()
        if isinstance(_ch, Gtk.Label):
            _ch.set_halign(Gtk.Align.START)
    
    def on_delete(self, _wdg, _item, _popover):
        _errors = ""
        if isinstance(_item, list):
            for el in _item:
                file_name = el._itext
                _f = os.path.join(DESKTOP_PATH,file_name)
                try:
                    if os.path.isdir(_f) and not os.path.islink(_f):
                        shutil.rmtree(_f)
                    else:
                        os.remove(_f)
                except Exception as E:
                    _errors += str(E)+"\n"
            _popover.popdown()
        else:
            file_name = _item._itext
            _f = os.path.join(DESKTOP_PATH,file_name)
            try:
                if os.path.isdir(_f) and not os.path.islink(_f):
                    shutil.rmtree(_f)
                else:
                    os.remove(_f)
            except Exception as E:
                _errors += str(E)+"\n"
            _popover.popdown()
        if _errors != "":
            itemWindow(self, "Error", _errors)
    
    def get_data_paste(self, obj, res, _d):
        _data = self.clipboard.read_finish(res)
        _atom = "x-special/gnome-copied-files"
        gio_input_stream = _data[0]
        outputStream = Gio.MemoryOutputStream.new_resizable()
        outputStream.splice_async(gio_input_stream,Gio.OutputStreamSpliceFlags.CLOSE_TARGET,GLib.PRIORITY_DEFAULT,None,self.on_get_data_paste, None)
    
    def on_get_data_paste(self, obj, res, _d):
        _data = obj.splice_finish(res)
        _dbytes = obj.steal_as_bytes()
        _list = _dbytes.get_data().decode("utf-8").split("\n")
        _errors = ""
        _operation = _list[0]
        for _f in _list[1:]:
            if _f == "":
                continue
            _file = Gio.File.new_for_uri(_f).get_path()
            if not os.path.exists(_file):
                continue
            try:
                _f_n = os.path.basename(_file)
                if _operation == "copy":
                    GLib.idle_add(self.item_op, ("copy", _file, os.path.join(DESKTOP_PATH,_f_n)))
                elif _operation == "cut":
                    GLib.idle_add(self.item_op, ("cut", _file, os.path.join(DESKTOP_PATH,_f_n)))
            except Exception as E:
                _errors += str(E)+"\n"
        if _errors != "":
            itemWindow(self, "Error", _errors)
    
    def on_button_clicked(self, _w, _type, _item, popover):
        if _type == "copy" or _type == "cut": # ok
            popover.popdown()
            if isinstance(_item,list):
                _data = "{}\n".format(_type)
                for el in _item:
                    file_name = el._itext
                    _f = os.path.join(DESKTOP_PATH, file_name)
                    _f_uri = Gio.File.new_for_path(_f).get_uri()
                    _data += _f_uri+"\n"
                _data += "\0"
            else:
                file_name = _item._itext
                _f = os.path.join(DESKTOP_PATH, file_name)
                _f_uri = Gio.File.new_for_path(_f).get_uri()
                _data = "{}\n{}\n\0".format(_type, _f_uri)
            
            gbytes = GLib.Bytes.new(bytes(_data, 'utf-8'))
            _atom = "x-special/gnome-copied-files"
            content = Gdk.ContentProvider.new_for_bytes(_atom, gbytes)
            self.clipboard.set_content(content)
        
        elif _type == "paste": # ok
            popover.popdown()
            _atom = "x-special/gnome-copied-files"
            self.clipboard.read_async([_atom],1,None,self.get_data_paste,None)
        
        elif _type == "trash": # ok
            popover.popdown()
            
            ren_pop = Gtk.Popover.new()
            ren_pop = Gtk.Popover()
            ren_pop.set_has_arrow(False)
            ren_pop.set_halign(Gtk.Align.START)
            ren_pop.set_parent(self._fixed)
            popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            #
            button = Gtk.Button(label="Send to trashcan?")
            button.connect("clicked", self.on_trash, _item, ren_pop)
            popover_box.append(button)
            # style_context_paste = button.get_style_context()
            # style_context_paste.add_class("ctxbtnbg")
            #
            button_close = Gtk.Button(label="Close")
            button_close.connect("clicked", lambda w:ren_pop.popdown())
            popover_box.append(button_close)
            # style_context_paste = button_close.get_style_context()
            # style_context_paste.add_class("ctxbtnbg")
            #
            # css_provider = Gtk.CssProvider()
            # Gtk.StyleContext.add_provider_for_display(
                # Gdk.Display.get_default(),
                # css_provider,
                # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            # css = ".ctxbtnbg {border: 0px;}"
            # css_provider.load_from_data(css.encode('utf-8'))
            #
            ren_pop.set_child(popover_box)
            #
            if isinstance(_item, list):
                _r = _item[-1].r
                _c = _item[-1].c
                _x = _item[-1].x
                _y = _item[-1].y+self.w_icon_size+10
            else:
                _r = _item.r
                _c = _item.c
                _x = _item.x
                _y = _item.y+self.w_icon_size+10
            _rect = Gdk.Rectangle()
            _rect.x = _x
            _rect.y = _y
            _rect.width = 1
            _rect.height = 1
            ren_pop.set_pointing_to(_rect)
            ren_pop.popup()
        
        elif _type == "delete": # ok
            popover.popdown()
            #
            ren_pop = Gtk.Popover.new()
            ren_pop = Gtk.Popover()
            ren_pop.set_has_arrow(False)
            ren_pop.set_halign(Gtk.Align.START)
            ren_pop.set_parent(self._fixed)
            popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            #
            button = Gtk.Button(label="Delete permanently?")
            button.connect("clicked", self.on_delete, _item, ren_pop)
            popover_box.append(button)
            # style_context_paste = button.get_style_context()
            # style_context_paste.add_class("ctxbtnbg")
            #
            button_close = Gtk.Button(label="Close")
            button_close.connect("clicked", lambda w:ren_pop.popdown())
            popover_box.append(button_close)
            # style_context_paste = button_close.get_style_context()
            # style_context_paste.add_class("ctxbtnbg")
            #
            # css_provider = Gtk.CssProvider()
            # Gtk.StyleContext.add_provider_for_display(
                # Gdk.Display.get_default(),
                # css_provider,
                # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            # css = ".ctxbtnbg {border: 0px;}"
            # css_provider.load_from_data(css.encode('utf-8'))
            #
            ren_pop.set_child(popover_box)
            #
            if isinstance(_item,list):
                _r = _item[-1].r
                _c = _item[-1].c
                _x = _item[-1].x
                _y = _item[-1].y+self.w_icon_size+10
            else:
                _r = _item.r
                _c = _item.c
                _x = _item.x
                _y = _item.y+self.w_icon_size+10
            _rect = Gdk.Rectangle()
            _rect.x = _x
            _rect.y = _y
            _rect.width = 1
            _rect.height = 1
            ren_pop.set_pointing_to(_rect)
            ren_pop.popup()
        
        elif _type == "rename": # OK
            if not isinstance(_item, list):
                popover.popdown()
                _item = self.selection_widget_found[0]
                file_name = _item._itext
                _f = os.path.join(DESKTOP_PATH,file_name)
                #
                ren_pop = Gtk.Popover.new()
                ren_pop = Gtk.Popover()
                ren_pop.set_has_arrow(False)
                ren_pop.set_halign(Gtk.Align.START)
                ren_pop.set_parent(self._fixed)
                popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                #
                _entry = Gtk.Entry.new()
                _entry.get_buffer().set_text(_item._itext, -1)
                popover_box.append(_entry)
                #
                button = Gtk.Button(label="Rename")
                button.connect("clicked", self.on_button_rename_clicked, _entry, ren_pop, _item)
                popover_box.append(button)
                # style_context_paste = button.get_style_context()
                # style_context_paste.add_class("ctxbtnbg")
                #
                button_close = Gtk.Button(label="Close")
                button_close.connect("clicked", lambda w:ren_pop.popdown())
                popover_box.append(button_close)
                # style_context_paste = button_close.get_style_context()
                # style_context_paste.add_class("ctxbtnbg")
                #
                # css_provider = Gtk.CssProvider()
                # Gtk.StyleContext.add_provider_for_display(
                    # Gdk.Display.get_default(),
                    # css_provider,
                    # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                # css = ".ctxbtnbg {border: 0px;}"
                # css_provider.load_from_data(css.encode('utf-8'))
                #
                ren_pop.set_child(popover_box)
                #
                _r = _item.r
                _c = _item.c
                _x = _item.x
                _y = _item.y+self.w_icon_size+10
                _rect = Gdk.Rectangle()
                _rect.x = _x
                _rect.y = _y
                _rect.width = 1
                _rect.height = 1
                ren_pop.set_pointing_to(_rect)
                ren_pop.popup()
        
        elif _type == "replace":
            popover.popdown()
            for el in self.WIDGET_TO_FUTURE_PLACE[:]:
                _tr, _tc = self.find_item_new_pos()
                if _tr == -1 and _tc == -1:
                    break
                    return
                #
                _tx, _ty = self.convert_pos_to_px(_tr,_tc)
                self.populate_items(_tx,_ty, _tr, _tc, el, "file")
                self.WIDGET_TO_FUTURE_PLACE.remove(el)
    
    def on_button_rename_clicked(self, w, entry, popover, _item):
        old_text = _item._itext
        _text = entry.get_buffer().get_text()
        _f = os.path.join(DESKTOP_PATH,_text)
        if not os.path.exists(_f):
            shutil.move(os.path.join(DESKTOP_PATH,_item._itext),_f)
            _item._itext = _text
            if (old_text, _item.r, _item.c) in self.WIDGET_LIST_PATH_POS[:]:
                self.WIDGET_LIST_PATH_POS.remove((old_text, _item.r, _item.c))
                self.WIDGET_LIST_PATH_POS.append((_text, _item.r, _item.c))
            popover.popdown()
    
    def background_context_menu(self, _item, _x, _y):
        popover = Gtk.Popover()
        popover.set_autohide(True)
        popover.set_has_arrow(False)
        popover.set_halign(Gtk.Align.START)
        popover.set_parent(_item)
        
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        button = Gtk.Button(label="Click Me")
        self.align_label(button)
        # style_context_property = button.get_style_context()
        # style_context_property.add_class("ctxbtnbg")
        button.connect("clicked", self.on_button_clicked, "booo", _item, popover)
        popover_box.append(button)
        
        _exp1 = Gtk.Expander.new(label="EXPANDER")
        _exp1.set_resize_toplevel(True)
        popover_box.append(_exp1)
        box_exp1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        _exp1.set_child(box_exp1)
        
        button_paste = Gtk.Button(label="Paste")
        self.align_label(button_paste)
        button_paste.connect("clicked", self.on_button_clicked, "paste", [], popover)
        popover_box.append(button_paste)
        # style_context_paste = button_paste.get_style_context()
        # style_context_paste.add_class("ctxbtnbg")
        
        if len(self.WIDGET_TO_FUTURE_PLACE) > 0:
            btn_replace = Gtk.Button(label="Replace")
            self.align_label(btn_replace)
            btn_replace.connect("clicked", self.on_button_clicked, "replace", [], popover)
            popover_box.append(btn_replace)
            # style_context_paste = btn_replace.get_style_context()
            # style_context_paste.add_class("ctxbtnbg")
        
        button2 = Gtk.Button(label="Click Me 2")
        self.align_label(button2)
        # style_context_property = button2.get_style_context()
        # style_context_property.add_class("ctxbtnbg")
        button2.connect("clicked", self.on_button_clicked, "cioa", _item, popover)
        box_exp1.append(button2)
        
        popover.set_child(popover_box)
        ######
        # css_provider = Gtk.CssProvider()
        # Gtk.StyleContext.add_provider_for_display(
            # Gdk.Display.get_default(),
            # css_provider,
            # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # css = ".ctxbtnbg {border: 0px;}"
        # css_provider.load_from_data(css.encode('utf-8'))
        #
        _rect = Gdk.Rectangle()
        _rect.x = _x + 1
        _rect.y = _y + 1
        _rect.width = 1
        _rect.height = 1
        popover.set_pointing_to(_rect)
        popover.popup()
        
    def on_draw(self, da, cr, w, h, data):
        pass
    
    def on_draw2(self, da, cr, w, h, data):
        if self.left_click_setted == 1:
            w = self.end_x
            h = self.end_y
            # the border
            _color = Gdk.RGBA()
            if _color.parse(R_BORDER_COLOR):
                cr.set_source_rgba(_color.red, _color.green, _color.blue, _color.alpha)
            else:
                cr.set_source_rgba(0.7, 0.7, 0.7, 0.5)
            cr.set_line_width(R_LINE_WIDTH)
            cr.rectangle(self.start_x,self.start_y,w,h)
            cr.stroke()
            # the inside
            _color = Gdk.RGBA()
            if _color.parse(R_COLOR):
                cr.set_source_rgba(_color.red, _color.green, _color.blue, _color.alpha)
            else:
                cr.set_source_rgba(0.25, 0.7, 1.0, 0.2)
            cr.rectangle(self.start_x,self.start_y,w,h)
            cr.fill()
    
    # mouse pressed (1) and released (0)
    def on_da_gesture_l(self, o,n,x,y, _t):
        if _t == 1:
            if self.selection_widget_found != []:
                for _wdg in self.selection_widget_found[:]:
                    _wdg._state = 0
                    _wdg._v = 0
                    _wdg.queue_draw()
                self.selection_widget_found = []
        
        if self.left_click_setted == 0:
            self.left_click_setted = 1
        else:
            self.left_click_setted = 0
        
    # def on_da_gesture_c(self, o,n,x,y):
        # pass
    
    def on_da_gesture_r(self, o,n,x,y):
        self.background_context_menu(self._fixed, x, y)
    
    # def on_right_pressed(self, o,n,x,y,da):
        # pass
    
    # drag begin
    def on_da_gesture_d_b(self, gesture_drag, start_x, start_y, da):
        self.start_x = start_x
        self.start_y = start_y
        self.isDragging = 1
        self.rubberband = myRubberBand(self)
        self._fixed.put(self.rubberband, self.start_x, self.start_y)
        
    # drag update
    def on_da_gesture_d_u(self, gesture_drag, offset_x, offset_y, da):
        if abs(offset_x) > 4:
            # the rubberband
            self.end_x = offset_x
            self.end_y = offset_y
            # da.queue_draw()
            self.rubberband.queue_draw()
            
            if offset_x >= 0:
                _x1 = self.start_x
                _x2 = self.start_x+offset_x
            else:
                _x1 = self.start_x+offset_x-self.widget_size_w
                _x2 = self.start_x
            
            if offset_y >= 0:
                _y1 = self.start_y
                _y2 = self.start_y+offset_y
            else:
                _y1 = self.start_y+offset_y-self.widget_size_h
                _y2 = self.start_y
            
            # select or deselect the items
            for _wdg in self.WIDGET_LIST:
                # skip the trashcan
                if _wdg == self.trash_item:
                    continue
                # skip removables
                if _wdg in self.list_devices:
                    continue
                #
                if _x1 < _wdg.x < _x2 and _y1 < _wdg.y < _y2:
                    if not _wdg in self.selection_widget_found:
                        self.selection_widget_found.append(_wdg)
                        if _wdg._state == 0:
                            _wdg._state = 1
                            _wdg._v = 2
                            _wdg.queue_draw()
                else:
                    if _wdg in self.selection_widget_found:
                        self.selection_widget_found.remove(_wdg)
                        if _wdg._state == 1:
                            _wdg._state = 0
                            _wdg._v = 0
                            _wdg.queue_draw()
        
    # drag end - drawing area
    def on_da_gesture_d_e(self, gesture_drag, offset_x, offset_y, da):
        # reset
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        # da.queue_draw()
        self._fixed.remove(self.rubberband)
        del self.rubberband
        self.rubberband = None
        #
        self.isDragging = 0
        
    def write_item_pos_conf(self):
        try:
            _f = open(os.path.join(_curr_dir,"item_positions.cfg"), "w")
            for el in self.WIDGET_LIST_PATH_POS:
                _f.write(el[0]+"/"+str(el[1])+"/"+str(el[2])+"\n")
            _f.close()
        except:
            pass
        
    def _to_close(self, w=None, e=None):
        # self.write_item_pos_conf()
        self.close()
    
    def sigtype_handler(self, sig, frame):
        if sig == signal.SIGINT or sig == signal.SIGTERM:
            self._to_close()


class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

app = MyApp(application_id="com.example.GtkApplication")
app.run(sys.argv)

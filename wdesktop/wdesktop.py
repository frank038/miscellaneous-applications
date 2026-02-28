#!/usr/bin/env python3

import sys, os, shutil, signal
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, Graphene, Gsk, Gio, Pango, GObject
from gi.repository import GLib
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk4LayerShell as GtkLayerShell


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

# BORDER MARGINS
TOP_MARGIN = 0
BOTTOM_MARGIN = 0
LEFT_MARGIN = 0
RIGHT_MARGIN = 0

# space between items
ITEM_MARGIN = 8

#### SETTINGS
# widget width and height and space between items
widget_size_w = 96+ITEM_MARGIN
widget_size_h = 96+ITEM_MARGIN
# icon size - square
w_icon_size = 48
# font family
_fm = "Sans"
# item font size - 0 to disable
_font_size = 0
# corner radius of the text
ROUNDED_CORNER = 3
# number of lines of each item text
NUMBER_OF_TEXT_LINES = 2
# normal text background colour
TEXT_BACKGROUND_NORMAL = "#aaaaaaaa"
# highlight text background colour
TEXT_BACKGROUND_HIGHLIGHT = "#aa0000aa"
# the desktop folder
DESKTOP_PATH = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)
DESKTOP_FILES = os.listdir(DESKTOP_PATH)
for el in DESKTOP_FILES[:]:
    if el[0] == ".":
        DESKTOP_FILES.remove(el)

class customItem(Gtk.Widget):
    def __init__(self, _parent, _w, _h, _iw, _fm, _fs, _itext):
        super().__init__()
        self._parent = _parent
        self._w = _w
        self._h = _h
        self._iw = _iw
        self._fm = _fm
        self._fs = _fs
        self._itext = _itext
        
        ####################
        
        self._file = Gio.File.new_for_path(os.path.join(DESKTOP_PATH, self._itext))
        self._file_info = self._file.query_info("standard::*,owner::user", Gio.FileQueryInfoFlags.NONE,None)
        
        # 0 inactive - 1 active mouse over - 2 active mouse selected
        self._v = 0
        self._snapshot = None
        
        self.set_size_request(self._w, self._h)
        
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
        
        ## dragging
        gesture_d = Gtk.GestureDrag.new()
        gesture_d.set_button(1)
        self.add_controller(gesture_d)
        gesture_d.connect('drag-begin', self.on_gesture_d_b)
        gesture_d.connect('drag-update', self.on_gesture_d_u)
        gesture_d.connect('drag-end', self.on_gesture_d_e)
        #
        # initial values
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        
        
    def on_change_cursor(self, _t):
        if _t == 1:
            cursor_window = Gdk.Cursor.new_from_name("grabbing")
            self.set_cursor(cursor_window)
        elif _t == 0:
            cursor_window = Gdk.Cursor.new_from_name("default")
            self.set_cursor(cursor_window)
    
    def on_gesture_d_b(self, gesture_drag, start_x, start_y):
        # dragging begins
        self_position = self._parent._fixed.get_child_position(self)
        self.start_x = self_position.x
        self.start_y = self_position.y
    
    def on_gesture_d_u(self, gesture_drag, offset_x, offset_y):
        if len(self._parent.selection_widget_found) > 1:
            return
        if abs(offset_x) > 4 and abs(offset_y) > 4:
            if self.left_mouse_pressed == 1:
                self.on_change_cursor(1)
                self.left_mouse_pressed = 2
        
    def on_gesture_d_e(self, gesture_drag, offset_x, offset_y):
        # dragging end
        if len(self._parent.selection_widget_found) > 1:
            return
        
        _x = self.start_x + offset_x
        _y = self.start_y + offset_y
        
        c_c = int(_x/self._w)
        c_r = int(_y/self._h)
        
        if 0 <= c_r <= self._parent.num_rows and 0 <= c_c <= self._parent.num_columns:
            _x = c_c*self._w+LEFT_MARGIN
            _y = c_r*self._h+TOP_MARGIN
            self._parent._fixed.move(self, _x, _y)
            
            if (self._itext,self.r,self.c) in self._parent.WIDGET_LIST_PATH_POS[:]:
                self._parent.WIDGET_LIST_PATH_POS.remove((self._itext,self.r,self.c))
            self._parent.WIDGET_LIST_PATH_POS.append((self._itext,c_r,c_c))
            
            self.x = _x
            self.y = _y
            self.r = c_r
            self.c = c_c
        
        self.left_mouse_pressed = 0
        self.on_change_cursor(0)
        
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
    
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
        # deselect all
        if self not in self._parent.selection_widget_found:
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
        
        if len(self._parent.selection_widget_found) > 1:
            return
        
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
    
    def find_icon_thumb(self):
        return None
    
    # _obj is snapshot
    def do_snapshot(self, _obj):
        if self._snapshot == None:
            self._snapshot = _obj
        ######## ICON
        ret = self.find_icon_thumb()
        if ret == None:
            display = Gdk.Display.get_default()
            icon_theme = Gtk.IconTheme.get_for_display(display)
            icon_name = self._file_info.get_content_type()
            icon_names = Gio.content_type_get_icon(icon_name).get_names()
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
                icon_file_path = os.path.join(_curr_dir, "images", "icon.svg")
            texture = Gdk.Texture.new_from_filename(icon_file_path)
        else:
            icon_file_path = ret
            texture = Gdk.Texture.new_from_filename(icon_file_path)
        #
        size_rect = Graphene.Rect()
        gx = int((self._w-self._iw)/2)-ITEM_MARGIN
        gy = ITEM_MARGIN
        size_rect.init(gx+ITEM_MARGIN, gy, self._iw, self._iw)
        _obj.append_scaled_texture(texture, 0, size_rect)
        #
        ######### text
        colour = Gdk.RGBA()
        colour.red = 0.0
        colour.green = 0.0
        colour.blue = 0.0
        colour.alpha = 1.0
        
        font = Pango.FontDescription.new()
        font.set_family(self._fm)
        if self._fs > 6:
            font.set_size(self._fs * Pango.SCALE)
        context = self.get_pango_context()
        layout = Pango.Layout(context) 
        layout.set_font_description(font)
        #
        new_text = ""
        tmp_text = self._itext[0]
        _lines = 1
        list_text = []
        for _c in self._itext[1:]:
            tmp_text += _c
            layout.set_text(tmp_text)
            
            if layout.get_pixel_size().width > (self._w-ITEM_MARGIN*2):
                if _lines < NUMBER_OF_TEXT_LINES or (self._state > 0 or self._v > 0):
                    new_text += tmp_text[:-1]+"\n"
                    list_text.append(tmp_text[:-1])
                    tmp_text = tmp_text[-1]
                    _lines += 1
                elif _lines == NUMBER_OF_TEXT_LINES and (self._state == 0 and self._v == 0):
                    new_text += tmp_text[:-3]+"..."
                    list_text.append(tmp_text[:-3]+"...")
                    break
        
        if _lines == 1:
            list_text.append(self._itext)
            new_text = self._itext
        elif tmp_text != "" and (self._state > 0 or self._v > 0):
            new_text += tmp_text
            list_text.append(tmp_text)
        ##
        # starting height: space between icon and text
        _text_height = 10
        ######## TEXT BACKGROUND
        
        _ac = Gdk.RGBA()
        if self._v == 0:
            _ac.parse(TEXT_BACKGROUND_NORMAL)
            _ac.to_string()
        else:
            _ac.parse(TEXT_BACKGROUND_HIGHLIGHT)
            _ac.to_string()
        
        ### calculate the text size
        layout.set_text(new_text)
        _tw = layout.get_pixel_size().width
        _th = layout.get_pixel_size().height
        
        r = Graphene.Rect()
        _pad = int(((self._w-ITEM_MARGIN*2)-_tw)/2)
        r.init(ITEM_MARGIN+_pad-1, self._iw+_text_height, _tw+1, _th)
        
        ########
        _rounded_r = Gsk.RoundedRect()
        _rounded_r.init_from_rect(r, ROUNDED_CORNER)
        _rounded_r.normalize()
        _obj.push_rounded_clip(_rounded_r)
        _obj.append_color(_ac, r)
        _obj.pop()
        #
        #### item name
        for _t in list_text:
            if _t[-1] == " ":
                _t = _t[:-1]
            layout.set_text(_t)
            text_width = layout.get_pixel_size().width
            #
            point = Graphene.Point()
            point.x = int((self._w-ITEM_MARGIN*2-text_width)/2)+ITEM_MARGIN
            point.y = self._iw + _text_height
            #
            _obj.save()
            _obj.translate(point)
            _obj.append_layout(layout, colour)
            _obj.restore()
            #
            _text_height += layout.get_pixel_size().height
    
    def do_measure(self, orientation, for_size):
        return self._w, self._h, -1, -1
       
        
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
    

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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
            # self.set_size_request(self.screen_width-self.win_width,self.win_height)
            self.set_size_request(WIDTH,HEIGHT)
        #
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
        self.num_rows = int((self.screen_height-TOP_MARGIN-BOTTOM_MARGIN)/self.widget_size_h)
        self.num_columns = int((self.screen_width-LEFT_MARGIN-RIGHT_MARGIN)/self.widget_size_w)
        ret_row = self.screen_height-(self.num_rows*self.widget_size_h)
        ret_column = self.screen_width-(self.num_columns*self.widget_size_w)
        # 
        BOTTOM_MARGIN += int(ret_row/2)
        TOP_MARGIN += ret_row - BOTTOM_MARGIN
        #
        RIGHT_MARGIN += int(ret_column/2)
        LEFT_MARGIN += ret_column - RIGHT_MARGIN
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("mydesktop")
        
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # # layershell
        # GtkLayerShell.init_for_window(self)
        # GtkLayerShell.auto_exclusive_zone_enable(self)
        # # GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BACKGROUND)
        # GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        # GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        
        self.clipboard = Gdk.Display.get_default().get_clipboard()
        
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box1)
        
        ###########
        
        self._fixed = Gtk.Fixed()
        self.box1.append(self._fixed)
        
        self.da = Gtk.DrawingArea()
        self._fixed.put(self.da, 0,0)
        self.da.set_size_request(WIDTH,HEIGHT)
        
        self.da_style_context = self.da.get_style_context()
        self.da_style_context.add_class("myda")
        #
        image_path = os.path.join(_curr_dir,"wallpaper.png")
        css = ".myda {background-image:url(file://"+"{}".format(image_path)+"); background-size: cover;}"
        self.css_provider.load_from_data(css.encode('utf-8'))
        #
        self.da.set_hexpand(True)
        self.da.set_vexpand(True)
        self.da.set_draw_func(self.on_draw, None)
        
        # list of customItem
        self.WIDGET_LIST = []
        # each item x,y,row,column
        self.WIDGET_LIST_POS = []
        # each item: name row column
        self.WIDGET_LIST_PATH_POS = []
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
        # # right button - main
        # gesture_r = Gtk.GestureClick.new()
        # gesture_r.set_button(3)
        # self.add_controller(gesture_r)
        # gesture_r.connect('pressed', self.on_gesture_r, self.on_right_pressed)
        # self.right_click_setted = 0
        #
        self.da.set_focusable(False)
        self.da.set_focus_on_click(False)
        #
        ## drawing area - dragging
        self.da_gesture_d = Gtk.GestureDrag.new()
        self.da_gesture_d.set_button(1)
        self.da.add_controller(self.da_gesture_d)
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
        drop_controller = Gtk.DropTarget.new(type=GObject.TYPE_NONE, actions=Gdk.DragAction.COPY)
        drop_controller.set_gtypes([self, Gdk.FileList, str])
        drop_controller.connect("drop", self.on_drop)
        self.add_controller(drop_controller)
        
        # self._dh_value = 0
        # initial values
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        
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
                self.WIDGET_LIST_PATH_POS.append((item, int(r), int(c)))
        except:
            pass
        
        # populate the program
        for item in DESKTOP_FILES:
            for el in self.WIDGET_LIST_PATH_POS:
                if el[0] == item:
                    _tr = el[1]
                    _tc = el[2]
                    _tx, _ty = self.convert_pos_to_px(_tr,_tc)
                    break
            else:
                _tr, _tc = self.find_item_new_pos(item)
                if _tr == -1 and _tc == -1:
                    _tx, _ty = self.convert_pos_to_px(0,0)
                else:
                    _tx, _ty = self.convert_pos_to_px(_tr,_tc)
            #
            self.populate_items(_tx,_ty, _tr, _tc, item, "file")
            
        #
        gdir = Gio.File.new_for_path(DESKTOP_PATH)
        self.monitor = gdir.monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
        self.monitor.connect("changed", self.on_directory_changed)
        
        
    def on_drag_prepare(self, ctrl, _x, _y, data=None):
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
        _operation = ""
        if  ctrl.get_actions() == Gdk.DragAction.COPY:
            _operation = "copy"
        elif ctrl.get_actions() == Gdk.DragAction.MOVE:
            _operation = "cut"
        
        if _operation == "":
            return
        
        if isinstance(value, Gdk.FileList):
            files = value.get_files()
            for ff in files:
                file_name = ff.get_path()
                item = os.path.basename(file_name)
                folder_source = os.path.dirname(file_name)
                if folder_source == DESKTOP_PATH:
                    return
                if not os.path.exists(os.path.join(DESKTOP_PATH,item)):
                    file_name = os.path.join(DESKTOP_PATH,item)
                elif not os.path.exists(os.path.join(DESKTOP_PATH,item+".new")):
                    file_name = os.path.join(DESKTOP_PATH,item+".new")
                else:
                    _item = item
                    i = 1
                    while os.path.exists(os.path.join(DESKTOP_PATH,_item)):
                        _item += ".new_"+str(i)
                    else:
                        file_name = os.path.join(DESKTOP_PATH,_item)
                if os.path.exists(file_name):
                    continue
                if _operation == "copy":
                    try:
                        if os.path.isdir(ff.get_path()) and not os.path.islink(ff.get_path()):
                            shutil.copytree(ff.get_path(), file_name)
                        else:
                            shutil.copy2(ff.get_path(), file_name)
                    except:
                        pass
                elif _operation == "cut":
                    try:
                        shutil.move(ff.get_path(), file_name)
                    except:
                        pass
    
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
    
    # convert pixel coordinates into position
    def convert_pos_to_px(self, r,c):
        x = r * self.widget_size_w+LEFT_MARGIN
        y = c * self.widget_size_h+TOP_MARGIN
        return (x,y)
        
    # convert position into pixel coordinates
    def convert_px_to_pos(self, x,y):
        c = int((x-LEFT_MARGIN)/self.widget_size_w)
        r = int((y-TOP_MARGIN)/self.widget_size_h)
        return (r,c)
        
    def find_item_new_pos(self, item):
        for r in range(self.num_columns):
            for c in range(self.num_rows):
                if (r,c) not in self.WIDGET_LIST_POS:
                    return (r,c)
        return (-1,-1)
        
    # type can be "file" or "device"
    def populate_items(self, _x, _y, _r, _c, _name, _type):
        custom = customItem(self, self.widget_size_w,self.widget_size_h, self.w_icon_size, self._fm, self._font_size, _name)
        custom.x = _x
        custom.y = _y
        custom.r = _r
        custom.c = _c
        custom.__type = _type
        self._fixed.put(custom, _x, _y)
        self.WIDGET_LIST.append(custom)
        self.WIDGET_LIST_POS.append((_r,_c))
        # skip items already registered
        if (_name,_r,_c) not in self.WIDGET_LIST_PATH_POS:
            self.WIDGET_LIST_PATH_POS.append((_name,_r,_c))
    
    def on_directory_changed(self, monitor, _file1, _file2, event):
        if event == Gio.FileMonitorEvent.DELETED or event == Gio.FileMonitorEvent.MOVED_OUT: # done
            item = os.path.basename(_file1.get_path())
            for el in self.WIDGET_LIST[:]:
                if el._itext == item:
                    self._fixed.remove(el)
                    self.WIDGET_LIST.remove(el)
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
        
        elif event == Gio.FileMonitorEvent.CREATED or event == Gio.FileMonitorEvent.MOVED_IN: # done
            item = os.path.basename(_file1.get_path())
            _tr, _tc = self.find_item_new_pos(item)
            if _tr == -1 and _tc == -1:
                _tx, _ty = self.convert_pos_to_px(0,0)
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
            button_open.set_halign(Gtk.Align.START)
            button_open.connect("clicked", self.on_button_clicked, "open", popover)
            popover_box.append(button_open)
            style_context_open = button_open.get_style_context()
            style_context_open.add_class("ctxbtnbg")
            
            _exp1 = Gtk.Expander.new(label="Open with...")
            _exp1.set_resize_toplevel(True)
            popover_box.append(_exp1)
            box_exp1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            _exp1.set_child(box_exp1)
            #
            button2 = Gtk.Button(label="Click Me 2")
            button2.set_halign(Gtk.Align.START)
            button2.connect("clicked", self.on_button_clicked, "non so 2", _item, popover)
            box_exp1.append(button2)
            style_context_btn2 = button2.get_style_context()
            style_context_btn2.add_class("ctxbtnbg")
            
            button_copy = Gtk.Button(label="Copy")
            button_copy.set_halign(Gtk.Align.START)
            button_copy.connect("clicked", self.on_button_clicked, "copy", _item, popover)
            popover_box.append(button_copy)
            style_context_copy = button_copy.get_style_context()
            style_context_copy.add_class("ctxbtnbg")
            
            button_cut = Gtk.Button(label="Cut")
            button_cut.set_halign(Gtk.Align.START)
            button_cut.connect("clicked", self.on_button_clicked, "cut", _item, popover)
            popover_box.append(button_cut)
            style_context_cut = button_cut.get_style_context()
            style_context_cut.add_class("ctxbtnbg")
            
            button_trash = Gtk.Button(label="Trash")
            button_trash.set_halign(Gtk.Align.START)
            button_trash.connect("clicked", self.on_button_clicked, "trash", _item, popover)
            popover_box.append(button_trash)
            style_context_trash = button_trash.get_style_context()
            style_context_trash.add_class("ctxbtnbg")
            
            button_delete = Gtk.Button(label="Delete")
            button_delete.set_halign(Gtk.Align.START)
            button_delete.connect("clicked", self.on_button_clicked, "delete", _item, popover)
            popover_box.append(button_delete)
            style_context_delete = button_delete.get_style_context()
            style_context_delete.add_class("ctxbtnbg")
            
            button_rename = Gtk.Button(label="Rename")
            button_rename.set_halign(Gtk.Align.START)
            button_rename.connect("clicked", self.on_button_clicked, "rename", _item, popover)
            popover_box.append(button_rename)
            style_context_rename = button_rename.get_style_context()
            style_context_rename.add_class("ctxbtnbg")
            
            button_property = Gtk.Button(label="Property")
            button_property.set_halign(Gtk.Align.START)
            button_property.connect("clicked", self.on_button_clicked, "property", _item, popover)
            popover_box.append(button_property)
            style_context_property = button_property.get_style_context()
            style_context_property.add_class("ctxbtnbg")
            
            css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            css = ".ctxbtnbg {border: 0px;}"
            css_provider.load_from_data(css.encode('utf-8'))
            
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
            button_copy.set_halign(Gtk.Align.START)
            button_copy.connect("clicked", self.on_button_clicked, "copy", _iteml, popover)
            popover_box.append(button_copy)
            style_context_copy = button_copy.get_style_context()
            style_context_copy.add_class("ctxbtnbg")
            
            button_cut = Gtk.Button(label="Cut")
            button_cut.set_halign(Gtk.Align.START)
            button_cut.connect("clicked", self.on_button_clicked, "cut", _iteml, popover)
            popover_box.append(button_cut)
            style_context_cut = button_cut.get_style_context()
            style_context_cut.add_class("ctxbtnbg")
            
            button_trash = Gtk.Button(label="Trash")
            button_trash.set_halign(Gtk.Align.START)
            button_trash.connect("clicked", self.on_button_clicked, "trash", _iteml, popover)
            popover_box.append(button_trash)
            style_context_trash = button_trash.get_style_context()
            style_context_trash.add_class("ctxbtnbg")
            
            button_delete = Gtk.Button(label="Delete")
            button_delete.set_halign(Gtk.Align.START)
            button_delete.connect("clicked", self.on_button_clicked, "delete", _iteml, popover)
            popover_box.append(button_delete)
            style_context_delete = button_delete.get_style_context()
            style_context_delete.add_class("ctxbtnbg")
            
            button_property = Gtk.Button(label="Property")
            button_property.set_halign(Gtk.Align.START)
            button_property.connect("clicked", self.on_button_clicked, "property", _iteml, popover)
            popover_box.append(button_property)
            style_context_property = button_property.get_style_context()
            style_context_property.add_class("ctxbtnbg")
            
            css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            css = ".ctxbtnbg {border: 0px;}"
            css_provider.load_from_data(css.encode('utf-8'))
            
            popover.set_child(popover_box)
            
            #
            _rect = Gdk.Rectangle()
            _rect.x = _item.x + _x + 1
            _rect.y = _item.y + _y + 1
            _rect.width = 1
            _rect.height = 1
            popover.set_pointing_to(_rect)
            popover.popup()
            
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
                    print("1203", str(E))
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
                print("1215", str(E))
                _errors += str(E)+"\n"
            _popover.popdown()
    
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
                if os.path.exists(os.path.join(DESKTOP_PATH,_f_n)):
                    continue
                if _operation == "copy":
                    if os.path.isdir(_file) and not os.path.islink(_file):
                        shutil.copytree(_file, os.path.join(DESKTOP_PATH,_f_n))
                    else:
                        shutil.copy2(_file, os.path.join(DESKTOP_PATH,_f_n))
                elif _operation == "cut":
                    shutil.move(_file, os.path.join(DESKTOP_PATH,_f_n))
            except Exception as E:
                print("1257:", str(E))
                _errors += str(E)+"\n"
    
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
            style_context_paste = button.get_style_context()
            style_context_paste.add_class("ctxbtnbg")
            #
            button_close = Gtk.Button(label="Close")
            button_close.connect("clicked", lambda w:ren_pop.popdown())
            popover_box.append(button_close)
            style_context_paste = button_close.get_style_context()
            style_context_paste.add_class("ctxbtnbg")
            #
            css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            css = ".ctxbtnbg {border: 0px;}"
            css_provider.load_from_data(css.encode('utf-8'))
            #
            ren_pop.set_child(popover_box)
            #
            if isinstance(_item, list):
                _r = _item[-1].r
                _c = _item[-1].c
                _x = _item[-1].x-int(LEFT_MARGIN/2)
                _y = _item[-1].y+self.w_icon_size+10
            else:
                _r = _item.r
                _c = _item.c
                _x = _item.x-int(LEFT_MARGIN/2)
                _y = _item.y+self.w_icon_size+10
            _rect = Gdk.Rectangle()
            _rect.x = _x + 1
            _rect.y = _y + 1
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
            style_context_paste = button.get_style_context()
            style_context_paste.add_class("ctxbtnbg")
            #
            button_close = Gtk.Button(label="Close")
            button_close.connect("clicked", lambda w:ren_pop.popdown())
            popover_box.append(button_close)
            style_context_paste = button_close.get_style_context()
            style_context_paste.add_class("ctxbtnbg")
            #
            css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            css = ".ctxbtnbg {border: 0px;}"
            css_provider.load_from_data(css.encode('utf-8'))
            #
            ren_pop.set_child(popover_box)
            #
            if isinstance(_item,list):
                _r = _item[-1].r
                _c = _item[-1].c
                _x = _item[-1].x-int(LEFT_MARGIN/2)
                _y = _item[-1].y+self.w_icon_size+10
            else:
                _r = _item.r
                _c = _item.c
                _x = _item.x-int(LEFT_MARGIN/2)
                _y = _item.y+self.w_icon_size+10
            _rect = Gdk.Rectangle()
            _rect.x = _x + 1
            _rect.y = _y + 1
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
                style_context_paste = button.get_style_context()
                style_context_paste.add_class("ctxbtnbg")
                #
                button_close = Gtk.Button(label="Close")
                button_close.connect("clicked", lambda w:ren_pop.popdown())
                popover_box.append(button_close)
                style_context_paste = button_close.get_style_context()
                style_context_paste.add_class("ctxbtnbg")
                #
                css_provider = Gtk.CssProvider()
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                css = ".ctxbtnbg {border: 0px;}"
                css_provider.load_from_data(css.encode('utf-8'))
                #
                ren_pop.set_child(popover_box)
                #
                _r = _item.r
                _c = _item.c
                _x = _item.x-int(LEFT_MARGIN/2)
                _y = _item.y+self.w_icon_size+10
                _rect = Gdk.Rectangle()
                _rect.x = _x + 1
                _rect.y = _y + 1
                _rect.width = 1
                _rect.height = 1
                ren_pop.set_pointing_to(_rect)
                ren_pop.popup()
    
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
        button.set_halign(Gtk.Align.START)
        button.set_hexpand(True)
        style_context_property = button.get_style_context()
        style_context_property.add_class("ctxbtnbg")
        button.connect("clicked", self.on_button_clicked, "booo", _item, popover)
        popover_box.append(button)
        
        _exp1 = Gtk.Expander.new(label="EXPANDER")
        _exp1.set_resize_toplevel(True)
        popover_box.append(_exp1)
        box_exp1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        _exp1.set_child(box_exp1)
        
        button_paste = Gtk.Button(label="Paste")
        button_paste.set_halign(Gtk.Align.START)
        button_paste.connect("clicked", self.on_button_clicked, "paste", [], popover)
        popover_box.append(button_paste)
        style_context_paste = button_paste.get_style_context()
        style_context_paste.add_class("ctxbtnbg")
        
        button2 = Gtk.Button(label="Click Me 2")
        button2.set_halign(Gtk.Align.START)
        style_context_property = button2.get_style_context()
        style_context_property.add_class("ctxbtnbg")
        button2.connect("clicked", self.on_button_clicked, "cioa", _item, popover)
        box_exp1.append(button2)
        
        popover.set_child(popover_box)
        
        ######
        css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        css = ".ctxbtnbg {border: 0px;}"
        css_provider.load_from_data(css.encode('utf-8'))
        #
        _rect = Gdk.Rectangle()
        _rect.x = _x + 1
        _rect.y = _y + 1
        _rect.width = 1
        _rect.height = 1
        popover.set_pointing_to(_rect)
        popover.popup()
        
    def on_draw(self, da, cr, w, h, data):
        if self.left_click_setted == 1:
            w = self.end_x
            h = self.end_y
            # adding a border
            cr.set_source_rgba(0, 0, 0, 0.5)
            cr.set_line_width(1.0)
            cr.rectangle(self.start_x,self.start_y,w,h)
            cr.stroke()
            #
            cr.set_source_rgba(1.0, 0.0, 0.0, 0.2)
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
        # print("gesture c")
    
    def on_da_gesture_r(self, o,n,x,y):
        self.background_context_menu(self._fixed, x, y)
    
    # def on_right_pressed(self, o,n,x,y,da):
        # print("right mouse pressed")
    
    # drag begin
    def on_da_gesture_d_b(self, gesture_drag, start_x, start_y, da):
        self.start_x = start_x
        self.start_y = start_y
        
    # drag update
    def on_da_gesture_d_u(self, gesture_drag, offset_x, offset_y, da):
        if abs(offset_x) > 4:
            # the rubberband
            self.end_x = offset_x
            self.end_y = offset_y
            da.queue_draw()
            
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
        if abs(offset_x) > 4:
            # reset
            self.start_x = 0
            self.start_y = 0
            self.end_x = 0
            self.end_y = 0
            da.queue_draw()
        
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

#!/usr/bin/env python3

# V 0.5

from searchercfg import *
from searcherlang import *

import sys,os
import gi
gi.require_version("Gdk", "4.0")
gi.require_version('Gtk', '4.0')
from gi.repository import Gdk,Gtk,Gio,GLib
from gi.repository import GdkPixbuf
from pathlib import Path
import sqlite3
import subprocess

# program directory
main_dir = os.getcwd()
# home directory
homepath = str(Path.home())

_DATABASE = os.path.join(main_dir, "DATABASE", "default.db")

icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

WW = WINDOWWIDTH
HH = WINDOWHEIGHT

# 0 no - 1 yes
ROUNDED_IMG = 0
# 0 square - 1 full rounded
ICON_ROUNDENESS = 1

# 1: whether to fetch the content of the files while searching
# 0: only after selected the item in the result list
CONTEXTUAL_FETCH = 0 # only 0

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(WW, 40)
        self.app_ = self.get_application()
        
        self.set_decorated(False)
        self.set_title("Searcher")
        self.set_icon_name("search")
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(os.path.join(main_dir,"configs/appstyle.css"))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.set_name("mainwin")
        
        self.main_vertical_box = Gtk.Box.new( Gtk.Orientation.VERTICAL,10)
        # self.set_child(self.main_vertical_box)
        
        self.set_margin_bottom(10)
        self.set_margin_end(10)
        self.set_margin_start(10)
        self.set_margin_top(10)
        
        #
        self._stack = Gtk.Stack()
        self.set_child(self._stack)
        self._stack.add_child(self.main_vertical_box)
        
        self.btn_box = Gtk.Box.new(0,0)
        self.main_vertical_box.append(self.btn_box)
        
        self.main_entry = Gtk.SearchBar.new()
        self.main_entry.set_hexpand(True)
        self.btn_box.append(self.main_entry)
        self.main_entry.set_search_mode(True)
        self.main_entry.set_show_close_button(False)
        self._entry = Gtk.Entry.new()
        self._entry.set_hexpand(True)
        self._entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear")
        self.main_entry.set_child(self._entry)
        # self.main_entry.connect_entry(self._entry)
        
        # self._entry.connect('changed', self.on_changed)
        self._entry.connect('activate', self.on_activate)
        self._entry.connect('icon-release', self.on_icon_pressed)
        
        keycontroller = Gtk.EventControllerKey()
        keycontroller.connect('key-pressed', self.on_key_pressed)
        # # keycontroller.connect('key-released', self.on_key_released)
        self.add_controller(keycontroller)
        
        self.entry_buffer = self._entry.get_buffer()
        # self.entry_buffer.connect('inserted-text', self.on_entry_inserted_text)
        
        self.scroll_win = Gtk.ScrolledWindow.new()
        self.scroll_win.set_vexpand(True)
        self.main_vertical_box.append(self.scroll_win)
        self.scroll_win.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        # self.scroll.set_propagate_natural_width(True)
        # self.scroll_win.set_propagate_natural_height(True)
        
        self.list_box = Gtk.ListBox.new()
        self.list_box.set_vexpand(True)
        if USE_APPS == 1:
            self.list_box.set_activate_on_single_click(True)
            self.list_box.connect('row-activated', self.on_list_box)
        self.scroll_win.set_child(self.list_box)
        
        self.scroll_win.set_visible(False)
        ##############
        # connection to the database
        con = sqlite3.connect(_DATABASE)
        self.cur = con.cursor()
        
        ##############
        self.button1 = Gtk.Button.new_from_icon_name("reload")
        self.button1.add_css_class("flat")
        self.button1.connect("clicked",self.on_button_1)
        self.btn_box.append(self.button1)
        
    # the delete text pressed
    def on_icon_pressed(self, _w, _pos):
        self.entry_buffer.delete_text(0, -1)
        self.scroll_win.set_visible(False)
        self.set_default_size(WW, 40)
    
    # enter pressed
    def on_activate(self, w):
        self.list_box.remove_all()
        _text = self.entry_buffer.get_text()
        ####
        self.list_files = []
        ### AND
        try:
            self.cur.execute("""select name, mime, dir, ROWID from tabella where content match ?""", (_text,))
            rae = self.cur.fetchall()
            for lenrae in range(len(rae)):
                nname = rae[lenrae][0]
                ttype = rae[lenrae][1]
                ffolder = rae[lenrae][2]
                rrowid = rae[lenrae][3]
                self.list_files.append([nname,ttype,ffolder, rrowid])
        except Exception as E:
            self.list_files = []
        #
        if len(self.list_files) > 0:
            self.scroll_win.set_visible(True)
            self.set_default_size(WW, HH)
        ##
        # list_path = []
        for el in self.list_files:
            # _label = el[0]
            _label = el[0]+"\n"+"<i><small>"+el[2]+"</small></i>"
            row = Gtk.ListBoxRow()
            row.set_name("lrow")
            row._item = el
            row._ret = ""
            row._name = ""
            row._data1 = ""
            # list_path.append(el[2])
            # if CONTEXTUAL_FETCH or el[1] in ["text/calendar", "text/vcard"]:
            if el[1] in ["text/calendar", "text/vcard"]:
                self.cur.execute("SELECT * FROM tabella where ROWID=(?);", (el[3],))
                ret = self.cur.fetchone()
                row._ret = ret
                if el[1] == "text/calendar":
                    try:
                        tmp_body = ret[4]
                        tmp_summ = tmp_body.split("\n")
                        for ell in tmp_summ:
                            if ell.lstrip()[0:8] == "SUMMARY:":
                                _label = ell[8:].lstrip()+"\n<i><small>{}</small></i>".format(WCALENDAR)
                                row._name = ell[8:].lstrip()
                        date_date = ret[4]
                        tmp_date = date_date.split("\n")
                        for ell in tmp_date:
                            if ell.lstrip()[0:8] == "DTSTART:":
                                row._data1 = ell[8:].lstrip()
                    except:
                        pass
                elif el[1] == "text/vcard":
                    try:
                        tmp_body = ret[4]
                        tmp_name = tmp_body.split("\n")
                        for ell in tmp_name:
                            if ell.lstrip()[0:3] == "FN:":
                                # _label = ell[2:].lstrip()
                                _label = ell[3:].lstrip()+"\n<i><small>{}</small></i>".format(WCONTACT)
                                row._name = ell[3:].lstrip()
                            elif ell.lstrip()[0:2] == "N:":
                                row._data1 = ell[2:].lstrip()
                    except Exception as E:
                        pass
            elif el[1] in ["application/mbox","message/rfc822"]:
                self.cur.execute("SELECT * FROM tabella where ROWID=(?);", (el[3],))
                ret = self.cur.fetchone()
                m_data_tmp = ret[4]
                m_data = m_data_tmp.split("\n")
                email_from = ""
                email_date = ""
                for eel in m_data:
                    if eel.lower().lstrip()[0:5] == 'from:':
                        email_from = eel[5:].lstrip()
                        row._name = email_from
                    elif eel.lower().lstrip()[0:5] == 'date:':
                        email_date = eel[5:].lstrip()
                        row._data1 = email_date
                if email_from != "":
                    _label="{} {}\n<i><small>{}</small></i>".format(WFROM,GLib.markup_escape_text(email_from), GLib.markup_escape_text(email_date))
            #
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            vbox.append(hbox)
            row.set_child(vbox)
            #
            if el[1]:
                _icon = Gio.content_type_get_icon(el[1])
                _img = Gtk.Image.new_from_gicon(_icon)
                _img.set_pixel_size(ICON_SIZE)
                hbox.append(_img)
            
            # if icon_theme.has_icon(el[1]):
                # _pb = icon_theme.lookup_icon(el[1], None, ICON_SIZE, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.FORCE_REGULAR)
            else:
                _image_path = os.path.join(main_dir,"icons","generic-icon.svg")
                _pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(_image_path,ICON_SIZE,ICON_SIZE,True)
                _pb = Gdk.Texture.new_for_pixbuf(_pix)
                #
                # if ROUNDED_IMG:
                    # _snapshot = Gtk.Snapshot.new()
                    # #
                    # _r = Graphene.Rect.alloc()
                    # _r.init(0,0,ICON_SIZE,ICON_SIZE)
                    # #
                    # _rr = Gsk.RoundedRect()
                    # _rr.init_from_rect(_r, ((ICON_SIZE*ICON_ROUNDENESS)/2))
                    # _rr.normalize()
                    # #
                    # _snapshot.push_rounded_clip(_rr)
                    # _snapshot.append_texture(_pb, _r)
                    # _snapshot.pop()
                    # #
                    # _rs = Graphene.Size()
                    # _rs.init(ICON_SIZE,ICON_SIZE)
                    # _pb = _snapshot.to_paintable(_rs)
                #
                _img = Gtk.Image.new_from_paintable(_pb)
                _img.set_pixel_size(ICON_SIZE)
                hbox.append(_img)
            #
            _lbl1 = Gtk.Label()
            _lbl1.set_hexpand(True)
            _lbl1.set_halign(1)
            _lbl1.set_wrap(True)
            _lbl1.set_wrap_mode(2)
            hbox.append(_lbl1)
            # _lbl1.set_label(_label)
            _lbl1.set_markup(_label)
            #
            # if el[1] not in ["application/mbox","message/rfc822"]:
            # btn_stack = Gtk.Button(label=">")
            btn_stack = Gtk.Button()
            btn_stack.add_css_class("flat")
            btn_stack.set_name("databtn")
            
            _btn_icon_name = "arrow-right"
            if icon_theme.has_icon(_btn_icon_name):
                ICON_SIZE2 = 16
                _pb = icon_theme.lookup_icon(_btn_icon_name, None, ICON_SIZE2, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.FORCE_REGULAR)
                _img = Gtk.Image.new_from_paintable(_pb)
                # _img.set_pixel_size(ICON_SIZE2)
                btn_stack.set_child(_img)
            else:
                btn_stack.set_label(">")
            
            btn_stack.connect("clicked", self.on_btn_stack, row)
            hbox.append(btn_stack)
            #
            self.list_box.append(row)
    
    # open the file with its default application if registered
    def on_list_box(self, _w, _r):
        # list box row activted ['file_name', 'mimetype', 'FILE_PATH', ROWID]
        item = _r._item
        _type = item[1]
        if _type in ["text/calendar","text/vcard","message/rfc822","application/mbox"]:
            f_data = _r._name
            f_data1 = ""
            if _type == "text/calendar":
                f_exec = os.path.join(main_dir,"calendar.sh")
                f_data1 = _r._data1
            elif _type == "text/vcard":
                f_exec = os.path.join(main_dir,"vcard.sh")
                f_data1 = _r._data1
            elif _type in ["message/rfc822","application/mbox"]:
                f_exec = os.path.join(main_dir,"email.sh")
                f_data1 = _r._data1
            try:
                subprocess.Popen([f_exec, f_data, f_data1])
                self.close()
            except:
                pass
        else:
            _file = item[2]+"/"+item[0]
            _f = Gio.File.new_for_path(_file)
            _launcher = Gtk.FileLauncher.new(_f)
            _launcher.set_always_ask(True)
            _launcher.launch(None, None, self.on_launched, None)
    
    def on_launched(self, ource_object, res, data):
        self.close()
    
    def on_btn_stack(self, _b, _r):
        vbox = Gtk.Box.new(1,0)
        self._stack.add_child(vbox)
        #
        stack_list = Gtk.Stack()
        stack_list.set_vexpand(True)
        #
        _stacksw = Gtk.StackSwitcher()
        _stacksw.set_stack(stack_list)
        vbox.append(_stacksw)
        vbox.append(stack_list)
        #
        self._iii = 1
        self.on_get_data(_r, stack_list)
        #
        back_btn = Gtk.Button(label=WBACK)
        vbox.append(back_btn)
        back_btn.connect("clicked", self.on_back_stack, vbox)
        #
        self._stack.set_visible_child(vbox)
        try:
            stack_list.set_visible_child_name(str(1))
        except:
            pass
    
    def on_back_stack(self, _b, _box):
        self._stack.set_visible_child(self.main_vertical_box)
        self._stack.remove(_box)
    
    def populate_list(self, _data, _type, stack_list, _row):
        _stack_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        
        scroll_stack = Gtk.ScrolledWindow.new()
        scroll_stack.set_vexpand(True)
        scroll_stack.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        # scroll_stack.set_hexpand(True)
        # scroll_stack.set_vexpand(True)
        scroll_stack.set_propagate_natural_width(True)
        scroll_stack.set_propagate_natural_height(True)
        
        lbl = Gtk.Label()
        lbl.set_wrap(True)
        lbl.set_wrap_mode(2)
        #
        # METADATA - TAGS
        if self._iii == 1:
            lbl.set_name("datalbl")
            # _ret = self.cur.execute("""select metadata,content,tag1 from tabella where name=(?) and dir=(?)""", (namefile, pathfile))
            self.cur.execute("""select metadata,tag1 from tabella where ROWID=(?)""", (_row,))
            _ret = self.cur.fetchall()
            if _ret != []:
                _metadata = _ret[0][0]
                _tags = _ret[0][1]
                #
                _label = ""
                if _metadata != "":
                    _label = _metadata
                if _tags != "":
                    _label += "\n{} ".format(WTAGS)+_tags
                if _data != "":
                    _metadata_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
                    lbl0 = Gtk.Label()
                    lbl0.set_name("metadatalbl")
                    lbl0.set_wrap(True)
                    lbl0.set_wrap_mode(2)
                    stack_list.add_titled(_metadata_vbox,str(0),WMETADATA)
                    lbl0.set_markup(GLib.markup_escape_text(_label))
                    box_lbl0 = Gtk.Box.new(0,0)
                    # box_lbl0.append(lbl0)
                    #
                    scroll_stack0 = Gtk.ScrolledWindow.new()
                    scroll_stack0.set_vexpand(True)
                    scroll_stack0.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                    scroll_stack0.set_propagate_natural_width(True)
                    scroll_stack0.set_propagate_natural_height(True)
                    scroll_stack0.set_child(lbl0)
                    box_lbl0.append(scroll_stack0)
                    #
                    _metadata_vbox.append(box_lbl0)
        # else:
        stack_list.add_titled(_stack_vbox,str(self._iii),WEXTRACT+str(self._iii))
        #
        lbl.set_markup(_data)
        lbl.set_margin_end(10)
        lbl.set_margin_start(10)
        box_lbl = Gtk.Box.new(0,0)
        # box_lbl.append(lbl)
        #
        scroll_stack.set_child(lbl)
        box_lbl.append(scroll_stack)
        #
        _stack_vbox.append(box_lbl)
        #
        self._iii += 1
        
    
    def on_get_data(self, _r, stack_list):
        _text = self.entry_buffer.get_text()
        item = _r._item
        _type = item[1]
        _row = item[3]
        if CONTEXTUAL_FETCH == 1:
            item_content = _r._ret
            _data = item_content[4]
            list_text = []
            # list of searching terms
            temp3 = _text.split()
            # remove OR if or is chosed
            try:
                temp3.remove("OR")
            except:
                pass
            # divides the text in pieces depending on the searching words
            rret = 0
            for _t in temp3:
                rret = _data.find(_t, rret)
                if rret == -1:
                    rret = 0
                    continue
                # text not splitted but formatted
                if item[1] in ["text/calendar", "text/vcard"]:
                    self.populate_list(_data, _type, stack_list, _row)
                    break
                else:
                    _l = _data[max(0, rret-100):rret+len(_t)+100]
                    rret += len(_t)
                    rret = 0
                    self.populate_list(_l, _type, stack_list, _row)
        else:
            _file = item[0]
            _id = item[3]
            self.cur.execute("""select offsets(tabella) from tabella where name=? AND content match ? AND ROWID=(?)""", (_file, _text, _id))
            ret = self.cur.fetchall()
            _data_tmp = ret[0][0]
            _data = _data_tmp.split(" ")
            len_data = len(_data)
            ###
            list_data = []
            for i in range(0,len_data,4):
                list_data.append([_data[i],_data[i+1],_data[i+2],_data[i+3]])
            # LIST DATA::  [['4', '0', '5', '7'], ['4', '0', '31', '7']]
            
            namefile = item[0]
            pathfile = item[2]
            
            # the starting character - index
            _start = 0
            # the last character to extract - index
            _end = PREVIEW
            
            for i in range(len(list_data)):
                _d = list_data[i]
                if int(_d[2]) > int(PREVIEW/2):
                    _start = int(PREVIEW/3)
                    _end = _start*3
                elif int(_d[2]) > PREVIEW:
                    _start = int(PREVIEW/2)
                    _end = _start*2
                    
                # the bound preview of the seeking text
                # self.cur.execute("""select substr(content,?,?) from tabella where name=(?) and dir=(?)""", (_start, _end, namefile, pathfile))
                self.cur.execute("""select substr(content,?,?) from tabella where name=(?) and dir=(?) and ROWID=(?)""", (_start, _end, namefile, pathfile, _id))
                ret = self.cur.fetchall()
                # list of searching terms
                temp3 = _text.split()
                # remove OR if or is chosed
                try:
                    temp3.remove("OR")
                except:
                    pass
                
                # use the markup or not
                if USE_MARKUP:
                    dic = {x: '<b>'+x+'</b>' for x in temp3}
                    # replace and set to bold each searched word
                    def replace_all(text, dic):
                        for i, j in dic.items():
                            text = text.replace(i, j)
                        return text
                    
                    aaaaa = ret[0][0]
                    aaaaal = replace_all(aaaaa.lower().replace("<", "&lt;").replace(">", "&gt;"),dic)
                    self.populate_list(aaaaal, _type, stack_list, _row)
                else:
                    self.populate_list(ret[0][0], _type, stack_list, _row)
    
    def on_key_pressed(self, event, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
    
    def on_button_1(self, btn):
        _pop = Gtk.Popover()
        _pop.set_has_arrow(False)
        _pop.set_halign(Gtk.Align.START)
        _pop.set_parent(btn)
        popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        _pop.set_child(popover_box)
        pop_btn = Gtk.Button(label=WREBUILTDATABASE)
        pop_btn.add_css_class("flat")
        pop_btn.connect('clicked', self.button_1_clicked, _pop)
        popover_box.append(pop_btn)
        _pop.popup()
        
    def button_1_clicked(self, _b, _pop):
        _pop.popdown()
        
        self.entry_buffer.delete_text(0, -1)
        self.scroll_win.set_visible(False)
        self.set_default_size(WW, 40)
        
        try:
            _p = os.path.join(main_dir, "indexerdb.py")
            ret = subprocess.run([_p], capture_output=True, text=True)
            ret_code = ret.returncode
            ret_stdout = ret.stdout
            myDialog(self, ret_stdout.strip("\n").split(" "))
        except:
            pass
        

class myDialog(Gtk.Window):
    def __init__(self, _parent, _data):
        super().__init__()
        self._parent = _parent
        self.set_name('mydialog')
        
        # self.set_size_request(400, 400)
        self.main_box = Gtk.Box.new(1,0)
        self.set_child(self.main_box)
        
        # files: processed - added - deleted - discharged - folder not in place - folders and files issues during indexing
        llist = "{} {} \n{} {} \n{} {} \n{} {} \n{} {} \n{} {}".format(WFPROCESSED,_data[0], WFADDED,_data[1], WFDELETED,_data[2], WFDISCHARGED,_data[3], WMISSINGFOLDERS,_data[4], WISSUESINDEXING,_data[5])
        lbl = Gtk.Label(label = llist)
        self.main_box.append(lbl)
        
        btn_close = Gtk.Button(label=WCLOSE)
        self.main_box.append(btn_close)
        btn_close.connect('clicked', lambda _w:self.close())
        
        self.set_visible(True)

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def do_activate(self):
        active_window = self.props.active_window
        if active_window:
            active_window.present()
        else:
            self.win = MainWindow(application=self)
            self.win.present()



app = MyApp(application_id="com.gsearcher.myapp",flags= Gio.ApplicationFlags.FLAGS_NONE)
app.run(sys.argv)
#!/usr/bin/env python3

# V. 1.1

BWIDTH=340
IS_WAYLAND=1

if IS_WAYLAND:
    from ctypes import CDLL
    try:
        CDLL('libgtk4-layer-shell.so.0')
    except:
        try:
            CDLL('libgtk4-layer-shell.so.1.0.4')
        except:
            try:
                CDLL('./libgtk4-layer-shell.so')
            except:
                IS_WAYLAND = 0

import gi
gi.require_version("Gtk", "4.0")
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, GLib, Gio, Gdk, GObject

gi.require_version("Polkit", "1.0")
gi.require_version("PolkitAgent", "1.0")
from gi.repository import Polkit, PolkitAgent

gi.require_version("Adw", "1")
from gi.repository import Adw

import os,sys,pwd # ,signal

if IS_WAYLAND:
    gi.require_version('Gtk4LayerShell', '1.0')
    from gi.repository import Gtk4LayerShell as GtkLayerShell
    
    _display = Gdk.Display.get_default()
    display_type = GObject.type_name(_display.__gtype__)
    if not display_type=="GdkWaylandDisplay":
        IS_WAYLAND = 0
    ret = GtkLayerShell.is_supported()
    if ret == False:
        IS_WAYLAND = 0

QUIT = False

def quit_(window):
    global QUIT
    QUIT = True

OBJECT_PATH = "/io/github/calculon/polkitwindow4/PolkitAgent"
AGENT_XML = """<node><interface name="org.freedesktop.PolicyKit1.AuthenticationAgent">
  <method name="BeginAuthentication">
    <arg type="s" name="action_id" direction="in"/><arg type="s" name="message" direction="in"/>
    <arg type="s" name="icon_name" direction="in"/><arg type="a{ss}" name="details" direction="in"/>
    <arg type="s" name="cookie" direction="in"/><arg type="a(sa{sv})" name="identities" direction="in"/>
  </method>
  <method name="CancelAuthentication"><arg type="s" name="cookie" direction="in"/></method>
</interface></node>"""
AUTHORITY = ("org.freedesktop.PolicyKit1", "/org/freedesktop/PolicyKit1/Authority",
             "org.freedesktop.PolicyKit1.Authority")

def _identity(kind: str, details: dict):
    try:
        if kind == "unix-user" and "uid" in details:
            return Polkit.UnixUser.new(int(details["uid"]))
        if kind == "unix-group" and "gid" in details:
            return Polkit.UnixGroup.new(int(details["gid"]))
    except (TypeError, ValueError):
        pass
    return None

def _user(identity) -> str:
    if isinstance(identity, Polkit.UnixUser):
        try:
            return pwd.getpwuid(identity.get_uid()).pw_name
        except KeyError:
            return str(identity.get_uid())
    return identity.to_string()


def _real_name(name: str) -> str:
    try:
        gecos = pwd.getpwnam(name).pw_gecos.split(",")[0]
    except KeyError:
        gecos = ""
    return gecos or name

class Agent:
    
    def __init__(self, app):
        self.app = app
        self.dialogs = {}
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        try:
            self.polkitd = self.bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus",
                                              "org.freedesktop.DBus", "GetNameOwner",
                                              GLib.Variant("(s)", (AUTHORITY[0],)), None,
                                              Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
        except GLib.Error:
            self.polkitd = None
        
        self.watch = Gio.bus_watch_name_on_connection(
            self.bus, AUTHORITY[0], Gio.BusNameWatcherFlags.NONE,
            lambda _c, _n, owner: setattr(self, "polkitd", owner),
            lambda *_a: setattr(self, "polkitd", None))
        node = Gio.DBusNodeInfo.new_for_xml(AGENT_XML)
        self.reg = self.bus.register_object(OBJECT_PATH, node.interfaces[0], self._call, None, None)
        
    def _call(self, _conn, sender, _path, _iface, method, params, invocation):
        if sender is None or sender != self.polkitd:
            invocation.return_dbus_error("org.freedesktop.PolicyKit1.Error.NotAuthorized",
                                         "Only polkitd may call the authentication agent")
            return
        if method == "CancelAuthentication":
            (cookie,) = params.unpack()
            dlg = self.dialogs.get(cookie)
            invocation.return_value(None)
            if dlg:
                dlg.finish(False)
            return
        action_id, message, _icon, _details, cookie, identities = params.unpack()
        ids = [i for i in (_identity(kind, det) for kind, det in identities) if i is not None]
        if not ids:
            invocation.return_dbus_error("org.freedesktop.PolicyKit1.Error.Failed", "No identity to authenticate")
            return

        def done(ok):
            self.dialogs.pop(cookie, None)
            if ok:
                invocation.return_value(None)
            else:
                invocation.return_dbus_error("org.freedesktop.PolicyKit1.Error.Cancelled",
                                             "Authentication was cancelled")
        self.dialogs[cookie] = PolkitWindow(self.app, message, ids, cookie, done)
        
def _session_id():
    try:
        subj = Polkit.UnixSession.new_for_process_sync(os.getpid(), None)
        if subj is not None:
            return subj.get_session_id()
    except GLib.Error:
        pass
    return os.environ.get("XDG_SESSION_ID")


def register(app):
    sid = _session_id()
    if not sid:
        print("polkitgtk4: no login session found")
        return None
    try:
        agent = Agent(app)
    except GLib.Error as e:
        print("polkitgtk4: no system bus: {}".format(e.message))
        return None
    subject = ("unix-session", {"session-id": GLib.Variant("s", sid)})
    locale = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "C"
    try:
        agent.bus.call_sync(*AUTHORITY, "RegisterAuthenticationAgent",
                            GLib.Variant("((sa{sv})ss)", (subject, locale, OBJECT_PATH)),
                            None, Gio.DBusCallFlags.NONE, 5000, None)
    except GLib.Error as e:
        print("polkitgtk4: couldn't register: {}".format(e.message))
        return None
    
    return agent

def avatar(size=108, user=None, real_name=None, icon=None):
    own = user is None
    user = user or GLib.get_user_name()
    real_name = real_name or (GLib.get_real_name() if own else "") or user
    paths = [icon] if icon else []
    if own:
        paths.append(os.path.expanduser("~/.face"))
    
    paths.append("/var/lib/AccountsService/icons/{}".format(user))
    for p in paths:
        if os.path.isfile(p):
            av = Adw.Avatar(size=size, show_initials=False)
            try:
                av.set_custom_image(Gdk.Texture.new_from_filename(p))
                return av
            except GLib.Error:
                pass
    return Adw.Avatar(size=size, text=real_name, show_initials=True)

def password_field(placeholder="Enter Password") -> Gtk.PasswordEntry:
    return Gtk.PasswordEntry(placeholder_text=placeholder,
                             halign=Gtk.Align.CENTER, show_peek_icon=False)

def push_button(label: str, on_click=None, style: str = "", **props) -> Gtk.Button:
    b = Gtk.Button(label=label, **props)
    if on_click:
        b.connect("clicked", lambda _b: on_click())
    return b

def popup_button(options, selected: int = 0, on_change=None) -> Gtk.DropDown:
    dd = Gtk.DropDown.new_from_strings(list(options))
    dd.set_selected(selected)
    if on_change:
        dd.connect("notify::selected", lambda d, _p: on_change(d.get_selected()))
    return dd

# def shake(entry: Gtk.Widget) -> None:
    # """Wrong password (macOS): the field shakes, empties and keeps focus."""
    # entry.set_sensitive(True)
    # if hasattr(entry, "set_text"):
        # entry.set_text("")
    # entry.grab_focus()
    # entry.remove_css_class("shake")
    # GLib.idle_add(lambda: (entry.add_css_class("shake"), False)[1])
    # GLib.timeout_add(500, lambda: (entry.remove_css_class("shake"), False)[1])


class PolkitWindow(Gtk.Window):
    def __init__(self, app, message, identities, cookie, done):
        super().__init__()
        self.app, self.cookie, self.done_cb = app, cookie, done
        self.connect("destroy", self.on_close)
        self.set_decorated(False)
        self.set_title("Authenticate")
        self.set_name("polkitgtk4")
        #
        self.identities = list(identities)
        me = GLib.get_user_name()
        names = [_user(i) for i in self.identities]
        self.index = names.index(me) if me in names else 0
        self.session = None
        self.finished = False
        ##
        if IS_WAYLAND:
            GtkLayerShell.init_for_window(self)
            GtkLayerShell.set_namespace(self, "polkitgtk4")
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        #
        self.mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10,
                        halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, width_request=BWIDTH)
        ##  lock image and text and main message
        box_auth = Gtk.Box(spacing=14)
        box_auth.append(Gtk.Image(icon_name="system-lock-screen-symbolic", pixel_size=40, valign=Gtk.Align.START))
        #
        box_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box_text.append(Gtk.Label(label="Authentication Required", xalign=0))
        box_text.append(Gtk.Label(label=message or "An application wants to make changes.", xalign=0, wrap=True,
                               max_width_chars=40))
        box_text.append(Gtk.Label(label="Enter the password to allow this.", xalign=0))
        box_auth.append(box_text)
        self.mainbox.append(box_auth)
        ## user: icon and name
        box_user = Gtk.Box(spacing=10, margin_top=6)
        self.box_user, self.names = box_user, names
        self.face = avatar(28, names[self.index], _real_name(names[self.index]))
        self.box_user.append(self.face)
        if len(names) > 1:
            self.account = popup_button([_real_name(n) for n in names], self.index, self._pick)
            self.account.set_hexpand(True)
            self.box_user.append(self.account)
        else:
            self.box_user.append(Gtk.Label(label=_real_name(names[self.index]), xalign=0, hexpand=True))
        self.mainbox.append(self.box_user)
        ##
        self.entry = password_field("Password")
        self.entry.remove_css_class("lk-field")
        self.entry.set_halign(Gtk.Align.FILL)
        self.entry.connect("activate", lambda *_: self._ok())
        self.mainbox.append(self.entry)
        self.error = Gtk.Label(xalign=0, visible=False, wrap=True)
        self.mainbox.append(self.error)
        ##
        buttons = Gtk.Box(spacing=8, halign=Gtk.Align.END, margin_top=4)
        cancel = push_button("Cancel", lambda: self.finish(False))
        self.ok = push_button("OK", self._ok, "default")
        buttons.append(cancel)
        buttons.append(self.ok)
        self.mainbox.append(buttons)
        ##
        self.set_child(self.mainbox)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", lambda _c, kv, *_: kv == 0xff1b and (self.finish(False), True)[1])
        self.add_controller(keys)
        #
        # signal.signal(signal.SIGINT, self.sigtype_handler)
        # signal.signal(signal.SIGTERM, self.sigtype_handler)
        #
        self.present()
        self.entry.grab_focus()
    
    # def sigtype_handler(self, sig, frame):
        # if sig == signal.SIGINT or sig == signal.SIGTERM:
            # self.on_close()
    
    def on_close(self, w=None):
        quit_()
        self.close()
    
    def _pick(self, i):
        self.index = i
        self._cancel_session()
        face = avatar(28, self.names[i], _real_name(self.names[i]))
        self.box_user.insert_child_after(face, self.face)
        self.box_user.remove(self.face)
        self.face = face

    def _ok(self):
        if not self.entry.get_text():
            return
        self.ok.set_sensitive(False)
        self.entry.set_sensitive(False)
        self.error.set_visible(False)
        self._cancel_session()
        s = self.session = PolkitAgent.Session.new(self.identities[self.index], self.cookie)
        s.connect("request", lambda sess, _prompt, _echo: sess.response(self.entry.get_text()))
        s.connect("show-error", lambda _s, text: self._say(text))
        s.connect("completed", self._completed)
        s.initiate()

    def _completed(self, _s, gained):
        done_session, self.session = self.session, None
        GLib.idle_add(lambda: (done_session and None, False)[1])
        if gained:
            self.finish(True)
            return
        self.ok.set_sensitive(True)
        self.entry.set_sensitive(True)
        self.entry.set_text("")
        self.entry.grab_focus()
        if not self.error.get_visible():
            self._say("Sorry, try again.")
        # shake(self.entry)

    def _say(self, text):
        self.error.set_label(text)
        self.error.set_visible(True)

    def _cancel_session(self):
        if self.session is not None:
            s, self.session = self.session, None
            try:
                s.cancel()
            except GLib.Error:
                pass

    def finish(self, ok: bool) -> None:
        if self.finished:
            return
        self.finished = True
        self._cancel_session()
        self.destroy()
        self.done_cb(ok)

###############
register(None)

loop = GLib.MainContext().default()
while not QUIT:
    loop.iteration(True)

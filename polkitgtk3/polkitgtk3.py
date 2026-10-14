import os,pwd
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gio
gi.require_version("Polkit", "1.0")
gi.require_version("PolkitAgent", "1.0")
from gi.repository import Polkit, PolkitAgent

WWIDTH=600
HHEIGHT=50
INVISIBLE_CHAR="●"


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
    """polkit's D-Bus identity -> the object PolkitAgent.Session wants."""
    # (no id given: skipped -- never a default of 0, which would mean root)
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
    """The agent over polkit's D-Bus interface (plain Gio: the listener
    class's async vfunc can't be implemented safely from Python). polkitd
    calls BeginAuthentication; the method returns once the dialog is done
    (an error when cancelled), and CancelAuthentication closes it."""

    def __init__(self, app):
        self.app = app
        self.dialogs = {}                 # cookie -> AuthDialog
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        # only polkitd may ask for passwords: track its unique bus name
        try:                              # known before any request (the watch reports it later)
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
        if sender is None or sender != self.polkitd:          # anyone else on the bus could fake a prompt
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
        # self.dialogs[cookie] = AuthDialog(self.app, message, ids, cookie, done)
        self.dialogs[cookie] = PolkitWindow(message, ids, cookie, done)
        
    # # test hook: the same entry polkitd uses, without D-Bus
    # def begin(self, message, identities, cookie, done):
        # self.dialogs[cookie] = AuthDialog(self.app, message, identities, cookie,
                                          # lambda ok: (self.dialogs.pop(cookie, None), done(ok)))

def _session_id():
    try:
        subj = Polkit.UnixSession.new_for_process_sync(os.getpid(), None)
        if subj is not None:
            return subj.get_session_id()
    except GLib.Error:
        pass
    return os.environ.get("XDG_SESSION_ID")

def register(app):
    """Register for this login session. Returns the agent (keep it) or None."""
    sid = _session_id()
    if not sid:
        print("Error polkit: no login session found")
        return None
    try:
        agent = Agent(app)
    except GLib.Error as e:
        print("Polkit: no system bus: {}".format(e.message))
        return None
    subject = ("unix-session", {"session-id": GLib.Variant("s", sid)})
    locale = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "C"
    try:
        agent.bus.call_sync(*AUTHORITY, "RegisterAuthenticationAgent",
                            GLib.Variant("((sa{sv})ss)", (subject, locale, OBJECT_PATH)),
                            None, Gio.DBusCallFlags.NONE, 5000, None)
    except GLib.Error as e:
        print("Polkit: couldn't register: {}".format(e.message))
        return None
    
    return agent

def avatar(size=108, user=None, real_name=None, icon=None):
    """`user` None: this process's user. `icon`: a picture file to use first."""
    own = user is None
    user = user or GLib.get_user_name()
    
    real_name = real_name or (GLib.get_real_name() if own else "") or user
    paths = [icon] if icon else []
    if own:
        paths.append(os.path.expanduser("~/.face"))
    
    paths.append("/var/lib/AccountsService/icons/{}".format(user))
    av = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    print("152", paths)
    for p in paths:
        if os.path.isfile(p):
            try:
                _img = Gtk.Image.new_from_file(p)
                av.add(_img)
            except GLib.Error:
                pass
            break
    
    return av
    

class PolkitWindow(Gtk.Window):
    def __init__(self, message, identities, cookie, done):
        Gtk.Window.__init__(self, title="Autentication")
        self.set_decorated(False)
        # self.props.decorated = False
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.connect("destroy", self.on_close)
        #
        self.cookie, self.done_cb = cookie, done
        self.identities = list(identities)
        me = GLib.get_user_name()
        names = [_user(i) for i in self.identities]
        self.index = names.index(me) if me in names else 0
        self.session = None
        self.finished = False
        #
        self.set_default_size(WWIDTH, HHEIGHT)
        self.mainbox = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.mainbox)
        ###### lock image and text
        box_auth = Gtk.Box(spacing=10)
        self.mainbox.add(box_auth)
        box_auth.add(Gtk.Image(icon_name="system-lock-screen-symbolic", pixel_size=40, valign=Gtk.Align.START))
        box_auth.add(Gtk.Label(label="Authentication Required\n", xalign=0))
        ###### main message
        box_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.mainbox.add(box_text)
        box_text.add(Gtk.Label(label=message+"\n" or "An application wants to make changes.\n", xalign=0, wrap=True,
                               max_width_chars=40))
        ###### user: icon and name
        self.box_user = Gtk.Box(spacing=10)#, margin_top=6)
        self.mainbox.add(self.box_user)
        
        # # icon
        # self.face = avatar(28, names[self.index], _real_name(names[self.index]))
        # self.box_user.add(self.face)
        
        # name
        if len(names) > 1:
            self.account = self.popup_button([_real_name(n) for n in names], self.index, self._pick)
            self.account.set_hexpand(True)
            self.box_user.add(self.account)
        else:
            self.box_user.add(Gtk.Label(label=_real_name(names[self.index]), xalign=0, hexpand=True))
        
        ###### password entry
        self.entry = Gtk.Entry(placeholder_text="Enter the password", hexpand=True)
        self.entry.set_invisible_char(INVISIBLE_CHAR)
        self.entry.set_visibility(False)
        self.mainbox.add(self.entry)
        self.entry.connect("activate", lambda *_: self._ok())
        self.entry_bf = self.entry.get_buffer()
        self.entry_bf.connect("inserted-text", self.on_entry_enter)
        ###### error message
        self.error = Gtk.Label(xalign=0, visible=False, wrap=True)
        self.mainbox.add(self.error)
        ######
        box_button = Gtk.Box(spacing=8, halign=Gtk.Align.END, valign=Gtk.Align.END, margin_top=4)
        self.mainbox.add(box_button)
        btn_cancel = Gtk.Button(label="Close")
        box_button.add(btn_cancel)
        btn_cancel.connect("clicked", self.on_close)
        btn_ok = Gtk.Button(label="OK")
        box_button.add(btn_ok)
        btn_ok.connect("clicked", lambda *_: self._ok())
        ##
        self.entry.grab_focus()
        self.show_all()
        self.error.set_visible(False)
        self.resize(WWIDTH, HHEIGHT)
        self.queue_draw()
    
    def on_close(self, w):
        self.close()
    
    def popup_button(self, options, selected: int = 0, on_change=None) -> Gtk.ComboBox:
        dd = Gtk.ComboBoxText()
        for _name in options:
            dd.append_text(_name)
        dd.set_active(selected)
        
        if on_change:
            dd.connect("notify::selected", lambda d, _p: on_change(d.get_selected()))
        return dd
    
    def _pick(self, i):
        return
        # # disabled
        # self.index = i
        # self._cancel_session()
        # # the picture follows the chosen account
        # face = avatar(28, self.names[i], _real_name(self.names[i]))
        # print("286::", face.get_icon_name(), face.get_text(), face.get_size())
        # self.box_user.insert_child_after(face, self.face)
        # self.box_user.remove(self.face)
        # self.face = face
    
    def _ok(self):
        if not self.entry.get_text():
            return
        #
        self.error.set_visible(False)
        self._cancel_session()
        s = self.session = PolkitAgent.Session.new(self.identities[self.index], self.cookie)
        s.connect("request", lambda sess, _prompt, _echo: sess.response(self.entry.get_text()))
        s.connect("show-error", lambda _s, text: self._say(text))
        s.connect("completed", self._completed)
        s.initiate()
    
    def _completed(self, _s, gained):
        # a finished session is only let go (cancelling it again is what crashed)
        done_session, self.session = self.session, None
        GLib.idle_add(lambda: (done_session and None, False)[1])       # dropped after the signal returns
        if gained:
            self.finish(True)
            return
        self.entry.set_text("")
        self.entry.grab_focus()
        if not self.error.get_visible():
            self._say("Sorry, try again.")

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
    
    def on_entry_enter(self, entry_buffer, position, chars, n_chars):
        if self.error.is_visible():
            self.error.set_visible(False)
            self.resize(WWIDTH, HHEIGHT)
            self.queue_draw()
    
###########
register(None)
Gtk.main()
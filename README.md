# miscellaneous-applications
Spare more or less useful applications found or modified or created.

- charactermap (character map): conversion to pyqt6 from the official Qt examples.
- notepad_qt6 (simple text editor): conversion to pyqt6 from the official Qt examples with improvements.
- textedit_qt6 (rich text editor for documents in html format): conversion to pyqt6 from the official Qt examples with many improvements (the images must be located in the folder images where the main html document is located; no other locations are supported)
- qalc_qt6 (basic calculator): conversion to pyqt6 from the official Qt examples with some improvements (decimal notation instead of scientific notation).
- usb_notifications: display a notification after an usb device is been inserted or removed, taking care to show the proper icon and description as much as possible; requirements: python3, pyudev, lsusb, notification server.
- qt6autostart: launch qt6autostart_tui.py to execute all the autostart applications, the system and the user ones; launch qt6autostart_gui.py to manage them; some options in the config file; requires: pyqt6.
- wdesktop: requires gtk4 python binding and wayland; an attempt to build a desktop icons program; implemented: basic file operations (copy/cut/paste; drag and drop; rename; trash; delete), item positioning, rubberband; works in a window.

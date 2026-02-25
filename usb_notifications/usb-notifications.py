from pyudev import Context, Monitor
import subprocess
import notify2
import os, sys, signal


_curr_dir = os.getcwd()

INSERTED = "Inserted"
REMOVED = "Removed"

context = Context()
monitor = Monitor.from_netlink(context)
monitor.filter_by(subsystem='usb')

def find_icon(_vendor, _product):
    comm = "lsusb -d {}:{} -v".format(_vendor,_product)
    _result_tmp = subprocess.run(comm.split(" "), capture_output=True, text=True)
    _result = _result_tmp.stdout.split("\n")
    
    _iProduct = ""
    _idProduct = ""
    _class = ""
    _subclass = ""
    _protocol = ""
    
    for el in _result:
        if "bInterfaceClass" in el:
            _class = el
            break
    for el in _result:
        if "bInterfaceSubClass" in el:
            _subclass = el
            break
    for el in _result:
        if "bInterfaceProtocol" in el:
            _protocol = el
            break
    for el in _result:
        if "idProduct" in el:
            _idProduct = el
            break
            
    if "Human Interface Device" in _class:
        if "keyboard" in _protocol.lower():
            return "input-keyboard"
        elif "mouse" in _protocol.lower():
            return "input-mouse"
        else:
            return "human-interface-device"
    
    if "audio" in _class.lower():
        return "audio-card"
    
    if "communications" in _class.lower():
        if "abstract" in _subclass.lower():
            return "modem"
        elif "ethernet" in _subclass.lower():
            return "network-wired"
    
    if "Mass Storage" in _class:
        return "media-removable"
        
    if "printer" in _class.lower():
        return "printer"
        
    if "video" in _class.lower():
        return "camera-web"
        
    if "wireless" in _class.lower():
        if "bluetooth" in _protocol.lower():
            return "bluetooth"
    
    if "controller" in _subclass.lower():
        return "input-gaming"
    
    else:
        
        for el in _result:
            if "bInterfaceClass" in el:
                if "printer" in el.lower():
                    return "printer"
        
        for el in _result:
            if "iProduct" in el:
                _iProduct = el
                break
            
        if "webcam" in _iProduct.lower() or "camera" in _iProduct.lower():
            return "camera-web"
        
        elif "scanner" in _idProduct.lower():
            return "scanner"
        
        elif "gamepad" in _idProduct.lower():
            return "input-gaming"
        
        else:
            return "device_usb"
    
USB_DATABASE = []

##### at start

for device in context.list_devices(subsystem='usb'):
    if device.device_type == "usb_device":
        if 'ID_USB_VENDOR_ID' in device.properties and 'ID_USB_MODEL_ID' in device.properties \
                and 'ID_USB_MODEL' in device.properties and 'ID_MODEL_FROM_DATABASE' in device.properties:
            _devpath = device.properties['DEVPATH']
            _vendor = device.properties['ID_USB_VENDOR_ID']
            _product = device.properties['ID_USB_MODEL_ID']
            _usb_model = device.properties['ID_USB_MODEL']
            _model_name = device.properties['ID_MODEL_FROM_DATABASE']
            
            _icon = find_icon(_vendor,_product)
            
            USB_DATABASE.append([_devpath, _vendor,_product, _usb_model, _model_name, _icon])

notify2.init("UsbNotifications")

def _send_notification(_msg1, _msg2, _icon):
    _n = notify2.Notification(_msg1,
        _msg2,
        os.path.join(_icon)
        )
    _n.show()

def sigtype_handler(sig, frame):
    if sig == signal.SIGINT or sig == signal.SIGTERM:
        sys.exit(0)
signal.signal(signal.SIGINT, sigtype_handler)
signal.signal(signal.SIGTERM, sigtype_handler)

device = monitor.poll(timeout=None)
while device:
    
    if device.device_type == "usb_device":
        if 'ACTION' in device.properties:
            _action = device.properties['ACTION']
            if _action == "add":
                if 'ID_USB_VENDOR_ID' in device.properties and 'ID_USB_MODEL_ID' in device.properties and 'DEVPATH' in device.properties:
                    _vendor = device.properties['ID_USB_VENDOR_ID']
                    _product = device.properties['ID_USB_MODEL_ID']
                    _devpath = device.properties['DEVPATH']
                    
                    _found = 0
                    if _found == 0:
                        if 'ID_USB_MODEL' in device.properties:
                            _usb_model = device.properties['ID_USB_MODEL']
                        
                        if 'ID_MODEL_FROM_DATABASE' in device.properties:
                            _model_name = device.properties['ID_MODEL_FROM_DATABASE']
                        
                        _icon = find_icon(_vendor,_product)
                        
                        new_device = [_devpath, _vendor,_product, _usb_model, _model_name, _icon]
                        if new_device not in USB_DATABASE:
                            USB_DATABASE.append(new_device)
                        
                        _send_notification(_model_name, INSERTED, os.path.join(_curr_dir, "icons/", _icon+".svg"))
            
            elif _action == "remove":
                if 'DEVPATH' in device.properties:
                    _devpath = device.properties['DEVPATH']
                    _el = None
                    for el in USB_DATABASE[:]:
                        if el[0] == _devpath:
                            _el = el
                            USB_DATABASE.remove(el)
                            
                            _icon = os.path.join(_curr_dir, "icons/", el[5]+".svg")
                            _send_notification(el[4], REMOVED, _icon)
                            
                            break
                    
                    if _el == None:
                        if 'ID_USB_VENDOR_ID' in device.properties and 'ID_USB_MODEL_ID' in device.properties \
                            and 'ID_USB_MODEL' in device.properties:# and 'ID_MODEL_FROM_DATABASE' in device.properties:
                            _vendor = device.properties['ID_USB_VENDOR_ID']
                            _product = device.properties['ID_USB_MODEL_ID']
                            _usb_model = device.properties['ID_USB_MODEL']
                            _icon = "device_usb"
                            _send_notification(_usb_model, REMOVED, os.path.join(_curr_dir, "icons/", _icon+".svg"))
    
    device = monitor.poll(timeout=None)

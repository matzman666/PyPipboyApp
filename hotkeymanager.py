import ctypes
from ctypes import wintypes
import win32con
byref = ctypes.byref
user32 = ctypes.windll.user32

class HotkeyManager():
    HOTKEYS = {}
    # RegisterHotkey is the wrong way to do this as it blocks any registered
    # keys from propagating even if we decide we don't want them
    #
    # Really we want to check if Fallout4 is the active window, and if 
    # not, just let the message pass through. A low level hook via 
    # SetWindowsHookEx is the right way to this, but so far I can't seem 
    # to get it to work with the Qt messageloop...
    
    
    # RegisterHotKey takes:
    #  Window handle for WM_HOTKEY messages (None = this thread)
    #  arbitrary id unique within the thread
    #  modifiers (MOD_SHIFT, MOD_ALT, MOD_CONTROL, MOD_WIN)
    #  VK code (either ord ('x') or one of win32con.VK_*)
    #
    def registerHotkey(self,vk, modifiers, action):
      id = len(self.HOTKEYS)
      #print ("Registering id", id, "for key", vk, "+", modifiers, ":", action)
      if not user32.RegisterHotKey (None, id, modifiers, vk):
         #print ("Unable to register id", id, "(key:", vk , "+", modifiers, ":", action, ")")
         pass
      else:
        self.HOTKEYS[id] = (vk, modifiers, action)

    def unregisterHotkey(self, vk, modifiers):
        for id in self.HOTKEYS.keys ():
            hk = self.HOTKEYS.get (id)
            if (hk[0] == vk and hk[1] == modifiers):
                user32.UnregisterHotKey (None, id)

        
    def unregisterAllHotkeys(self):
        for id in self.HOTKEYS.keys ():
            #print ("unregistering: " + str(self.HOTKEYS.get(id)))
            user32.UnregisterHotKey (None, id)

    def processKeyId(self, id):
        hk = self.HOTKEYS.get (id)
        #print action_to_take
        if hk[2]:
            #hk[2] (hk[0], hk[1])
            hk[2]()
        else:
            #print ("no action?")
            pass
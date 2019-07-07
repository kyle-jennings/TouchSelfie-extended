
# Helper class to launch function after a long-press
class LongPressDetector:
    """Helper class that calls a callback after a long press/click"""
# call_back will get the long_click duration as parameter
    def __init__(self, root, call_back, long_press_duration = 1000 ):
        """Creates the LongPressDetector

        Arguments:
            root (Tk Widget): parent element for the event binding
            call_back       : a callback function with prototype callback(press_duration_ms)
            long_press_duration : amount of milliseconds after which we consider this press is long
        """
        self.ts=0
        self.root = root
        self.call_back = call_back
        self._suspend = False
        self.long_press_duration = long_press_duration
        root.bind("<Button-1>",self.__click)
        root.bind("<ButtonRelease-1>",self.__release)


    def suspend(self):
        """suspend longpress action"""
        self._suspend = True

    def activate(self):
        """reactivate longpress action"""
        self._suspend = False


    def __click(self,event):
        self.ts = event.time

    def __release(self,event):
        if self._suspend:
            #cancel this event
            self.ts = event.time
            return
        duration = event.time - self.ts
        if self.call_back != None and duration > self.long_press_duration:
            self.call_back(duration)

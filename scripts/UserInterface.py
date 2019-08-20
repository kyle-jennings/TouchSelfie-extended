import logging
import tkMessageBox
import time
import traceback
import os
import subprocess
import OAuthServices
from Tkinter import *
from PIL import Image, ImageTk
from mykb import TouchKeyboard
from ImageLabel import ImageLabel
from constants import *
from LongPressDetector import LongPressDetector


log = logging.getLogger(__name__)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.basicConfig(
    format='%(asctime)s|%(name)-16s| %(levelname)-8s| %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='../log',
    filemode='w',
    level = logging.DEBUG
)

try:
    import cups
    import getpass
    printer_selection_enable = True
except ImportError:
    log.warning("Cups not installed. removing option")
    printer_selection_enable = False

try:
    import HardwareButtons as HWB
except ImportError:
    log.error("Error importing hardware_buttons, using fakehardware instead")
    import fakehardware as HWB
    #pass

try:
    import picamera as mycamera
    from picamera.color import Color
except ImportError:
    log.warning("picamera not found, trying cv2_camera")
    try:
        import Camera as mycamera
        from fakehardware import Color
    except ImportError:
        import fakehardware as mycamera
        from fakehardware import Color
        #SystemExit('No camera installed!')


class UserInterface():
    
    """
    Constructor for the UserInterface object

    Arguments:
        config (configuration.Configuration()) : the configuration object
        window_size  tupple(w,h) : the window size (defaults to size in constants.py)
        poll_period : polling period for hardware buttons changes (ms)
        log_level : amount of log (see python module 'logging')
    """
    def __init__(self, config, window_size = None, poll_period = HARDWARE_POLL_PERIOD, log_level = logging.INFO):

        import datetime

        """
        Events to enable/disable cursor based on motion
        on_motion() is called on mouse motion and sets a boolean
        enable_cursor is a fast loop that checks this boolean and enable the cursor
        check_and_disable_cursor is a slow loop that checks this boolean and resets it
        """
        def enable_cursor():
            if self.cursor_motion:
                self.root.config(cursor = "")
            self.enable_cursor_after_id = self.root.after(200, enable_cursor)

        def check_and_disable_cursor():
            if self.cursor_motion == False:
                #remove the cursor,reactivated by motion
                self.root.config(cursor = "none")
            else:
                #erase it
                self.cursor_motion = False
            self.disable_cursor_after_id = self.root.after(3000, check_and_disable_cursor)
        
        def on_motion(event):
            self.cursor_motion = True

        def quit():
            self.log.debug('exiting')
            self.root.destroy();

        #Callback for long-press on screen
        def long_press_cb(time):
            #Create a toplevel window with checkboxes and a "Quit application button"
            top = Toplevel(self.root)
            qb = Button(top,text = "Quit Application", command = self.root.destroy)
            qb.pack(pady = 20)

            mail_enable = IntVar()
            upload_enable = IntVar()
            
            if self.send_emails: mail_enable.set(1)
            else: mail_enable.set(0)
            
            if self.upload_images: upload_enable.set(1)
            else: upload_enable.set(0)

            me = Checkbutton(top, text = "Enable Email sending", variable = mail_enable, anchor = W)
            me.pack(padx = 20,pady = 10,fill = X)
            
            ue = Checkbutton(top, text = "Enable Uploading", variable = upload_enable, anchor = W)
            ue.pack(padx = 20,pady = 10,fill = X)

            def ok():
                enable_email = (mail_enable.get() != 0)
                enable_upload = (upload_enable.get() != 0)
                self.__change_services(enable_email,enable_upload)
                top.destroy()

            b = Button(top, text = "OK", command = ok)
            b.pack(pady = 20)
            self.root.wait_window(top)
        ## End of Auto-hide mouse cursor

        # Factory to launch actions only when no snap is being processed
        def safe_execute_factory(callback):
            def safe_execute(args):
                if not self.suspend_poll == True:
                    callback()
            return safe_execute

        def create_on_screen_buttons():
            import datetime
            self.log.warning("No hardware buttons found, generating on screen buttons")
            self.software_buttons_images = {}

            # decurrying of callback parameter
            def snap_factory(effect):
                def snap_fun():
                    if not self.suspend_poll:
                        self.snap(effect)
                return snap_fun

            def get_button_widths():
                total_width = 0
                for i, effect in enumerate(SOFTWARE_BUTTONS):
                    file    = Image.open(SOFTWARE_BUTTONS[effect]['image'])
                    w, h    = file.size
                    image = ImageTk.PhotoImage(file)
                    self.software_buttons_images[effect] = {}
                    self.software_buttons_images[effect]['image'] = image
                    self.software_buttons_images[effect]['size'] = (w,h)
                    total_width = total_width + w
                return total_width

            def button_factory(padding):
                X_ = 0
                for i, effect in enumerate(SOFTWARE_BUTTONS):
                    w, h  = self.software_buttons_images[effect]['size']
                    Y     = self.size[1] - h
                    image = self.software_buttons_images[effect]['image']
                    btn   = Button(
                        self.root,
                        image = image,
                        width = w,
                        height = h,
                        activebackground = BG_COLOR,
                        activeforeground = BG_COLOR,
                        background = BG_COLOR,
                        borderwidth = 0,
                        highlightbackground = BG_COLOR,
                        highlightcolor = BG_COLOR,
                        highlightthickness = 0,
                        command = snap_factory(effect)
                    )
                    btn.place(x = X_, y = Y)
                    X_ = X_ + w + padding

            #we have the total size, compute padding
            total_width = get_button_widths();
            padding = int((self.size[0] - total_width) / (len(SOFTWARE_BUTTONS) - 1))
            button_factory(padding)

        def make_button(image, callback):
            return Button(
                self.root,
                image = image,
                height = h,
                width = w,
                activebackground = BG_COLOR,
                activeforeground = BG_COLOR,
                background = BG_COLOR,
                borderwidth = 0,
                highlightbackground = BG_COLOR,
                highlightcolor = BG_COLOR,
                highlightthickness = 0,
                command = callback
            )

        self.root                    = Tk()
        self.log                     = logging.getLogger("UserInterface")
        self.log_level               = log_level
        self.cursor_motion           = False
        self.full_screen             = config.full_screen
        self.selected_image_effect   = 'none'
        self.send_prints             = config.enable_print
        self.send_emails             = config.enable_email
        self.image_effects           = config.enable_effects
        self.hardware_buttons        = config.enable_hardware_buttons
        self.quit                    = quit        
        self.enable_cursor_after_id  = self.root.after(100, enable_cursor)
        self.disable_cursor_after_id = self.root.after(2000, check_and_disable_cursor)
        
        self.log.setLevel(self.log_level)
        self.root.bind("<Motion>", on_motion)
        self.root.title('Kat and Kyle 2019')

        self.install_key_binding("snap_single", safe_execute_factory(lambda *args: self.snap("single")))
        self.install_key_binding("snap_collage", safe_execute_factory(lambda *args: self.snap("collage")))
        self.install_key_binding("send_email", safe_execute_factory(lambda *args: self.send_email()))
        self.install_key_binding("send_print", safe_execute_factory(lambda *args: self.send_print()))
        self.install_key_binding("configure", safe_execute_factory(lambda *args: self.long_press_cb(self)))
        self.install_key_binding("quit", safe_execute_factory(lambda *args: self.quit()))
     
        ## Bind keyboard keys to actions
        if self.full_screen:
            global SCREEN_H, SCREEN_W
            SCREEN_W = self.root.winfo_width()
            SCREEN_H = self.root.winfo_height()
            self.root.attributes("-fullscreen", True)
            self.root.update()
            self.size = (SCREEN_W, SCREEN_H)
            window_size = self.size

        self.root.configure(background = BG_COLOR)
        if window_size is not None:
            self.size = window_size
        else:
            self.size = (640,480)
        
        self.root.geometry('%dx%d+0+0'%(self.size[0], self.size[1]))

        #Configure Image holder
        self.image = ImageLabel(self.root, size = self.size)
        self.image.place(x = 0, y = 0, relwidth = 1, relheight = 1)
        self.image.configure(background = BG_COLOR)

        # Create sendprint button
        if self.send_prints:
            print_image = Image.open(PRINT_BUTTON_IMG)
            w,h = print_image.size
            self.print_imagetk = ImageTk.PhotoImage(print_image)
            self.print_btn = make_button(self.print_imagetk, self.send_print)
            # self.print_btn.place( x=2, y=0)
            self.print_btn.configure(background = BG_COLOR)

        # Create sendmail Button
        # if self.send_emails:
        #     mail_image = Image.open(EMAIL_BUTTON_IMG)
        #     w,h = mail_image.size
        #     self.mail_imagetk = ImageTk.PhotoImage(mail_image)
        #     self.mail_btn = self.make_button(self.mail_imagetk, self.send_email)
        #     self.mail_btn.place(x=SCREEN_W-w-2, y=0)
        #     self.mail_btn.configure(background = BG_COLOR)
            
        # Create image_effects button
        # We dont want this right now.
        # if self.image_effects:
        #     effects_image = Image.open(EFFECTS_BUTTON_IMG)
        #     w,h = effects_image.size
        #     self.effects_imagetk = ImageTk.PhotoImage(effects_image)
        #     self.mail_btn = self.make_button(self.effects_imagetk, self.__choose_effect)
        #     self.effects_btn.place(x = SCREEN_W-w-2,y = int((SCREEN_H-h)/2))
        #     self.effects_btn.configure(background = BG_COLOR)
            
        #Create status line
        self.status_lbl = Label(self.root, text="", font=("Helvetica", 20))
        self.status_lbl.config(background = BG_COLOR, foreground=FG_COLOR)
        self.status_lbl.place(x=0 + 10, y=0)

        #State variables
        self.signed_in = False
        self.auth_after_id = None
        self.poll_period = poll_period
        self.poll_after_id = None

        # the last picture taken
        self.last_picture_filename  = None
        self.last_picture_time      = None
        self.last_picture_mime_type = None

        self.tkkb = None
        self.email_addr = StringVar()

        self.suspend_poll = False

        self.config           = config
        self.upload_images    = config.enable_upload
        self.account_email    = config.user_name
        self.send_emails      = config.enable_email
        self.selected_printer = config.selected_printer
        
        # Google credentials
        self.configdir = os.path.expanduser('./')
        self.oauth2service = OAuthServices.OAuthServices(
            os.path.join(self.configdir, APP_ID_FILE),
            os.path.join(self.configdir, CREDENTIALS_STORE_FILE),
            self.account_email,
            enable_email = self.send_emails,
            enable_upload = self.upload_images,
            log_level = self.log_level)

        # Hardware buttons - these would be used to start various picture modes
        if self.hardware_buttons:
            self.buttons = HWB.HardwareButtons( buttons_pins = HARDWARE_BUTTONS['button_pins'], mode = HARDWARE_BUTTONS["pull_up_down"], active_state = HARDWARE_BUTTONS["active_state"])
        else:
            self.buttons = HWB.HardwareButtons( buttons_pins = [], mode="pull_down", active_state=0)

        # creates on screen buttons - these would be used to start various picture modes
        if not self.buttons.has_buttons():
            create_on_screen_buttons()

        # Camera
        self.camera = mycamera.PiCamera()
        self.camera.annotate_text_size = 160 # Maximum size
        self.camera.annotate_foreground = Color(FG_COLOR)
        self.camera.annotate_background = Color(BG_COLOR)
        
        self.long_press_cb = long_press_cb
        self.longpress_obj = LongPressDetector(self.root, long_press_cb)

    """ Destructor """
    def __del__(self):
        try:
            self.root.after_cancel(self.auth_after_id)
            self.root.after_cancel(self.poll_after_id)
            self.camera.close()
        except:
            pass
    
    ## Bind keyboard keys to actions
    def install_key_binding(self, action, function):
        if action in ACTIONS_KEYS_MAPPING.keys():
            for key in ACTIONS_KEYS_MAPPING[action]:
                self.log.debug("Installing keybinding '%s' for action '%s'"%(key,action))
                self.root.bind(key, function)
        else:
            self.log.warning("install_key_binding: no action '%s'"%action)

    """ Update the application status line with status_text """
    def set_status(self, status_text):
        self.status_lbl['text'] = status_text
        self.root.update()

    """ Start the user interface and call Tk::mainloop() """
    def start_ui(self):
        self.auth_after_id = self.root.after(100, self.refresh_auth)
        self.poll_after_id = self.root.after(self.poll_period, self.run_periodically)
        self.root.mainloop()

    """ Hardware poll function launched by start_ui """
    def run_periodically(self):
        import datetime

        if self.last_picture_time is not None:
            if self.last_picture_time < datetime.datetime.now() - datetime.timedelta(seconds = 60):
                self.image.unload()
                self.last_picture_time = None
                self.print_btn.place_forget();

        # self.log.debug(self.image)

        if not self.suspend_poll == True:
            btn_state = self.buttons.state()
            if btn_state == 1:
                self.snap("single")
            elif btn_state == 2:
                self.snap("collage")

        self.poll_after_id = self.root.after(self.poll_period, self.run_periodically)

    """ Take 4 photos and arrange into a collage """
    def collage_snap(self, snap_size, timestamp):
        picture_taken = False
        # collage of four shots
        # compute collage size
        self.log.debug("snap: starting collage of three photos")
        w = snap_size[0]
        h = snap_size[1]
        w_ = w * 2
        h_ = h * 2
        # take 4 photos and merge into one image.
        for i in range(1, 4):
            self.__show_countdown(TIMER, font_size = 80)
            self.camera.capture('collage_' + str(i) + '.jpg')
            try:
                os.system("mpg321 " + MP3S['shutter'])
            except Exception, e:
                self.log.debug(e);
                pass

        # Assemble collage
        self.camera.stop_preview()
        self.set_status("Assembling collage")
        self.log.debug("snap: assembling collage")
        snapshot = Image.new('RGBA', (w_, h_))
        snapshot.paste(Image.open('collage_1.jpg'), (0, 0, w, h))
        snapshot.paste(Image.open('collage_2.jpg'), (w, 0, w_, h))
        snapshot.paste(Image.open('collage_3.jpg'), (0, h, w, h_))
        # snapshot.paste(Image.open('collage_4.jpg'), (w, h, w_, h_))
        picture_taken = True
        
        #paste the collage frame if it exists
        try:
            self.log.debug("snap: Adding the collage cover")
            front = Image.open(MODE_PARAMETERS['collage']['foreground_image'])
            front = front.resize((w_,h_))
            front = front.convert('RGBA')
            snapshot = snapshot.convert('RGBA')
            snapshot = Image.alpha_composite(snapshot, front)

        except Exception, e:
            self.log.error("snap: unable to paste collage cover: %s"%repr(e))

        self.set_status("")
        self.log.debug("snap: Saving collage")
        filename = timestamp + '.jpg'
        snapshot = snapshot.convert('RGB')
        snapshot.save(filename)
        
        return filename, picture_taken

    """ Take a single photo """
    def single_snap(self):

        self.log.debug("snap: single picture")
        self.__show_countdown(TIMER, font_size = 80)
        picture_taken = True        
        filename = self.last_picture_filename;
        # simple shot with logo
        self.camera.capture(filename)
        snapshot = Image.open(filename)
        snapshot.save(filename)
        self.camera.stop_preview()

        try:
            os.system("mpg321 " + MP3S['shutter'])
        except Exception, e:
            self.log.debug(e);
            pass

        return filename, picture_taken

    """ Snap a shot in given mode

        This will start a countdown preview and:
            - take snapshot(s)
            - process them
            - archive them locally
            - upload them to Google Photos

        Arguments:
            mode ("single"|"collage") : the selected mode
    """
    def snap(self, mode = "single"):
        import os
        import datetime

        self.log.info("Snaping photo (mode=%s)" % mode)
        self.suspend_poll = True
        self.set_status("")
        picture_taken = False
        picture_saved = False
        picture_uploaded = False

        if mode not in MODE_PARAMETERS.keys():
            self.log.error("Wrong effectmode %s defaults to 'Single'" % mode)
            mode = "single"

        #hide backgroud image
        self.image.unload()

        # update this to be able to send email and upload
        # snap_filename = snap_picture(mode)
        # take a snapshot here
        snap_filename = None
        snap_size = MODE_PARAMETERS[mode]['snap_size']
        try:

            self.camera.resolution = snap_size
            self.camera.start_preview()

            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d_%H-%M-%S")
            self.last_picture_filename  = timestamp + '.jpg'
            self.last_picture_time      = datetime.datetime.now()
            self.last_picture_title     = timestamp
            self.last_picture_mime_type = 'image/jpg'

            if mode == "single":
                filename, picture_taken = self.single_snap()
            else:
                filename, picture_taken = self.collage_snap(snap_size, timestamp)

            self.log.debug('======================================================')
            self.log.debug('snapshot taken here is the filename:' + filename)
            self.log.debug('======================================================')

            # cancel image_effect (hotfix: effect was not reset to 'none' after each shot)
            self.selected_image_effect = 'none'

            # Here, the photo is in filename
            self.log.info(filename)
            if os.path.exists(filename) & os.path.isfile(filename):
                if self.send_prints:
                    self.print_btn.place(x=4, y=0)
                picture_saved, picture_uploaded = self.save_and_upload(filename, timestamp)   
            else:
                # error
                self.set_status("Snap failed :(")
                self.log.critical("snap: snapshot file doesn't exists: %s"%filename)
                self.image.unload()
        except Exception, e:
            self.log.exception("snap: error during snapshot")
            snapshot = None

        self.suspend_poll = False
        
        #check if a picture was taken and not saved
        if picture_taken and not (picture_saved or picture_uploaded):
            self.log.critical("Error! picture was taken but not saved or uploaded")
            self.set_status("ERROR: Picture was not saved!")
            return None

        return False

    """ Kill the popup keyboard """
    def close_keyboard(self):
        if self.tkkb is not None:
            self.tkkb.destroy()
            self.tkkb = None
            self.suspend_poll = False
        self.root.after(300,self.longpress_obj.activate)

    """ If you have a hardware led on the camera, link it to this """
    def __countdown_set_led(self, state):
        try:
            self.camera.led = state
        except:
            pass

    """ Wrapper function to select between overlay and text countdowns """
    def __show_countdown(self, countdown, font_size = 160):
        # self.__show_text_countdown(countdown,font_size=font_size)
        self.__show_overlay_countdown(countdown)

    """ Display countdown. the camera should have a preview active and the resolution must be set """
    def __show_text_countdown(self, countdown, font_size = 160):
        led_state = False
        self.__countdown_set_led(led_state)

        self.camera.annotate_text = "" # Remove annotation
        self.camera.annotate_text_size = font_size
        self.camera.preview.fullscreen = True

        #Change text every second and blink led
        for i in range(countdown):
            # Annotation text
            self.camera.annotate_text = "  " + str(countdown - i) + "  "
            if i < countdown - 2:
            # slow blink until -2s
                time.sleep(1)
                led_state = not led_state
                self.__countdown_set_led(led_state)
            else:
            # fast blink until the end
                for j in range(5):
                    time.sleep(.2)
                    led_state = not led_state
                    self.__countdown_set_led(led_state)
        self.camera.annotate_text = ""

    """ Display countdown as images overlays """
    def __show_overlay_countdown(self, countdown):
        # COUNTDOWN_OVERLAY_IMAGES
        led_state = False
        self.__countdown_set_led(led_state)

        self.camera.preview.fullscreen = True
        self.camera.preview.hflip = True  #Mirror effect for easier selfies

        """ uses the countdown timer to reverse find the correct timer number image
        this could be simplified if we just reorder the countdown images array
        """
        overlay_images = []
        for i in range(countdown):
            
            image_num = countdown -1 -i #3-1-0 ==> 2; 3-1-1 ==> 1; 3-1-2 ==> 0
            overlay = None
            image = None
            
            if i >= len(COUNTDOWN_OVERLAY_IMAGES):
                break;
            if i >= countdown:
                break;

            image = self.__build_overlay_image(image_num)

            if image == None:
                continue;

            try:
                overlay = self.camera.add_overlay(image.tobytes(), size = image.size)
                overlay.layer = 3
                overlay.alpha = 100

                try:
                    os.system("mpg321 " + MP3S["countdown"])
                except Exception, e:
                    self.log.debug(e);
                    if i <= countdown - 1:
                        time.sleep(1)
                    pass

            except Exception, e:
                self.root.destroy()

            # this timeout is not needed when we used the beeps!

            if overlay != None:
                self.camera.remove_overlay(overlay)

            led_state = False

    """ Builds the overlay image for the countdown """
    def __build_overlay_image(self, i):

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # I'm making the bet that preview window size == screen size in fullscreen mode
        # If this fails we should try preview_width = min(screen_width, self.camera.resolution[0])
        preview_width = screen_width
        preview_height = screen_height

        overlay_height = int(preview_height * COUNTDOWN_IMAGE_MAX_HEIGHT_RATIO)
        
        # read overlay image file
        file = Image.open(COUNTDOWN_OVERLAY_IMAGES[i])
        # resize to 20% of height
        file.thumbnail((preview_width, overlay_height))

        # overlays should be padded to 32 (width) and 16 (height)
        pad_width  = int((preview_width + 31) / 32) * 32
        pad_height = int((preview_height + 15) / 16) * 16

        image = Image.new('RGBA', (pad_width, pad_height))
        # Paste the original image into the padded one (centered)
        image.paste(file, ( int((preview_width - file.size[0]) / 2.0), int((preview_height - file.size[1]) / 2.0)))

        return image;

    """ Save or upload the photo - func comment for consistency """
    def save_and_upload(self, filename, timestamp):
        # import datetime
        picture_saved    = False
        picture_uploaded = False
        self.log.info('saving and uploading')
        self.log.info(filename)
        self.log.info(timestamp)
        # 1. Display
        self.log.debug("snap: displaying image")
        self.image.load(filename)

        # 2. Upload
        if self.signed_in:
            picture_uploaded = self.upload_image_to_google(filename, timestamp)
        else:
            self.log.info('not signed in')

        # 3. Archive
        if config.ARCHIVE:
            picture_saved = self.save_locally(filename)

        return picture_saved, picture_uploaded

    """ Actual code to email picture self.last_picture_filename
    """
    def __send_picture(self):
        
        if not self.send_emails:
            return False
        
        retcode = False
        if self.signed_in:
            self.set_status("Sending Email")
            self.log.debug("send_picture: sending picture by email")
            self.log.debug(self.last_picture_filename)
            try:
                retcode = self.oauth2service.send_message(
                    self.email_addr.get().strip(),
                    config.emailSubject,
                    config.emailMsg,
                    self.last_picture_filename
                )
            except Exception, e:
                self.log.exception('send_picture: Mail sending Failed')
                self.set_status("Send failed :(")
                retcode = False
            else:
                self.set_status("")
        else:
            self.log.error('send_picture: Not signed in')
            retcode = False
        return retcode

    """ Refresh the oauth2 service (regularly called)"""
    def refresh_auth(self):
        # useless if we don't need image upload
        if not (self.upload_images or self.send_emails):
            if self.send_emails:
                self.signed_in = True #Will fail otherwise
                self.mail_btn.configure(state=NORMAL)
            return
        # actual refresh
        if self.oauth2service.refresh():
            # if self.send_emails:
            #     self.mail_btn.configure(state=NORMAL)
            self.signed_in = True
        else:
            # if self.send_emails:
            #     self.mail_btn.configure(state=DISABLED)
            self.signed_in = False
            self.log.error('refresh_auth: refresh failed')

        #relaunch periodically
        self.auth_after_id = self.root.after(OAUTH2_REFRESH_PERIOD, self.refresh_auth)

    """ Uploads the image to google photos """
    def upload_image_to_google(self, filename, title):
        picture_uploaded = False
        self.set_status("Uploading image")
        self.log.debug("Uploading image")
        try:
            caption = config.photoCaption + " " + title
            
            if not self.upload_images:
                return

            if caption is None:
                caption = config.photoCaption
            if config.albumID == 'None':
                config.albumID = None

            self.oauth2service.upload_picture(filename, config.albumID, title, caption)
            self.log.info("Image %s successfully uploaded"%title)
            self.set_status("")

            picture_uploaded = True
        except Exception as e:
            self.set_status("Error uploading image :(")
            self.log.exception("snap: Error uploading image")

        return picture_uploaded

    """ Saves the image to a USB drive if available """
    def save_to_usb(self, filename):
        self.log.info("Archiving to USB keys")
        picture_saved = False
        try:
            usb_mount_point_root = "/media/pi/"
            import os
            root, dirs, files = next(os.walk(usb_mount_point_root))
            
            for directory in dirs:
                mountpoint = os.path.join(root, directory)
            
                if mountpoint.find("SETTINGS") != -1:
                    #don't write into SETTINGS directories
                    continue
                
                if os.access(mountpoint, os.W_OK):
                    #can write in this mountpoint
                    self.log.info("Writing snaphshot to %s" % mountpoint)
            
                    try:
                        dest_dir = os.path.join(mountpoint, "TouchSelfiePhotos")
                        if not os.path.exists(dest_dir):
                            os.makedirs(dest_dir)
                        import shutil
                        shutil.copy(filename, os.path.join(dest_dir, new_filename))
                        picture_saved = True
                    except:
                        self.log.warning("Could not write %s to %s mountpoint" % (new_filename, mountpoint))
                        self.log.exception("Error")
        except:
            self.log.warning("Unable to write %s file to usb key" % (new_filename))
        return picture_saved;

    """ Saves the image to local storage """
    def save_locally(self, filename):
        import os
        self.log.info("Archiving image %s" % filename)
        try:
            if os.path.exists(config.archive_dir):
                # new_filename = "%s-photo.jpg" % filename

                # Try to write the picture we've just taken to ALL plugged-in usb keys
                if config.archive_to_all_usb_drives:
                    self.save_to_usb(filename);

                #Archive on the setup defined directory
                self.log.info("Archiving to local directory %s" % config.archive_dir)
                self.last_picture_filename = new_loc = os.path.join(config.archive_dir, filename)
                picture_saved = True
                os.rename(filename, new_loc)
            else:
                self.log.error("snap: Error : archive_dir %s doesn't exist" % config.archive_dir)
        except Exception as e:
            self.set_status("Saving failed :(")
            self.log.exception("Image %s couldn't be saved" % filename)
            picture_saved = False

        return picture_saved
    
    """ Ask for an email address and send the last picture to it
        This will popup a touch keyboard
    """
    def send_email(self):
        if not self.send_emails:
            return

        if self.signed_in and self.tkkb is None:
            self.email_addr.set("")
            self.suspend_poll = True
            self.longpress_obj.suspend()
            self.tkkb = Toplevel(self.root)
            keyboard_parent = self.tkkb
            consent_var = IntVar()
            
            if self.config.enable_email_logging:
                #build consent control
                main_frame = Frame(self.tkkb)
                consent_frame = Frame(self.tkkb, bg = FG_COLOR, pady = 20)
                consent_var.set(1)
                consent_cb = Checkbutton(
                    consent_frame,
                    text = "Ok to log my mail address",
                    variable = consent_var,
                    font = "Helvetica",bg = FG_COLOR,
                    fg = 'black'
                )
                consent_cb.pack(fill = X)
                consent_frame.pack(side = BOTTOM,fill = X)
                main_frame.pack(side = TOP,fill = Y)
                keyboard_parent = main_frame
                
                def onEnter(*args):
                    filename = self.last_picture_filename
                    self.close_keyboard()
                    res = self.__send_picture()
                    if not res:
                        self.set_status("Error sending email")
                        self.log.error("Error sending email")
                    self.__log_email_address(self.email_addr.get(), consent_var.get()!=0, res, filename)
                
                TouchKeyboard(keyboard_parent, self.email_addr, onEnter = onEnter)
                self.tkkb.wm_attributes("-topmost", 1)
                self.tkkb.transient(self.root)
                self.tkkb.protocol("WM_DELETE_WINDOW", self.close_keyboard)

            else:
                def onEnter(*args):
                    self.close_keyboard()
                    self.__send_picture()

                TouchKeyboard(keyboard_parent,self.email_addr, onEnter = onEnter)
                self.tkkb.wm_attributes("-topmost", 1)
                self.tkkb.transient(self.root)
                self.tkkb.protocol("WM_DELETE_WINDOW", self.close_keyboard)

    """ Send the photo to the printers """
    def send_print(self):
        self.log.info("send_print: Printing image")
        filename = self.last_picture_filename
        title    = self.last_picture_title
        self.log.info(filename)
        self.log.info(title)
        try:
            conn = cups.Connection()
            printers = conn.getPrinters()
            default_printer = printers.keys()[self.selected_printer]#defaults to the first printer installed
            cups.setUser(getpass.getuser())
            conn.printFile(default_printer, filename, title, {'fit-to-page':'True'})
            self.log.info('send_print: Sending to printer...')
        except:
            self.log.exception('print failed')
            self.log.info('print failed')
            self.set_status("Print failed :(")

        self.log.info("send_print: Image printed")

    """ Logs the recipient(?) email address in the sendmail logs """
    def __log_email_address(self, mail_address, consent_to_log, success, last_picture_filename):
        import time
        import datetime
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime("[%Y-%m-%d %H:%M]")
        sendcode = "?"
        if not consent_to_log:
            #user does'nt want his address to be logged
            mail_address = "xxx@xxx"
            if success:
                sendcode = '-'
            else:
                sendcode = "X"
        else:
            if success:
                sendcode = '*'
            else:
                sendcode = 'X'
        file_path = last_picture_filename
        try:
            file_path = os.path.basename(last_picture_filename)
        except:
            pass
        sendmail_log = open(EMAILS_LOG_FILE,"a")
        status = "%s (%s) %s %s\n"%(timestamp, sendcode, mail_address, file_path)
        sendmail_log.write(status)
        sendmail_log.close()

    """ Called whenever we should change the state of OAuthServices """
    def __change_services(self, email, upload):
        self.oauth2service.enable_email = email
        self.oauth2service.enable_upload = upload
        self.send_emails = email
        self.upload_images = upload
        #TODO show/hide button = OAuthServices.OAuthServices(
        if email:
            self.mail_btn.configure(state=NORMAL)
        else:
            self.mail_btn.configure(state=DISABLED)
       
    """ Displays a screen from where user can choose a builtin effect
        This modifies self.selected_image_effect
    """
    def __choose_effect(self):
        self.selected_image_effect = 'none'

        if not self.image_effects: #Shouldn't happen
            return

        #Create a toplevel window to display effects thumbnails
        top = Toplevel(self.root)
        if self.full_screen:
            top.attributes("-fullscreen",True)

        top.geometry('%dx%d+0+0'%(self.size[0],self.size[1]))
        top.configure(background = BG_COLOR)
        
        #layout
        NCOLS = 4
        NROWS = 3       
        window_width = self.size[0]
        window_height = self.size[1]
        
        button_size = min(int(window_width/NCOLS), int(window_height/NROWS))
        button_images = []

        def cb_factory(img_effect):
            def mod_effect():
                self.selected_image_effect = img_effect
                self.log.info("Effect " + str(img_effect) + " selected")
                top.destroy()
            return mod_effect
            
        effect_buttons = []
        for index in range(len(IMAGE_EFFECTS_LIST)):
            effect = IMAGE_EFFECTS_LIST[index]
            params = IMAGE_EFFECTS[effect]
            try:
                button_img = Image.open(params["effect_icon"])
                button_img.thumbnail((button_size,button_size))
                button_img_tk = ImageTk.PhotoImage(button_img)
                button_images.append(button_img_tk)
                button = Button(top, image = button_img_tk, text=effect, height = button_size, width = button_size, background = BG_COLOR, command = cb_factory(effect))
            except:
                self.log.error("Error for effect " + str(effect)+" trying text button")
                button = Button(top, text = effect, background = "#333333",fg = "white",font = 'Helvetica', command = cb_factory(effect))
            row = int(index/NCOLS)
            col = index % NCOLS
            button.grid(row = row + 1, column = col + 1) #+1 -> leave one empty row and one empty column for centering
            effect_buttons.append(button)

        # auto-centering: configure empty border rows/cols with a weight of 1
        top.columnconfigure(0, weight = 1)
        top.columnconfigure(NCOLS + 1, weight = 1)
        top.rowconfigure(0, weight = 1)
        top.rowconfigure(NROWS + 1, weight = 1)
        
        self.root.wait_window(top)

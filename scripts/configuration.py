"""Configuration module to adapt TouchSelfie behavior"""
import json
import os

class Configuration():
    """Configuration class acts as configuration keys/values holder"""
    # default values
    user_name = None
    logo_file = None
    countdown1  = 5 # seconds of preview before first snap
    countdown2  = 3 # seconds of preview between snaps (Four pictures mode)
    photoCaption = "" # Caption in the photo album
    ARCHIVE      = True # Do we archive photos locally
    archive_dir  = os.path.join("..","photos") # Where do we archive photos
    archive_to_all_usb_drives  = False
    albumID      = None #  use install_credentials.py to create 'album.id'
    album_name   = "Wedding"
    emailSubject = "Kat and Kyle 2019 Photobooth!" # subject line of the email sent from the photobooth
    emailMsg     = "Thank you for being part of this celebration!" # Brief body of the message sent from the photobooth
    full_screen  = False #Start application in full screen
    enable_email  = True #Enable the 'send email" feature
    enable_upload = True #Enable the upload feature
    enable_print = False #Enable the printer feature
    enable_effects = False
    selected_printer = None #No printer select
    enable_hardware_buttons = False #Enable hardware buttons
    enable_email_logging = False # Should we log outgoing emails?

    #init
    def __init__(self, configuration_file_name):
        """Creates the configuration object with default values and load the configuration file

        __init__ will parse the configuration file given as its argument
        After parsing, is_valid property is set to True if no error was encountered

        Arguments:
            configuration_file_name -- the conf.json file to read from or write to
        """
        self.config_file = configuration_file_name
        self.is_valid = False
        self.__read_config_file()

    def __read_config_file(self):
        self.is_valid = True
        try:
            with open(self.config_file, 'r') as content_file:
                file_content = content_file.read()
            config = json.loads(file_content)
        except Exception as error:
            print "Error while parsing %s config file : %s"%(self.config_file,error)
            self.is_valid = False
            return False
        
        #mandatory configuration!!
        if "gmail_user" in config.keys(): self.user_name = config['gmail_user']
        else:
            self.is_valid = False


        # all other configuration keys are optional
        if "archive_to_all_usb_drives" in config.keys(): self.archive_to_all_usb_drives = config["archive_to_all_usb_drives"]
        if "countdown_before_snap" in config.keys(): self.countdown2 = config["countdown_before_snap"]
        if "countdown_inter_snap" in config.keys(): self.countdown2 = config["countdown_inter_snap"]
        if "email_body" in config.keys(): self.emailMsg = config["email_body"]
        if "email_subject" in config.keys(): self.emailSubject = config["email_subject"]
        if "enable_effects" in config.keys(): self.enable_effects = config["enable_effects"]
        if "enable_email" in config.keys(): self.enable_email = config["enable_email"]
        if "enable_email_logging" in config.keys(): self.enable_email_logging = config["enable_email_logging"]
        if "enable_hardware_buttons" in config.keys(): self.enable_hardware_buttons = config["enable_hardware_buttons"]
        if "enable_print" in config.keys(): self.enable_print = config["enable_print"]
        if "enable_upload" in config.keys(): self.enable_upload = config["enable_upload"]
        if "full_screen" in config.keys(): self.full_screen = config["full_screen"]
        if "google_photo_album_id" in config.keys(): self.albumID = config["google_photo_album_id"]
        if "google_photo_album_name" in config.keys(): self.album_name = config["google_photo_album_name"]
        if "local_archive" in config.keys(): self.ARCHIVE = config["local_archive"]
        if "local_archive_dir" in config.keys(): self.archive_dir = config["local_archive_dir"]
        if "logo_file" in config.keys(): self.logo_file = config["logo_file"]
        if "selected_printer" in config.keys(): self.selected_printer = config["selected_printer"]
        if "snap_caption" in config.keys(): self.photoCaption = config["snap_caption"]


        return self.is_valid

    def write(self):
        """ write the configuration object to the configuration file given at creation time"""
        myconfig = {
            "archive_to_all_usb_drives" : self.archive_to_all_usb_drives,
            "countdown_before_snap": self.countdown2,
            "countdown_inter_snap": self.countdown2,
            "email_body":self.emailMsg,
            "email_subject": self.emailSubject,
            "enable_effects": self.enable_effects,
            "enable_email": self.enable_email,
            "enable_email_logging" : self.enable_email_logging,
            "enable_hardware_buttons": self.enable_hardware_buttons,
            "enable_print": self.enable_print,
            "enable_upload": self.enable_upload,
            "full_screen": self.full_screen,
            "gmail_user": self.user_name,
            "google_photo_album_id" : self.albumID,
            "google_photo_album_name" : self.album_name,
            "local_archive": self.ARCHIVE,
            "local_archive_dir" : self.archive_dir,
            "logo_file": self.logo_file,
            "selected_printer": self.selected_printer,
            "snap_caption": self.photoCaption,
        }
        try:
            file = os.path.join("..", self.config_file)
            with open(file, 'w') as config:
                config.write(json.dumps(myconfig, indent =4, sort_keys=True))
        except Exception as error:
            raise ValueError("Problem writing %s configuration file: %s"%(self.config_file,error))


if __name__ == "__main__":

    config = Configuration("myconf.conf")
    if not config.is_valid:
        config.write()

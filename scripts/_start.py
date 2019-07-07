from UserInterface import UserInterface
import configuration
import argparse
import logging
from constants import *

if __name__ == '__main__':


    log = logging.getLogger(__name__)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.basicConfig(
        format='%(asctime)s|%(name)-16s| %(levelname)-8s| %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename='touchselfie.log',
        filemode='w',
        level = logging.DEBUG
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("-de", "--disable-email", help="disable the 'send photo by email' feature",
                    action="store_true")
    parser.add_argument("-du", "--disable-upload", help="disable the 'auto-upload to Google Photo' feature",
                    action="store_true")
    parser.add_argument("-df", "--disable-full-screen", help="disable the full-screen mode",
                    action="store_true")
    parser.add_argument("-dh", "--disable-hardware-buttons", help="disable the hardware buttons (on-screen buttons instead)",
                    action="store_true")
    parser.add_argument("--log-level", type=str, choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
                    help="Log level (defaults to WARNING)")
    args = parser.parse_args()
    
    if args.log_level is None:
        args.log_level = "INFO"
        
    #print args
    config = configuration.Configuration("configuration.json")
    if not config.is_valid:
        log.critical("No configuration file found, please run setup.sh script to create one")
        sys.exit()

    # command line arguments have higher precedence than config
    if args.disable_upload and config.enable_upload:
        log.warning("* Command line argument '--disable-upload' takes precedence over configuration")
        config.enable_upload = False

    if args.disable_email and config.enable_email:
        log.warning("* Command line argument '--disable-email' takes precedence over configuration")
        config.enable_email = False

    if args.disable_hardware_buttons and config.enable_hardware_buttons:
        log.warning("* Command line argument '--disable-hardware-buttons' takes precedence over configuration")
        config.enable_hardware_buttons = False

    if args.disable_full_screen and config.full_screen:
        log.warning("* Command line argument '--disable-full-screen' takes precedence over configuration")
        config.full_screen = False

    ch = logging.StreamHandler()
    ch.setLevel(args.log_level)
    ch.setFormatter(logging.Formatter(fmt='%(levelname)-8s|%(asctime)s| %(message)s', datefmt="%H:%M:%S"))
    logging.getLogger("").addHandler(ch)

    #TODO move every arguments into config file
    ui = UserInterface(config,window_size=(SCREEN_W, SCREEN_H),log_level = logging.DEBUG)

    ui.start_ui()

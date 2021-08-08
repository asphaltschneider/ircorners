from pynput import keyboard
import irsdk
import logging
import yaml
import os
import time
from threading import Thread

SCRIPTNAME = "trackbuilder"
CONFIG_FILE = "ircorners.cfg"

class State:
    ir_connected = False
    current_track_id = -1
    current_track_name = ""
    current_corner = ""
    corner_list = []
    all_track_ids = []
    cur_pct = 0
    cur_starts_at = 0
    cur_ends_at = 0
    cur_turn_number = 0
    all_turns_list = []
    info_displayed = 0

# initate everything we need for thread safe logging to stdout
logger = logging.getLogger(SCRIPTNAME)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("---------------------------------------------")
logger.info("%s" % (SCRIPTNAME,))
logger.info("---------------------------------------------")


file_list = os.listdir()
if CONFIG_FILE not in file_list:
    logger.info("There is no ircorners.cfg config file.")
    logger.info("Please copy the ircorners_example.cfg to")
    logger.info("ircorners.cfg and edit it.")
    logger.info("---------------------------------------------")
    input("Press return key to end!")
    exit(0)
else:
    with open(CONFIG_FILE) as fl:
        config = yaml.load(fl, Loader=yaml.FullLoader)

        logger.info("config has been read.")
        logger.info("---------------------------------------------")


def check_iracing():
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset your State variables
        state.last_car_setup_tick = -1
        # we are shutting down ir library (clearing all internal variables)
        ir.shutdown()
        state.info_displayed = 0
        logger.info('iRacing - irsdk disconnected')

    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        state.ir_connected = True
        logger.info('iRacing - irsdk connected')


def iracingworker(stop):
    logger.info("iRacingWorker - Thread starts")

    # looping iracing
    while not stop():
        if not state.ir_connected:
            try:
                ir.startup()
            except Exception as e:
                logger.critical("cannot startup IRSDK: %s" % (e,))
                exit(1)
        try:
            check_iracing()
        except Exception as e:
            logger.critical("iRacingWorker - Exception while checking iracing: %s" % (e,))
        # if we are, then process data
        if state.ir_connected and ir["WeekendInfo"] and ir["SessionInfo"] and ir["DriverInfo"]:
            ir.freeze_var_buffer_latest()
            if ir["WeekendInfo"]["TrackID"] != state.current_track_id:
                state.current_track_id = ir["WeekendInfo"]["TrackID"]
                state.current_track_name = ir["WeekendInfo"]["TrackName"]
                if state.info_displayed == 0:
                    logger.info("TrackID: %s Track: %s" % (state.current_track_id, state.current_track_name, ))
                    state.info_displayed = 1
            #logger.info("TrackID: %s - Corner: '%s' - Dist: %s - Percent: %s" % (ir["WeekendInfo"]["TrackID"], state.current_corner, ir["LapDist"], float(ir["LapDistPct"])))
            state.cur_pct = float(ir["LapDistPct"])
            found = 0
            #print(state.corner_list)
            for i in state.corner_list:
                #logger.info("%s -> %s" % (float(i["starts_at"]), float(i["ends_at"])))
                if float(ir["LapDistPct"]) >= float(i["starts_at"]) and float(ir["LapDistPct"]) < float(i["ends_at"]):
                    #logger.info("match.... %s" % (i["name"], ))
                    state.current_corner = i["name"]
                    found = 1
            if found == 0:
                state.current_corner = ""
            time.sleep(10/60)
    logger.info("iRacingWorker - Thread ends")


def on_press(key):
    if key == keyboard.Key.esc:
        return False  # stop listener
    try:
        k = key.char  # single-char keys
    except:
        k = key.name  # other keys

    if k in ['1', '2', '3']:  # keys of interest
        # self.keys.append(k)  # store it in global-like variable
        #print('Key pressed: %s at %s' % (k, state.cur_pct))

        if k == '1':
            state.cur_starts_at = state.cur_pct
            state.cur_turn_number += 1
        if k == '2':
            state.cur_ends_at = state.cur_pct
            state.all_turns_list.append('    <turn number="%s" starts_at="%s" ends_at="%s" name=""/>' % (state.cur_turn_number, state.cur_starts_at, state.cur_ends_at))
            #print('    <turn number="%s" starts_at="%s" ends_at="%s" name=""/>' % (state.cur_turn_number, state.cur_starts_at, state.cur_ends_at))
        if k == '3':
            print('<?xml version="1.0" encoding="UTF-8" ?>')
            print('<!-- %s - %s -->' % (state.current_track_name, state.current_track_id))
            print('<track>')
            for i in state.all_turns_list:
                print(i)
            print('</track>')
            state.cur_turn_number = 0
        #return False  # stop listener; remove this if want more keys

if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press)
    # initialize our State class
    state = State()
    # initialize IRSDK
    try:
        ir = irsdk.IRSDK(parse_yaml_async=True)
        logger.info("startup iRacing SDK")
    except Exception as e:
        logger.critical("cannot initialize IRSDK: %s" % (e,))

    stop_threads = False

    iRacingThread = Thread(target=iracingworker, args=(lambda: stop_threads, ))
    #webserverThread = Thread(target=startWebServer)
    #xmlReaderThread = Thread(target=xmlreaderworker, args=(lambda: stop_threads, ))

    iRacingThread.start()
    #webserverThread.start()
    #xmlReaderThread.start()
    listener.start()  # start to listen on a separate thread

    input("any key to end\n")
    stop_threads = True

    iRacingThread.join()
    #webserverThread.join()
    #xmlReaderThread.join()
    listener.join()  # remove if main thread is polling self.keys

    logger.info("iRcorner - Programm finished....")



import irsdk
import logging
import yaml
import os
import time
from threading import Thread
from flask import Flask, render_template, jsonify
import untangle


SCRIPTNAME = "iRcorners"
CONFIG_FILE = "ircorners.cfg"

app = Flask(__name__)


class State:
    ir_connected = False
    current_track_id = -1
    current_track_name = ""
    current_track_layout = ""
    current_corner = ""
    corner_list = []
    all_track_ids = []



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
            logger.info("TrackID: %s - Corner: '%s' - Dist: %s - Percent: %s" % (ir["WeekendInfo"]["TrackID"], state.current_corner, ir["LapDist"], float(ir["LapDistPct"])))
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


def startWebServer():
    logger.info("WebServerWorker - Thread starts")
    logger.info("WebServerWorker - Bind to IP: %s and Port: %s" % (config["HTTP_IP"], config["HTTP_PORT"], ))
    app.run(host=config["HTTP_IP"], port=config["HTTP_PORT"])
    logger.info("WebServerWorker - Thread ends")


def webserverworker(stop):
    logger.info("WebServerWorker - Thread starts")
    logger.info("WebServerWorker - Bind to IP: %s and Port: %s" % (config["HTTP_IP"], config["HTTP_PORT"], ))
    if config["HTTP_ENABLED"] == True:
        while not stop():
            logger.info("WebServerWorker - still running....")
            time.sleep(10)
    else:
        logger.info("WebServerWorker - configured to be disabled. Finish Thread...")
    logger.info("WebServerWorker - Thread ends")

def xmlreaderworker(stop):
    logger.info("XMLReaderThread - Thread starts")
    logger.info("XMLReaderThread - Reading all_tracks.xml")
    all_tracks = untangle.parse('ressources/all_tracks.xml')
    # print(all_tracks.all_tracks.track)
    all_track_ids = []
    for i in all_tracks.all_tracks.track:
        all_track_ids.append(int(i["id"]))
        logger.info("id: %s name: %s layout: %s" % (i["id"], i["name"], i["layout"], ))
    state.all_track_ids = all_track_ids
    lasttrackid = state.current_track_id
    while not stop():
        if state.current_track_id != lasttrackid:
            logger.info("XMLReaderThread - The trackID changed. Is there a XML for trackID %s ?" % (state.current_track_id, ))
            if state.current_track_id in all_track_ids:
                logger.info("XMLReaderThread - Yes! ID %s is supported. Loading the XML..." % (state.current_track_id))
                filename = str(state.current_track_id) + ".xml"
                print("XML: %s" % (filename,))
                current_track = untangle.parse('ressources/' + filename)
                print(current_track.track.turn)
                turn_dict = {}
                turn_list =[]
                for i in current_track.track.turn:
                    print(i)
                    turn_dict['starts_at'] = i['starts_at']
                    turn_dict['ends_at'] = i['ends_at']
                    turn_dict['name'] = i['name']
                    turn_list.append(turn_dict)
                    turn_dict = {}
                state.corner_list = turn_list


            else:
                logger.info("XMLReaderThread - No! ID %s is not yet supported." % (state.current_track_id))
        lasttrackid = int(state.current_track_id)
        logger.info("XMLReaderThread - still running....")
        time.sleep(10)

    logger.info("XMLReaderThread - Thread ends")

@app.route( "/" )
def index():
    return render_template( "index.html" )

@app.route( "/ircorners" )
def ircorners():
    return jsonify( {"turnname": state.current_corner} )


if __name__ == "__main__":
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
    webserverThread = Thread(target=startWebServer)
    #Thread(target=webserverworker, args=(lambda: stop_threads, ))
    xmlReaderThread = Thread(target=xmlreaderworker, args=(lambda: stop_threads, ))

    iRacingThread.start()
    webserverThread.start()
    xmlReaderThread.start()

    input("any key to end\n")
    stop_threads = True

    iRacingThread.join()
    webserverThread.join()
    xmlReaderThread.join()

    logger.info("iRcorner - Programm finished....")

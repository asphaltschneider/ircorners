import irsdk
import logging

SCRIPTNAME = "iRcorners"

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
ir = irsdk.IRSDK(parse_yaml_async=True)
logger.info("startup iRacing SDK")
ir.startup()
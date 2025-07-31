import ismrmrd
import os
import logging
import traceback
import mrdhelper
import constants

# ------------------------------------------------------------------------
#   Purpose: This script just dumps all header data from
#   images 
#
#   Script also logs to logging.info (.utr file) to analyse input order
#   and directly compare with other logging processes.
#
#   TODO: Handle k-space/acquisition 
#   TODO: Make YAML in neurocontainer builder
#   
# ------------------------------------------------------------------------


def process(connection, config, mrdHeader):
    try:
        logging.info("MANUAL_LOG: Incoming dataset contains %d encodings", len(mrdHeader.encoding))
        logging.info("MANUAL_LOG: First encoding is the following:\n%s", mrdHeader.encoding[0])
        try:
            logging.info("MANUAL_LOG: First full mrdHeader is the following:\n%s",mrdHeader[0])
            logging.info("MANUAL_LOG: First full Config:\n%s",config[0])
        except:
            logging.info("MANUAL_LOG: First full mrdHeader failed. logging mrdHeader:\n%s",mrdHeader)
            logging.info("MANUAL_LOG_ERROR: First full config failed logging config:\n%s",config)
    except:
        logging.info("MANUAL_LOG: Improperly formatted metadata: \n%s",mrdHeader)
    try:
        for item in connection:
            
            # ----------------------------------------------------------
            # Raw k-space data messages
            # ----------------------------------------------------------
            if isinstance(item, ismrmrd.Acquisition):
                logging.info("MANUAL_LOG: Raw k-space data recieved, logging AcquisitionHeader:\n%s",item.AcquisitionHeader())
                try:
                    logging.info("MANUAL_LOG_TESTING: Logging AcquisitionHeader via item.getHead():\n%s",item.getHead())
                except:
                    logging.info("MANUAL_LOG_TESTING-FAILED: Could not log AcquisitionHeader:\n%s",item.AcquisitionHeader())
                raise Exception("MANUAL_LOG: Raw k-space data is not supported by this module")
            # ----------------------------------------------------------
            # Image data messages
            # ----------------------------------------------------------
            elif isinstance(item, ismrmrd.Image):
                logging.info("MANUAL_LOG: Image data recieved, logging ImageHeader:\n%s",item.ImageHeader())
                logging.info("MANUAL_LOG: Processing a group of images because series index changed to %d", item.image_series_index)# If no **A then no this
                try:
                    logging.info("MANUAL_LOG_TESTING: item.image_series_index:%s,item.imtype:%s,item.phase:%s,item.repetition:%s",item.image_series_index,item.image_type,item.phase,item.repetition)
                except:
                    logging.info("MANUAL_LOG_TESTING: item.image_series_index, item.phase and item.repetition failed.")
                tmpMeta = ismrmrd.Meta.deserialize(item.attribute_string)
                tmpMeta['Keep_image_geometry']    = 1
                item.attribute_string = tmpMeta.serialize()
                connection.send_image(item)
                continue

            elif item is None:
                break
            else:
                raise Exception("MANUAL_LOG: Unsupported data type %s", type(item).__name__)

    except Exception as e:
        logging.error("MANUAL_ERROR: "+traceback.format_exc())
        connection.send_logging(constants.MRD_LOGGING_ERROR, traceback.format_exc())

        # Close connection without sending MRD_MESSAGE_CLOSE message to signal failure
        connection.shutdown_close()
    finally:
        try:
            connection.send_close()
        except:
            logging.error("MANUAL_LOG: Failed to send close message!")
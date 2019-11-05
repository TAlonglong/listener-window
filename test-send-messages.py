#!/usr/bin/env python

import sys
import os
import os.path
import datetime as dt
import time

from posttroll.publisher import NoisyPublisher
from posttroll.message import Message
from trollsift import parse

def send_message(topic, info, message_type):
    '''Send message with the given topic and info'''
    pub_ = NoisyPublisher("dummy_sender", 0, topic, nameservers=['localhost'])
    pub = pub_.start()
    time.sleep(2)
    msg = Message(topic, message_type, info)
    print("Sending message: %s" % str(msg))
    for x in range(10):
        pub.send(str(msg))
    pub_.stop()

def main():
    '''Main.'''

    message_type = 'collection' 
    topic = "/SATPROC3/GATHERED/OLCI/1B"

    info_dicts = [{"origin": "157.249.16.182:9218", "stream": "eumetcast", "centre": "MAR", "tle_platform_name": "SENTINEL 3A", "frame": 1260, "relative_orbit": 163, "creation_time": "2018-05-16T09:49:37", "collection": [{"uid": "S3A_OL_1_EFR____20180516T065834_20180516T070121_20180516T094937_0167_031_163_1260_MAR_O_NR_002.SEN3.tar", "start_time": "2018-05-16T06:58:34", "end_time": "2018-05-16T07:01:21", "uri": "/data/pytroll/olci/S3A_OL_1_EFR____20180516T065834_20180516T070121_20180516T094937_0167_031_163_1260_MAR_O_NR_002.SEN3.tar"}], "datatype_id": "EFR", "duration": 167, "cycle": 31, "sensor": "olci", "timeliness": "NR", "collection_area_id": "ears_high_res", "orbit_number": 11686, "platform_name": "Sentinel-3A", "mode": "O", "pass_key": "", "data_processing_level": "1B", "start_time": "2018-05-16T06:58:34", "end_time": "2018-05-16T07:01:21"},]
    
    for info_dict in info_dicts:
        send_message(topic, info_dict, message_type)

if __name__ == "__main__":
    main()

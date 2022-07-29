#!/usr/bin/python
#
# In order for pyaudio to work (as used by AudioCapture/etc), you need to install it
# You can do this for ubuntu as
# sudo apt install python3-pyaudio
# 
# This also requires portaudio19 to be installed, or else you get some very cryptic messages:
#
# sudo apt-get install portaudio19-dev

import time

from guild.av import WebCamTest, SomeDisplay, AudioCapture, WaveWriter
from guild.actor import *

wct = WebCamTest()
d = SomeDisplay()
ac = AudioCapture()
ww = WaveWriter()

pipe(wct, "produce", d, "show")
pipe(ac, "output", ww, "record")

start(wct, d, ac, ww)

time.sleep(6)

stop(wct, d, ac, ww)
wait_for(wct, d, ac, ww)

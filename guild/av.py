#!usr/bin/python

from __future__ import print_function

import os
import time
import wave
import sys
import pprint

import pyaudio
import pygame
import pygame.camera

from guild.actor import *

pygame.init()
pygame.camera.init()

modes = {
          "240p": (),
          "480p": (),
          "720p": ()
        }

vidsize = (320, 240)

# Global. Undecided if this is a good or bad thing.
# Currently that's the way it is.
p = pyaudio.PyAudio()


class AudioCapture(Actor):
    def main(self):
        global p
        yield 1
        CHUNK = 2048
        FORMAT = pyaudio.paInt16
        RECORD_SECONDS = 5
        RATE = 44100
        CHANNELS = 1

        device_count = p.get_device_count()

        devices = {}

        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            devices[info["name"]] = info

        #pprint.pprint(devices)

        #device_names = [x for x in devices.keys() if (("USB" in x) and ("0x46d:0x825" in x))]

        #device = devices[device_names[0]]

#        RATE = int(device.get("defaultSampleRate", 44100))
#        CHANNELS = int(device.get("maxInputChannels", 2))
#        DEVICE_INDEX = int(device.get("index", 0))

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
#                        input_device_index=DEVICE_INDEX,
                        frames_per_buffer=CHUNK)

        print("* recording")

        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            self.output(data, time.time())
            yield 1

        self.output(None, 0)
        print("* done recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

    @late_bind
    def output(self, frame, timestamp):
        pass


class WaveWriter(Actor):
    def __init__(self):
        self.frames = []
        self.CHANNELS = 1
        self.FORMAT = pyaudio.paInt16
        self.WAVE_OUTPUT_FILENAME = "output.wav"
        self.RATE = 44100

        super(WaveWriter, self).__init__()

    @actor_method
    def record(self, audio, timestamp):
        global p

        if audio != None:
            self.frames.append(audio)
        else:
            wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            self.stop()


class WebCamTest(Actor):
    def main(self):
        device = "/dev/video0"

        capturesize = vidsize
        camera = pygame.camera.Camera(device, capturesize)
        camera.start()
        count = 0
        ts = time.time()
        print("START")
        while True:
            time.sleep(0.02)
            yield 1
            count += 1
            snapshot = camera.get_image()
            now = time.time()
            try:
                self.produce(snapshot, now)
            except:
                pass
            if count > 30:
                print(ts, time.time(), "Count", count, end="")
                dur = time.time() - ts
                if dur > 0:
                    print("RATE: ", count / (time.time() - ts))
                count = 0
                ts = time.time()

    @late_bind
    def produce(self, image, timestamp):
        pass


class SomeDisplay(Actor):
    def __init__(self):
        super(SomeDisplay, self).__init__()
        displaysize = vidsize
        self.display = pygame.display.set_mode(displaysize)
        self.frames = []

    @actor_method
    def show(self, image, timestamp):
        # pass
        self.frames.append((image, timestamp))
        self.display.blit(image, (0, 0))
        pygame.display.flip()

    def onStop(self):
        if len(self.frames) > 0:
            for image, timestamp in self.frames:
                pygame.image.save(image, "snaps/" + str(timestamp) + ".png")


if __name__ == "__main__":
    if False:
        wct = WebCamTest()
        d = SomeDisplay()

        wct.bind("produce", d, "show")

        d.start()
        wct.start()
        time.sleep(1)

        wct.join()
        d.join()

    if False:
        ac = AudioCapture()
        ww = WaveWriter()
        ac.bind("output", ww, "record")
        ww.start()
        ac.start()
        ac.join()
        ww.join()

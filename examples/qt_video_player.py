#!/usr/bin/python

"""Example of a guild - Qt hybrid system.

This example shows three ways to connect guild pipelines to Qt
objects. Version 1 (preferred) uses a normal guild pipeline with a
hybrid (guild/Qt) display object. Version 2 uses a hybrid source and a
standard Qt display, which is what you'd do if you don't want to
modify your Qt component. Version 3 introduces a hybrid "bridge"
between a guild source and a Qt display - useful if you don't want to
modify either.

"""

from __future__ import print_function

import re
import subprocess
import sys
import time

from guild.actor import *
from guild.qtactor import ActorSignal, QtActorMixin
from PyQt5 import QtGui, QtCore, QtWidgets

def VideoFileReader(file_name):
    # get video dims
    proc_pipe = subprocess.Popen([
        'ffmpeg', '-loglevel', 'info', '-i', file_name,
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
    stdout, stderr = proc_pipe.communicate()
    pattern = re.compile('Stream.*Video.* ([0-9]{2,})x([0-9]+)')
    for line in str(stderr).split('\n'):
        match = pattern.search(line)
        if match:
            xlen, ylen = map(int, match.groups())
            break
    else:
        print('Could not get video dimensions of', file_name)
        return
    try:
        bytes_per_frame = xlen * ylen * 3
        proc_pipe = subprocess.Popen([
            'ffmpeg', '-loglevel', 'warning', '-i', file_name,
            '-f', 'image2pipe', '-pix_fmt', 'rgb24', '-vcodec', 'rawvideo', '-'
            ], stdout=subprocess.PIPE, bufsize=bytes_per_frame)
        while True:
            raw_image = proc_pipe.stdout.read(bytes_per_frame)
            if len(raw_image) < bytes_per_frame:
                break
            yield xlen, ylen, raw_image
    finally:
        proc_pipe.terminate()
        proc_pipe.stdout.close()

class Player(Actor):
    def __init__(self, video_file):
        self.video_file = video_file
        self.paused = False
        super(Player, self).__init__()

    def main(self):
        self.reader = VideoFileReader(self.video_file)
        raw_image = None
        while True:
            yield 1
            if not (self.paused and raw_image):
                try:
                    xlen, ylen, raw_image = next(self.reader)
                except StopIteration:
                    break
            image = QtGui.QImage(
                raw_image, xlen, ylen, QtGui.QImage.Format_RGB888)
            self.output(image)
            time.sleep(1.0/25)

    @actor_method
    def set_paused(self, paused):
        self.paused = paused

    def onStop(self):
        self.reader.close()

class PlayerQt(QtActorMixin, QtCore.QObject):
    signal = QtCore.pyqtSignal(QtGui.QImage)

    def __init__(self, video_file):
        self.video_file = video_file
        self.paused = False
        super(PlayerQt, self).__init__()

    def main(self):
        self.reader = VideoFileReader(self.video_file)
        raw_image = None
        while True:
            yield 1
            if not (self.paused and raw_image):
                try:
                    xlen, ylen, raw_image = next(self.reader)
                except StopIteration:
                    break
            image = QtGui.QImage(
                raw_image, xlen, ylen, QtGui.QImage.Format_RGB888)
            self.signal.emit(image)
            time.sleep(1.0/25)

    @actor_method
    @QtCore.pyqtSlot(bool)
    def set_paused(self, paused):
        self.paused = paused

    def onStop(self):
        self.reader.close()

class Display(QtWidgets.QLabel):
    @QtCore.pyqtSlot(QtGui.QImage)
    def show_frame(self, frame):
        pixmap = QtGui.QPixmap.fromImage(frame)
        self.setPixmap(pixmap)

class DisplayActor(QtActorMixin, QtWidgets.QLabel):
    @actor_method
    def show_frame(self, frame):
        pixmap = QtGui.QPixmap.fromImage(frame)
        self.setPixmap(pixmap)

    input = show_frame

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, video_file):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Guild video player")
        # create guild pipeline
        # version 1: guild player -> hybrid display
        self.player = Player(video_file).go()
        display = DisplayActor().go()
        pipeline(self.player, display)
        self.actors = [self.player, display]

        # version 2: hybrid player -> Qt display
##        self.player = PlayerQt(video_file).go()
##        display = Display()
##        self.player.signal.connect(display.show_frame)
##        self.actors = [self.player]

        # version 3: guild player -> hybrid bridge -> Qt display
##        self.player = Player(video_file).go()
##        bridge = ActorSignal().go()
##        display = Display()
##        pipeline(self.player, bridge)
##        bridge.signal.connect(display.show_frame)
##        self.actors = [self.player, bridge]

        # central widget
        widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(4, 1)
        widget.setLayout(grid)
        self.setCentralWidget(widget)
        grid.addWidget(display, 0, 0, 1, 6)
        # pause button
        pause_button = QtWidgets.QCheckBox('pause')
        pause_button.clicked.connect(self.player.set_paused)
        pause_button.setShortcut('Space')
        grid.addWidget(pause_button, 1, 0)
        # quit button
        quit_button = QtWidgets.QPushButton('quit')
        quit_button.clicked.connect(self.shutdown)
        quit_button.setShortcut('Ctrl+Q')
        grid.addWidget(quit_button, 1, 5)
        self.show()

    def shutdown(self):
        stop(*self.actors)
        wait_for(*self.actors)
        QtWidgets.QApplication.instance().quit()

if len(sys.argv) != 2:
    print('usage: %s video_file' % sys.argv[0])
    sys.exit(1)
app = QtWidgets.QApplication([])
main = MainWindow(sys.argv[1])
app.exec_()

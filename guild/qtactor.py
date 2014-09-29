"""Integrate guild with Qt.

The QtActorMixin mixin class allows you to add actor functionality to
any PyQt class. Your class runs in a Qt thread, unless it is a QWidget
(or derived from QWidget) in which case it runs in the main Qt thread.
Queued method invocations (@actor_method, @actor_function) are handled
as Qt events.

The ActorSignal class implements a simple bridge between guild and
PyQt. Any object received by its guild input is emitted on its Qt
signal. This allows guild and Qt components to be connected without
modifying either.

Qt signals can be connected directly to guild components' actor
methods. Their queued invocation allows them to be called safely from
a Qt thread.

"""

import socket
import threading

from PyQt4 import QtCore, QtGui

from actor import ActorMixin, ActorMetaclass, actor_method

class _QtActorMixinMetaclass(QtCore.pyqtWrapperType, ActorMetaclass):
    pass


class QtActorMixin(ActorMixin):
    __metaclass__ = _QtActorMixinMetaclass

    def __init__(self, *argv, **argd):
        super(QtActorMixin, self).__init__(*argv, **argd)
        # set up QSocketNotifier to handle queued method notifications
        self._qtactor_rsock, self._qtactor_wsock = socket.socketpair()
        self._qtactor_notifier = QtCore.QSocketNotifier(
            self._qtactor_rsock.fileno(), QtCore.QSocketNotifier.Read)
        self._qtactor_notifier.activated.connect(self._qtactor_do_queued)
        # signal to tell loop to exit
        self._qtactor_kill = threading.Event()
        self._qtactor_stopped = threading.Event()
        self._qtactor_stopped.set()
        # if not a Widget, move to a Qt thread
        if isinstance(self, QtGui.QWidget):
            # widgets can't be moved to another thread
            self._qtactor_thread = None
        else:
            # create a thread and move to it
            self._qtactor_thread = QtCore.QThread()
            self.moveToThread(self._qtactor_thread)
            self._qtactor_thread.started.connect(self._qtactor_run)

    def _actor_notify(self):
        # run from any thread that needs to wake up our thread
        self._qtactor_wsock.send('1')

    def _qtactor_do_queued(self):
        # runs in Qt thread after it's been woken up by QSocketNotifier
        self._qtactor_rsock.recv(1)
        self._actor_do_queued()

    def start(self):
        if self._qtactor_thread:
            self._qtactor_thread.start()
        else:
            self._qtactor_run()

    def _qtactor_run(self):
        # get main process generator
        self._qtactor_main_gen = self._qtactor_main()
        if self._qtactor_thread:
            # run generator continuously
            while True:
                try:
                    self._qtactor_main_gen.next()
                except StopIteration:
                    break
                QtCore.QCoreApplication.processEvents()
        else:
            # use a timer to run generator in the background
            self._qtactor_timer = QtCore.QTimer()
            self._qtactor_timer.timeout.connect(self._qtactor_step)
            self._qtactor_timer.start()

    def _qtactor_step(self):
        try:
            self._qtactor_main_gen.next()
        except StopIteration:
            self._qtactor_timer.stop()

    def _qtactor_main(self):
        self._qtactor_stopped.clear()
        self.process_start()
        self.process()
        try:
            for i in self.gen_process():
                if self._qtactor_kill.is_set():
                    self.onStop()
                    break
                yield 1
        except AttributeError:
            pass
        self._qtactor_stopped.set()

    def stop(self):
        self._qtactor_kill.set()
        self._qtactor_stopped.wait()
        if self._qtactor_thread:
            self._qtactor_thread.quit()

    def join(self):
        if self._qtactor_thread:
            self._qtactor_thread.wait()


class ActorSignal(QtActorMixin, QtCore.QObject):
    signal = QtCore.pyqtSignal(object)

    @actor_method
    def input(self, msg):
        self.signal.emit(msg)

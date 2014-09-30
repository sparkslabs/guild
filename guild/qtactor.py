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
import sys

from PyQt4 import QtCore, QtGui

from actor import ActorMixin, ActorMetaclass, actor_method

class _QtActorMixinMetaclass(QtCore.pyqtWrapperType, ActorMetaclass):
    pass


class QtActorMixin(ActorMixin):
    __metaclass__ = _QtActorMixinMetaclass
    # create unique event types
    _qtactor_step_event = QtCore.QEvent.registerEventType()
    _qtactor_stop_event = QtCore.QEvent.registerEventType()

    def __init__(self, *argv, **argd):
        super(QtActorMixin, self).__init__(*argv, **argd)
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
        # do first step
        self._qtactor_step()
        # set up QSocketNotifier to handle queued method notifications
        self._qtactor_rsock, self._qtactor_wsock = socket.socketpair()
        self._qtactor_notifier = QtCore.QSocketNotifier(
            self._qtactor_rsock.fileno(), QtCore.QSocketNotifier.Read)
        self._qtactor_notifier.activated.connect(self._qtactor_do_queued)

    def event(self, event):
        if event.type() == self._qtactor_step_event:
            event.accept()
            self._qtactor_step()
            return True
        if event.type() == self._qtactor_stop_event:
            event.accept()
            self._qtactor_stop()
            return True
        return super(QtActorMixin, self).event(event)

    def _qtactor_step(self):
        try:
            self._qtactor_main_gen.next()
        except StopIteration:
            self._qtactor_main_gen = None
            return
        # trigger next iteration, at lower priority than other Qt events
        QtCore.QCoreApplication.postEvent(
            self, QtCore.QEvent(self._qtactor_step_event), -sys.maxint)

    def _qtactor_main(self):
        self.process_start()
        self.process()
        try:
            for i in self.gen_process():
                yield 1
        except AttributeError:
            pass

    def _qtactor_stop(self):
        if self._qtactor_main_gen:
            self._qtactor_main_gen.close()
            self._qtactor_main_gen = None
            self.onStop()
        if self._qtactor_thread:
            self._qtactor_thread.quit()

    def stop(self):
        QtCore.QCoreApplication.postEvent(
            self, QtCore.QEvent(self._qtactor_stop_event))

    def join(self):
        if self._qtactor_thread:
            self._qtactor_thread.wait()


class ActorSignal(QtActorMixin, QtCore.QObject):
    signal = QtCore.pyqtSignal(object)

    @actor_method
    def input(self, msg):
        self.signal.emit(msg)

import socket
import threading

from PyQt4 import QtCore, QtGui

from actor import ActorMixin, ActorMetaclass

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
        self._qtactor_running = threading.Event()
        self._qtactor_running.set()
        # if not a Widget, move to a Qt thread
        if isinstance(self, QtGui.QWidget):
            # widgets can't be moved to another thread
            self._qtactor_thread = None
        else:
            # create a thread and move to it
            self._qtactor_thread = QtCore.QThread()
            self.moveToThread(self._qtactor_thread)
            self._qtactor_thread.started.connect(self._qtactor_run)
        self._qtactor_proc_gen = None
        self._qtactor_main_gen = None

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
        # use a timer to run generator in the background
        self._qtactor_timer = QtCore.QTimer()
        self._qtactor_timer.timeout.connect(self._qtactor_do_main)
        self._qtactor_timer.start()

    def _qtactor_do_main(self):
        try:
            self._qtactor_main_gen.next()
        except StopIteration:
            self._qtactor_timer.stop()
            self._qtactor_running.clear()

    def _qtactor_main(self):
        self.process_start()
        self.process()
        try:
            self._qtactor_proc_gen = self.gen_process()
        except:
            self._qtactor_proc_gen = None
        while self._qtactor_proc_gen:
            if not self._qtactor_running.is_set():
                self.onStop()
                self._qtactor_running.set()
                break
            self._qtactor_proc_gen.next()
            yield 1

    def stop(self):
        if self._qtactor_running.is_set():
            # process generator is still running
            self._qtactor_running.clear()
            self._qtactor_running.wait()
        if self._qtactor_thread:
            self._qtactor_thread.quit()

    def join(self):
        if self._qtactor_thread:
            self._qtactor_thread.wait()

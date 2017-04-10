from __future__ import (absolute_import, division, print_function)

from multiprocessing import Queue
from select import select
import logging

from .controller import Controller  # NOQA
from .vim_x import VimX  # NOQA

__metaclass__ = type  # pylint: disable=invalid-name


class Middleman:

    def __init__(self, vimx):
        self.ctrl = Controller(vimx)
        self.vimx = vimx
        self.queue = Queue(maxsize=2)
        self.logger = logging.getLogger(__name__)

    def safe_exec(self, fn):
        """ fn should take a VimX object as the only argument. """
        self.queue.put(['exec', fn])

    def loop(self):
        while True:
            rlist = [self.vimx.ch_in, self.queue._reader]
            if self.ctrl.dbg is not None:
                rlist += self.ctrl.dbg.read_list
            ready, _, _ = select(rlist, [], [], 2)
            for ev in ready:
                if ev == self.queue._reader:
                    req = self.queue.get()
                    if req[0] == 'exec':
                        fn = req[1]
                        fn(self.vimx)
                    elif req[0] == 'exit':
                        break
                elif ev == self.vimx.ch_in:
                    msg = self.vimx.wait()
                    self._handle(msg)
                else:
                    self.dbg.poke()

    def _handle(self, msg):
        head = msg[0]
        args = msg[1:]
        if head == 'session':
            self.ctrl.session.handle(*args)
        elif head == 'mode':
            assert(len(args) == 1)
            self.ctrl.session.mode_setup(args[0])
        elif head == 'exec':
            self.ctrl.execute(' '.join(args))
            if args[0] == 'help':
                self.ctrl.vimx.command('drop [gdb]logs')
        elif head == 'stdin':
            assert(len(args) == 1)
            self.ctrl.put_stdin(args[0])
        elif head == 'exit':
            assert(len(args) == 0)
            self.ctrl.dbg_stop()
        elif head == 'breakswitch':
            bufnr, line = args
            self.ctrl.do_breakswitch(bufnr, line)
        elif head == 'breakdelete':
            assert(len(args) == 1)
            self.ctrl.do_breakdelete(bp_id)
        elif head == 'refresh':
            assert(len(args) == 0)
            self.ctrl.update_buffers()

    def _select_thread_and_frame(self, thread, frame):
        pass

    def _btswitch(self):
        pass

    def _watchpoint(self, var_name):
        pass

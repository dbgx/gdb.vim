from __future__ import (absolute_import, division, print_function)

from threading import Thread, Event
from queue import Queue, Empty, Full
from signal import SIGINT
from os import path

from .vim_buffers import VimBuffers
from .session import Session

from pygdbmi.gdbcontroller import GdbController

__metaclass__ = type  # pylint: disable=invalid-name


class Controller(Thread):  # pylint: disable=too-many-instance-attributes
    """ Thread object that handles GDB events and commands. """

    def __init__(self, vimx):
        """ Creates the GDB SBDebugger object and more! """
        import logging
        self.logger = logging.getLogger(__name__)

        self._dbg = None

        self._proc_cur_line_len = 0
        self._proc_lines_count = 0
        self._ready = Event()
        self._ready.clear()

        self.result_queue = Queue(maxsize=1)

        self.vimx = vimx
        self.busy_stack = 0  # when > 0, buffers are not updated
        self.buffers = VimBuffers(self, vimx)
        self.session = Session(self, vimx)

        super(Controller, self).__init__()
        self.start() # start the thread

    def dbg_run(self):
        if self._dbg is None:
            self._dbg = GdbController()
            self._ready.set()

    def dbg_stop(self):
        self._ready.clear()
        self._dbg.gdb_process.send_signal(SIGINT) # remote process?

    def is_busy(self):
        return self.busy_stack > 0

    def busy_more(self):
        self.busy_stack += 1

    def busy_less(self):
        self.busy_stack -= 1
        if self.busy_stack < 0:
            self.logger.critical("busy_stack < 0")
            self.busy_stack = 0

    def get_program_counters(self):
        return []

    def get_breakpoints(self):
        return []

    def serialize_mijson(self, result):
        self.buffers.logs_append(str(result) + '\n', u'\u2713') # \u2717 for error

    def execute(self, command):
        """ Run command in the interpreter, refresh all buffers, and display the
            result in the logs buffer. Returns True if succeeded.
        """
        self.buffers.logs_append(u'\u2192(gdb) {}\n'.format(command))
        result = self.get_command_result(command)
        self.serialize_mijson(result)

        self.update_buffers()

    def complete_command(self, arg, line, pos):
        """ Returns a list of viable completions for line, and cursor at pos. """
        # TODO complete the first word?
        return []

    def update_buffers(self, buf=None):
        """ Update gdb buffers and signs placed in source files.
            @param buf
                If None, all buffers and signs would be updated.
                Otherwise, update only the specified buffer.
        """
        if self.is_busy():
            return
        if buf is None:
            self.buffers.update()
        else:
            self.buffers.update_buffer(buf)

    def bp_set_line(self, spath, line):
        filepath = path.abspath(spath)
        self.buffers.logs_append(u'\u2192(gdb-bp) {}:{}\n'.format(spath, line))
        #self.execute("b {}:{}".format(filepath, line)) #TODO
        #self.update_buffers(buf='breakpoints')

    def do_breakswitch(self, bufnr, line):
        """ Switch breakpoint at the specified line in the buffer. """
        key = (bufnr, line)
        if key in self.buffers.bp_list:
            bp = self.buffers.bp_list[key]
            #self.execute("delete breakpoints {}".format(bp.id)) #TODO
        else:
            self.bp_set_line(self.vimx.get_buffer_name(bufnr), line)

    def do_breakdelete(self, bp_id):
        """ Delete a breakpoint by id """
        #self.execute("breakpoint delete {}".format(bp_id)) #TODO
        pass

    def put_stdin(self, instr):
        #if process is running:
        self._dbg.write(instr, 0, read_response=False)

    def get_command_result(self, command):
        """ Runs command in the interpreter and returns (success, output)
            Not to be called directly for commands which changes debugger state;
            use execute instead.
        """
        #if process is not running:
        self.logger.info('(gdb) %s', command)
        self._dbg.write(command, 0, read_response=False)

        try:
            result = self.result_queue.get(block=True, timeout=3)
        except Empty:
            self.logger.warning('(gdb-no-result) %s', command)
            return None

        return result

    def _dbg_loop(self):
        to_count = 0
        while self._ready.is_set():
            try:
                responses = self._dbg.get_gdb_response(timeout_sec=1)
                to_count = 0
            except ValueError:
                to_count += 1
                if to_count > 3*3600:  # 3 hours: expected to occur only if timeout isn't timing out!
                    self.logger.critical('Broke the loop barrier!')
                    break
            except Exception as e:
                self.logger.critical('Unexpected error %s', e)
                break

            for resp in responses:
                if resp['type'] == 'result':
                    if self.result_queue.full():  # garbage?
                        self.result_queue.get()   # clean
                    self.result_queue.put(resp)

                # TODO handle 'notify' events
                # TODO handle 'output' and 'target' events
                # TODO handle 'console', 'log' and 'done' events

            #n_lines = self.buffers.logs_append(out)
            #if n_lines == 0:
            #    self._proc_cur_line_len += len(out)
            #else:
            #    self._proc_cur_line_len = 0
            #    self._proc_lines_count += n_lines
            #if self._proc_cur_line_len > 8192 or self._proc_lines_count > 2048:
            #    # detect and stop/kill insane process
            #    self._dbg.gdb_process.send_signal(SIGINT) # remote process?
            #    break

        self._dbg.exit()
        self._dbg = None
        self._ready.clear()
        self.logger.info('Terminated!')

    def run(self):
        while self._ready.wait():
            self._dbg_loop()

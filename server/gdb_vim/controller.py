from __future__ import (absolute_import, division, print_function)

from queue import Queue, Empty, Full
from signal import SIGINT
from os import path

from .vim_buffers import VimBuffers
from .session import Session

from pygdbmi.gdbcontroller import GdbController

__metaclass__ = type  # pylint: disable=invalid-name


class Controller():  # pylint: disable=too-many-instance-attributes
    """ Thread object that handles GDB events and commands. """

    def __init__(self, vimx):
        """ Creates the GDB SBDebugger object and more! """
        import logging
        self.logger = logging.getLogger(__name__)

        self.dbg = None

        self._proc_cur_line_len = 0
        self._proc_lines_count = 0

        self.result_queue = Queue(maxsize=1)

        self.vimx = vimx
        self.busy_stack = 0  # when > 0, buffers are not updated
        self.buffers = VimBuffers(self, vimx)
        self.session = Session(self, vimx)

    def dbg_start(self):
        if self.dbg is None:
            self.dbg = GdbController()

    def dbg_interrupt(self):
        self.dbg.gdb_process.send_signal(SIGINT) # what if remote process?

    def dbg_stop(self):
        self.dbg.exit()
        self.dbg = None
        self.logger.info('Terminated!')

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
        out = "message: {}, stream: {}, token: {}, type: {}\n".format(result.get('message'),
                                                                      result.get('stream'),
                                                                      result.get('token'),
                                                                      result.get('type'))
        payload = result.get('payload')
        if isinstance(payload, str):
            payload = payload.encode('utf8').decode('unicode_escape')
        else:
            payload = str(payload)
        out += "{}\n".format(payload)
        self.buffers.logs_append(out, u'\u2713')

    def execute(self, command):
        """ Run command in the interpreter, refresh all buffers, and display the
            result in the logs buffer. Returns True if succeeded.
        """
        self.buffers.logs_append(u'\u2192(gdb) {}\n'.format(command))
        result = self.get_command_result(command)
        if result is not None:
            self.serialize_mijson(result)
        else:
            self.logs_append("error\n", u'\u2717')

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
        self.dbg.write(instr, 0, read_response=False)

    def get_command_result(self, command):
        """ Runs command in the interpreter and returns (success, output)
            Not to be called directly for commands which changes debugger state;
            use execute instead.
        """
        #if process is not running:
        self.logger.info('(gdb) %s', command)
        self.dbg.write(command, 0, read_response=False)

        try:
            result = self.result_queue.get(block=True, timeout=3)
        except Empty:
            self.logger.warning('(gdb-no-result) %s', command)
            return None

        return result

    def poke(self):
        """ Pokes the gdb process for responses. """
        try:
            responses = self.dbg.get_gdb_response(timeout_sec=0.5)
            to_count = 0
        except ValueError as e:
            self.logger.warning('Gdb poke error: %s', e)
        except Exception as e:
            self.logger.critical('Unexpected error: %s', e)
            self.dbg_stop()

        for resp in responses:
            if resp['type'] == 'result':
                if self.result_queue.full():  # garbage?
                    self.result_queue.get()   # clean
                self.result_queue.put(resp)
            else:
                #self.serialize_mijson(resp)
                pass

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
        #    self.dbg.gdb_process.send_signal(SIGINT) # remote process?
        #    break

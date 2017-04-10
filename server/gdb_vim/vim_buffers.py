# Manages Vim user interface.
#
# TODO: display watched expressions
# TODO: define interface for interactive panes, like catching enter
#        presses to change selected frame/thread...

from __future__ import (absolute_import, division, print_function)

from os import path
from sys import stderr
from .vim_signs import BPSign, PCSign

__metaclass__ = type  # pylint: disable=invalid-name


class VimBuffers:  # pylint: disable=too-many-instance-attributes
    content_map = {
        "backtrace": "-stack-list-frames",
        "breakpoints": "-break-list",
        "disassembly": "-data-disassemble -f ab.c -l 1 -- 0",
        "threads": "-thread-info",
        "locals": "-stack-list-variables --frame 0 --simple-values",
        "registers": "-data-list-register-values 0 1 2 3 4 5 6 7"
    }

    def __init__(self, ctrl, vimx):
        """ Declare VimBuffers state variables """
        import logging
        self.ctrl = ctrl
        self.vimx = vimx
        self.logger = logging.getLogger(__name__)

        self.buf_map = {}

        # Currently shown signs
        self.bp_signs = {}  # maps (bufnr, line) -> <BPSign object>
        self.pc_signs = {}
        self.pc_cur_loc = None

    def buf_check_init(self):
        if not self.buf_map:
            self.buf_map = self.vimx.init_buffers()

    def logs_append(self, outstr, prefix=None):
        """ Returns the number lines appended """
        self.buf_check_init()

        if len(outstr) == 0:
            return 0
        lines = outstr.replace('\r\n', '\n').split('\n')
        if prefix is not None:
            last_line = lines[-1]
            if len(last_line) > 0:
                last_line = prefix + last_line
            lines = [prefix + line for line in lines[:-1]] + [last_line]
        print('\n'.join(lines), file=stderr)
        #self.vimx.update_noma_buffer(self.buf_map['logs'], lines, append=True)
        self.vimx.buffer_scroll_bottom(self.buf_map['logs'])
        return len(lines) - 1

    def update_pc(self):  # pylint: disable=too-many-branches
        """ Place the PC sign on the PC location of each thread's selected frame.
            If the 'selected' PC location has changed, jump to it.
        """

        pc_list = self.ctrl.get_program_counters()

        # Clear all existing PC signs
        for sign in self.pc_signs.values():
            sign.hide()
        self.pc_signs = {}

        for filepath, line, is_selected in pc_list:
            self.logger.info("Got pc loc: %s", repr(loc))
            if path_exists(filepath):
                bufnr = self.vimx.buffer_add(filepath)
            else:
                continue

            key = (bufnr, line)
            if key in self.pc_signs: # already added in a previous iteration
                if is_selected:
                    self.pc_signs[key].hide()
                else:
                    continue

            sign = PCSign(self.vimx, bufnr, line, is_selected)
            self.pc_signs[key] = sign

            if is_selected and self.pc_cur_loc != key:
                self.vimx.sign_jump(bufnr, sign.id)
                self.pc_cur_loc = key

    def update_breakpoints(self, hard_update=False):
        """ Decorates buffer with signs corresponding to breakpoints. """

        bp_list = self.ctrl.get_breakpoints()

        new_bps = set()
        for filepath, line, bpid in bp_list:
            if filepath and path.exists(filepath):
                bufnr = self.vimx.buffer_add(filepath)
                key = (bufnr, line)
                new_bps.add(key)

        # Hide all (outdated) breakpoint signs
        for key, sign in self.bp_signs.copy().items():
            if hard_update or key not in new_bps:
                sign.hide()
                del self.bp_signs[key]
            else:
                if bp_signs[key].hidden:
                    bp_signs[key].show()
                new_bps.discard(key)

        # Show all (new) breakpoint signs
        for (bufnr, line) in new_bps:
            self.bp_signs[(bufnr, line)] = BPSign(
                self.vimx, bufnr, line, (bufnr, line) in self.pc_signs)

    def update_buffer(self, buf):
        self.buf_check_init()

        command = self.content_map[buf]
        result = self.ctrl.get_command_result(command)
        result_lines = str(result).split('\n')

        if buf == 'breakpoints':
            self.update_breakpoints()

        self.vimx.update_noma_buffer(self.buf_map[buf], result_lines)

    def update(self):
        """ Updates signs, buffers, and possibly jumps to pc. """
        self.update_pc()

        for buf in self.content_map:
            self.update_buffer(buf)

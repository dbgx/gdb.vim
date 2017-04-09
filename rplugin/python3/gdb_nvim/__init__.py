from __future__ import (absolute_import, division, print_function)

import logging
import neovim

__metaclass__ = type  # pylint: disable=invalid-name

# pylint: disable=wrong-import-position
from .controller import Controller  # NOQA
from .vim_x import VimX  # NOQA
# pylint: enable=wrong-import-position


@neovim.plugin  # pylint: disable=too-few-public-methods
class Middleman:

    def __init__(self, vim):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.ctrl = Controller(VimX(vim))
        if self.ctrl.vimx._vim_test:  # pylint: disable=protected-access
            print("Note: `:LL-` commands are not bound with this test instance")
        else:
            vim.command('call gdb#remote#init(%d)' % vim.channel_id)

    # The only interface that is predefined in the remote plugin manifest file.
    # The first execution of `:LLsession` initializes the remote part of the plugin.
    @neovim.command('LLsession', nargs='+', complete='customlist,gdb#session#complete')
    def _session(self, args):
        self.ctrl.session.handle(*args)

    @neovim.rpc_export('mode')
    def _mode(self, mode):
        self.ctrl.session.mode_setup(mode)

    @neovim.rpc_export('exec')
    def _exec(self, *args):
        self.ctrl.execute(' '.join(args))

        if args[0] == 'help':
            self.ctrl.vimx.command('drop [gdb]logs')

    @neovim.rpc_export('stdin')
    def _stdin(self, strin):
        self.ctrl.put_stdin(strin)

    @neovim.rpc_export('exit')
    def _exit(self):
        self.ctrl.dbg_stop()

    @neovim.rpc_export('complete', sync=True)
    def _complete(self, arg, line, pos):
        return self.ctrl.complete_command([arg, line, pos])

    @neovim.rpc_export('get_modes', sync=True)
    def _get_modes(self):
        return self.ctrl.session.get_modes()

    @neovim.rpc_export('select_thread_and_frame')
    def _select_thread_and_frame(self, thread_and_frame_idx):
        thread, frame = thread_and_frame_idx
        pass

    @neovim.rpc_export('btswitch')
    def _btswitch(self):
        pass

    @neovim.rpc_export('breakswitch')
    def _breakswitch(self, bufnr, line):
        self.ctrl.do_breakswitch(bufnr, line)

    @neovim.rpc_export('breakdelete')
    def _breakdelete(self, bp_id):
        self.ctrl.do_breakdelete(bp_id)

    @neovim.rpc_export('refresh')
    def _refresh(self):
        self.ctrl.update_buffers()

    @neovim.rpc_export('watchswitch')
    def _watchpoint(self, var_name):
        pass  # TODO create watchpoint from locals pane

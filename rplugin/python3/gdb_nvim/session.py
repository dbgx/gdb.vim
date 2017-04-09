from __future__ import (absolute_import, division, print_function)

from collections import OrderedDict
from time import sleep
from os import path, chdir
import json

__metaclass__ = type  # pylint: disable=invalid-name


class Session:  # pylint: disable=too-many-instance-attributes

    def __init__(self, ctrl, vimx):
        import logging
        self.logger = logging.getLogger(__name__)

        self.ctrl = ctrl
        self.vimx = vimx
        self.state = OrderedDict()
        self.internal = {}
        self.json_decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
        self.help_flags = {"new": False, "launch_prompt": True, "session_show": True}
        self.bpid_map = {}

    def isalive(self):
        """ Returns true if a well-defined session is alive """
        return len(self.state) > 1 and '@file' in self.internal and '@mode' in self.internal

    def new_target(self, target):
        self.bpid_map = {}

    def format(self, s):
        return s.format(**self.state['variables'])

    def run_actions(self, actions):  # pylint: disable=too-many-branches
        self.ctrl.busy_more()
        for action in actions:
            if isinstance(action, str):
                self.ctrl.execute(self.format(action))
            else:
                self.logger.critical("Invalid action!")
        self.ctrl.busy_less()

    def get_modes(self):
        if 'modes' in self.state:
            return self.state['modes'].keys()
        else:
            return []

    def mode_setup(self, mode):
        """ Tear down the current mode, and switch to a new one. """
        if mode not in self.get_modes():
            self.vimx.log("Invalid mode!")
            return
        self.mode_teardown()
        self.internal['@mode'] = mode
        self.vimx.command("call call(g:gdb#session#mode_setup, ['%s'])" % mode)
        if mode.startswith('debug'):
            self.ctrl.dbg_run()
            if 'setup' in self.state['modes'][mode]:
                self.run_actions(self.state['modes'][mode]['setup'])
            self.ctrl.update_buffers()
        if self.help_flags["new"] and \
                self.help_flags["launch_prompt"] and \
                self.internal['@mode'] == 'debug':
            sleep(0.4)
            if self.vimx.eval("input('Launch the target? [y=yes] ', 'y')") == 'y':
                self.state['modes']['debug']['setup'].append('run')
                self.ctrl.execute('run')
                self.vimx.log('Process launched! Try `:GGsession show`', 0)
            self.help_flags["launch_prompt"] = False

    def mode_teardown(self):
        if self.isalive():
            mode = self.internal['@mode']
            if 'teardown' in self.state['modes'][mode]:
                self.run_actions(self.state['modes'][mode]['teardown'])
            self.vimx.command("call call(g:gdb#session#mode_teardown, ['%s'])" % mode)
            del self.internal['@mode']
            if mode.startswith('debug'):
                self.ctrl.dbg_stop()
            return True
        return False

    def get_confpath(self):
        if self.isalive():
            return path.join(self.internal["@dir"], self.internal["@file"])
        else:
            return None

    def path_shorten(self, abspath):
        return path.relpath(abspath, self.internal["@dir"])

    def set_path(self, confpath):
        head, tail = path.split(path.abspath(confpath))
        if len(tail) == 0:
            self.vimx.log("Error: invalid path!")
            return False
        try:
            chdir(head)
        except OSError as e:
            self.vimx.log("%s" % e)
            return False
        self.internal["@dir"] = head
        self.internal["@file"] = tail
        return True

    def parse_and_load(self, conf_str):  # pylint: disable=too-many-branches
        state = self.json_decoder.decode(conf_str)
        if not isinstance(state, dict):
            raise ValueError("The root object must be an associative array")

        for key in ["variables", "modes", "breakpoints"]:
            if key not in state:
                state[key] = {}

        for key in state:
            if key == "variables":
                pass  # TODO check validity
            elif key == "modes":
                if len(state["modes"]) == 0:
                    raise ValueError("At least one mode has to be defined")
            elif key == "breakpoints":
                pass
            else:
                raise ValueError("Invalid key '%s'" % key)

            if not isinstance(state[key], dict):
                raise ValueError('"%s" must be an associative array' % key)

        self.mode_teardown()
        self.state = state
        self.mode_setup(list(self.state["modes"].keys())[0])

    def handle_new(self):
        if self.isalive() and self.vimx.eval("gdb#session#discard_prompt()") == 0:
            self.vimx.log("Session left unchanged!", 0)
            return

        ret = self.vimx.eval("gdb#session#new()")
        if not ret or '_file' not in ret:
            self.vimx.log("Skipped -- no session was created!")
            return
        if not self.set_path(ret["_file"]):
            return

        try:
            self.parse_and_load("""{
                "variables": {},
                "modes": {
                    "code": {},
                    "debug": {
                        "setup": ["#source -v bps.gdb #note: commented out"],
                        "teardown": ["#save breakpoints bps.gdb"]
                    }
                }
            }""")
        except ValueError as e:
            self.vimx.log("Unexpected error: " + str(e))
            return

        if 'target' in ret and len(ret['target']) > 0:
            self.state["variables"]["target"] = \
                self.path_shorten(self.vimx.abspath(ret["target"]))
            debug = self.state["modes"]["debug"]
            debug["setup"].insert(0, "file {target}")
            self.help_flags["new"] = True

        self.vimx.log("New session created!", 0)

    def handle_load(self, confpath):
        if self.isalive() and self.vimx.eval("gdb#session#discard_prompt()") == 0:
            self.vimx.log("Session left unchanged!", 0)
            return

        try:
            with open(confpath) as f:
                self.parse_and_load(''.join(f.readlines()))
        except (ValueError, IOError) as e:
            self.vimx.log("Bad session file: " + str(e))
        else:
            self.set_path(confpath)
            self.vimx.log("Loaded %s" % confpath, 0)

    def handle_show(self):
        if self.isalive():
            sfile_bufnr = self.vimx.buffer_add(self.get_confpath())
            self.vimx.command('exe "tab drop ".escape(bufname({0}), "$%# ")'
                              .format(sfile_bufnr))

            json_str = json.dumps(self.state, indent=4, separators=(',', ': '))

            def json_show(b):
                if b.number == sfile_bufnr:
                    b[:] = json_str.split('\n')
                    raise StopIteration

            self.vimx.map_buffers(json_show)
            if self.help_flags["new"] and self.help_flags["session_show"]:
                self.vimx.log(
                    'Save this file, and do `:GGsession reload` to load any changes made.')
                self.help_flags["session_show"] = False
        else:
            self.vimx.log("No active session.")

    def handle(self, cmd, *args):
        """ Handler for :GGsession commands. """
        if cmd == 'new':
            self.handle_new()
        elif cmd == 'relod':
            if '@file' not in self.internal:
                self.vimx.log("No active session!")
            elif len(args) > 0:
                self.vimx.log("Too many arguments!")
            else:
                self.handle_load(self.get_confpath())
        elif cmd == 'load':
            if len(args) == 0:
                confpath = self.vimx.eval('findfile(g:gdb#session#file, ".;")')
                self.handle_load(confpath)
            elif len(args) == 1:
                self.handle_load(args[0])
            else:
                self.vimx.log("Too many arguments!")
        elif cmd == 'show':
            self.handle_show()
        else:
            self.vimx.log("Invalid sub-command: %s" % cmd)

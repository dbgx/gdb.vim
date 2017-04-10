from __future__ import (absolute_import, division, print_function)

from queue import Queue
from os import path
import logging
import json

__metaclass__ = type  # pylint: disable=invalid-name


class VimX:

    def __init__(self, ch_in, ch_out):
        self.ch_in = ch_in
        self.ch_out = ch_out
        self.counter = -1
        self.buffer = [] # buffer for 'positive' objects
        self.logger = logging.getLogger(__name__)
        self.buffer_cache = {}

    def wait(self, expect=0):
        """ Blocking function. Use with care!
            `expect` should either be 0 or a negative number. If `expect == 0`, any positive
            indexed object is returned. Otherwise, it will queue any positive objects until the
            first negative object is received. If the received negative object does not match
            `expect`, then a ValueError is raised.
        """
        if expect > 0:
            raise AssertionError('expect <= 0')
        if expect == 0 and len(self.buffer) > 0:
            return self.pop()
        while True:
            s = self.ch_in.readline()
            self.logger.info("read: %s", s)
            ind, obj = json.loads(s)
            if (expect == 0 and ind < 0) or (expect < 0 and expect != ind):
                raise ValueError('Incorrect index received! {} != {}', expect, ind)
            elif expect < 0 and ind > 0:
                self.buffer.insert(0, obj)
            else:
                break
        return obj

    def write(self, obj):
        s = json.dumps(obj)
        print(s, file=self.ch_out) # with line break
        self.ch_out.flush()
        self.logger.info("write: %s", s)

    def send(self, obj):
        self.write([0, obj])

    def call(self, fname, *args, reply=True):
        obj = ['call', fname, args]
        if reply:
            self.counter -= 1
            obj += [self.counter]
        self.write(obj)
        if reply:
            re = self.wait(expect=self.counter)
            return re[1]

    def eval(self, expr, reply=True):
        obj = ['expr', expr]
        if reply:
            self.counter -= 1
            obj += [self.counter]
        self.write(obj)
        if reply:
            re = self.wait(expect=self.counter)
            return re

    def command(self, cmd):
        obj = ['ex', cmd]
        self.write(obj)

    def log(self, msg, level=1):
        """ Execute echom in vim using appropriate highlighting. """
        level_map = ['None', 'WarningMsg', 'ErrorMsg']
        msg = msg.strip().replace('"', '\\"').replace('\n', '\\n')
        self.command('echohl {} | echom "{}" | echohl None'.format(level_map[level], msg))

    def buffer_add(self, name):
        """ Create a buffer (if it doesn't exist) and return its number. """
        bufnr = self.call('bufnr', name, 1)
        self.call('setbufvar', bufnr, '&bl', 1, reply=False)
        return bufnr

    def buffer_scroll_bottom(self, bufnr):
        """ Scroll to bottom for every window that displays the given buffer in the current tab """
        self.call('gdb#util#buffer_do', bufnr, 'normal! G', reply=False)

    def sign_jump(self, bufnr, sign_id):
        """ Try jumping to the specified sign_id in buffer with number bufnr. """
        self.call('gdb#layout#signjump', bufnr, sign_id, reply=False)

    def sign_place(self, sign_id, name, bufnr, line):
        """ Place a sign at the specified location. """
        self.command("sign place {} name={} line={} buffer={}".format(sign_id, name, line, bufnr))

    def sign_unplace(self, sign_id):
        """ Hide a sign with specified id. """
        self.command("sign unplace {}".format(sign_id))

    def get_buffer_name(self, nr): # FIXME?
        """ Get the buffer name given its number. """
        return self.call('bufname', nr)

    def abspath(self, relpath):
        vim_cwd = self.call("getcwd")
        return path.join(vim_cwd, relpath)

    def init_buffers(self):
        """ Create all gdb buffers and initialize the buffer map. """
        return self.call('gdb#layout#init_buffers')

    def update_noma_buffer(self, bufnr, content):  # noma => nomodifiable
        has_mod = True
        if bufnr in self.buffer_cache \
                and len(content) == len(self.buffer_cache[bufnr]):
            has_mod = False
            for l1, l2 in zip(content, self.buffer_cache[bufnr]):
                if l1 != l2:
                    has_mod = True
                    break

        if has_mod:
            self.call('gdb#layout#update_buffer', bufnr, content, reply=False)

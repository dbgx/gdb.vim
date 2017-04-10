import sys
import os
import logging

logger = logging.getLogger(__name__)
logfile = 'logs'
handler = logging.FileHandler(logfile, 'w')
handler.formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s @ '
    '%(filename)s:%(funcName)s:%(lineno)s] %(process)s - %(message)s')
logging.root.addHandler(handler)
logging.root.setLevel(logging.DEBUG)

plugpath = os.path.realpath('../server')
sys.path.append(plugpath)

try:
    from gdb_vim import Middleman
    from gdb_vim.vim_x import VimX
    vimx = VimX(sys.stdin, sys.stdout)
    iface = Middleman(vimx)

    # FIXME
    from time import sleep
    delay = 1
    iface._session(['load', 'gdb-vim.json'])
    sleep(delay)
    iface._mode('debug')
    sleep(2*delay)
    iface._exec('continue')
    sleep(delay)
    iface._stdin('4\n')
    sleep(delay)
    iface._exec('continue')
    sleep(delay)
    iface._mode('code')
    iface._exit() # Don't forget to exit!
except:
    import traceback
    traceback.print_exc()

print('Debugger terminated! If you see no errors, everything\'s cool!')

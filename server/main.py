import logging
from gdb_vim.vim_x import VimX
from gdb_vim import Middleman
import sys

def main():
    ch_in = sys.stdin
    ch_out = sys.stdout
    vimx = VimX(ch_in, ch_out)

    Middleman(vimx).loop()

if __name__ == '__main__':
    handler = logging.FileHandler('/tmp/gdb.vim.log', 'w')
    handler.formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s @ '
        '%(filename)s:%(funcName)s:%(lineno)s] - %(message)s')
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.DEBUG)
    main()

# GDB Vim Frontend

**Warning: Under development. Development currently stalled due to issues with Vim.**

This plugin provides GDB debugger integration for Vim ([demo gif]) featuring:

* Elaborate view of debugger state
* Event-based, non-blocking UI
* Jump to code from Backtrace or Threads windows
* Define commands to replay when switching between modes (`code <-> debug`)

This plugin takes advantage of Vim's job API.

## Prerequisites

* [Vim 8.0+](https://github.com/vim/vim) (for `+channel` and `+job` support)
* [GDB 7.7+](https://www.gnu.org/software/gdb/)
* [Pygdbmi](https://github.com/cs01/pygdbmi)

## Installation

1. Using a plugin manager such as [vim-plug](https://github.com/junegunn/vim-plug):

   ```
       Plug 'dbgx/gdb.vim'
   ```

   Alternatively, clone this repo, and add the following line to your vimrc:

   ```
       set rtp+=/path/to/gdb.vim
   ```

## Goals

The plugin is being developed keeping 3 broad goals in mind:

* **Ease of use**: Users with almost zero knowledge of command line debuggers should feel comfortable using this plugin.
* **Completeness**: Experienced users of GDB should not feel restricted.
* **Customizability**: Users should be able to bend this plugin to their needs.

## FAQ

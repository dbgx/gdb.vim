# GDB Neovim Frontend

This plugin provides GDB debugger integration for Neovim ([demo gif]) featuring:

* Elaborate view of debugger state
* Event-based, non-blocking UI
* Jump to code from Backtrace or Threads windows
* Define commands to replay when switching between modes (`code <-> debug`)

This plugin takes advantage of Neovim's job API to spawn a separate process
and communicates with the Neovim process using RPC calls.

## Prerequisites

* [Neovim](https://github.com/neovim/neovim)
* [Neovim python3-client](https://github.com/neovim/python-client) (release >= 0.1.6)
* [GDB](https://www.gnu.org/software/gdb/)
* [Pygdbmi](https://github.com/cs01/pygdbmi)

## Installation

1. Using a plugin manager such as [vim-plug](https://github.com/junegunn/vim-plug):

   ```
       Plug 'dbgx/gdb.nvim'
   ```

   Alternatively, clone this repo, and add the following line to your nvimrc:

   ```
       set rtp+=/path/to/gdb.nvim
   ```

2. Execute:

   ```
       :UpdateRemotePlugins
   ```

   and restart Neovim.

## Goals

The plugin is being developed keeping 3 broad goals in mind:

* **Ease of use**: Users with almost zero knowledge of command line debuggers should feel comfortable using this plugin.
* **Completeness**: Experienced users of GDB should not feel restricted.
* **Customizability**: Users should be able to bend this plugin to their needs.

## FAQ

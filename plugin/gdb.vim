" ---------------------------------------------------------------------
"  File:        gdb.vim
"  Maintainer:  John C F <john.ch.fr@gmail.com>
"  --------------------------------------------------------------------

if exists('g:loaded_gdb') || !has('nvim') || !has('python')
  finish
endif
let g:loaded_gdb = 1

if !exists('g:gdb#session#file')
  let g:gdb#session#file = 'gdb-nvim.json'
endif
if !exists('g:gdb#session#mode_setup')
  let g:gdb#session#mode_setup = 'gdb#layout#setup'
endif
if !exists('g:gdb#session#mode_teardown')
  let g:gdb#session#mode_teardown = 'gdb#layout#teardown'
endif

let s:bp_symbol = get(g:, 'gdb#sign#bp_symbol', 'B>')
let s:pc_symbol = get(g:, 'gdb#sign#pc_symbol', '->')

highlight default link LLBreakpointSign Type
highlight default link LLUnselectedPCSign NonText
highlight default link LLUnselectedPCLine DiffChange
highlight default link LLSelectedPCSign Debug
highlight default link LLSelectedPCLine DiffText

execute 'sign define llsign_bpres text=' . s:bp_symbol .
    \ ' texthl=LLBreakpointSign linehl=LLBreakpointLine'
execute 'sign define llsign_pcsel text=' . s:pc_symbol .
    \ ' texthl=LLSelectedPCSign linehl=LLSelectedPCLine'
execute 'sign define llsign_pcunsel text=' . s:pc_symbol .
    \ ' texthl=LLUnselectedPCSign linehl=LLUnselectedPCLine'

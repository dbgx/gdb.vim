" ---------------------------------------------------------------------
"  File:        gdb.vim
"  Maintainer:  John C F <john.ch.fr@gmail.com>
"  --------------------------------------------------------------------

if exists('g:loaded_gdb') || !has('job') || !has('channel')
  finish
endif
let g:loaded_gdb = 1

let g:gdb#_server = expand('<sfile>:p:h:h') . '/server/main.py'

if !exists('g:gdb#session#file')
  let g:gdb#session#file = 'gdb-vim.json'
endif
if !exists('g:gdb#session#mode_setup')
  let g:gdb#session#mode_setup = 'gdb#layout#setup'
endif
if !exists('g:gdb#session#mode_teardown')
  let g:gdb#session#mode_teardown = 'gdb#layout#teardown'
endif

command! -nargs=+ -complete=customlist,gdb#session#complete GGsession call gdb#remote#init() | call gdb#remote#__notify("session", <f-args>)

let s:bp_symbol = get(g:, 'gdb#sign#bp_symbol', 'B>')
let s:pc_symbol = get(g:, 'gdb#sign#pc_symbol', '->')

highlight default link GGBreakpointSign Type
highlight default link GGUnselectedPCSign NonText
highlight default link GGUnselectedPCLine DiffChange
highlight default link GGSelectedPCSign Debug
highlight default link GGSelectedPCLine DiffText

execute 'sign define llsign_bpres text=' . s:bp_symbol .
    \ ' texthl=GGBreakpointSign linehl=GGBreakpointLine'
execute 'sign define llsign_pcsel text=' . s:pc_symbol .
    \ ' texthl=GGSelectedPCSign linehl=GGSelectedPCLine'
execute 'sign define llsign_pcunsel text=' . s:pc_symbol .
    \ ' texthl=GGUnselectedPCSign linehl=GGUnselectedPCLine'

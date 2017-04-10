function! gdb#remote#__notify(event, ...) abort
  if !exists('g:gdb#_job')
    throw 'GDB: job does not exist!'
  endif
  let arg_list = extend([a:event], a:000)
  call ch_sendexpr(g:gdb#_job, arg_list)
endfun

function! gdb#remote#init()
  if exists('g:gdb#_job') && job_status(g:gdb#_job) == 'run'
    throw 'GDB: job already running'
  endif
  let cmd = ['python3', g:gdb#_server]
  let g:gdb#_job = job_start(cmd, { 'in_mode': 'json',
                                  \ 'out_mode': 'json',
                                  \ 'err_mode': 'nl',
                                  \ 'err_io': 'buffer',
                                  \ 'err_name': '[gdb]logs'})
  au VimLeavePre * call gdb#remote#__notify('exit')
  call gdb#remote#define_commands()
endfun

let s:ctrlchars = { 'BS': "\b",
                  \ 'CR': "\r",
                  \ 'EOT': "\x04",
                  \ 'LF': "\n",
                  \ 'NUL': "\0",
                  \ 'SPACE': " " }
function! s:stdincompl(A, L, P)
  return keys(s:ctrlchars) + [ '--raw' ]
endfun

function! gdb#remote#stdin_prompt(...)
  let strin = ''
  if a:0 == 1 && len(a:1) > 0
    if has_key(s:ctrlchars, a:1)
      let strin = s:ctrlchars[a:1]
    elseif a:1 == '--raw'
      let strin = input('raw> ')
    else
      let strin = input("Invalid argument!\nline> ", a:1) . "\n"
    endif
  elseif a:0 > 1
    let strin = input("Too many arguments!\nline> ", join(a:000, ' ')) . "\n"
  else
    let strin = input('line> ') . "\n"
  endif
  call gdb#remote#__notify("stdin", strin)
endfun

function! gdb#remote#get_modes()
  if exists('g:gdb#_channel_id')
    return rpcrequest(g:gdb#_channel_id, 'get_modes')
  else
    return []
  endif
endfun

function! gdb#remote#define_commands()
  command!           GGrefresh call gdb#remote#__notify("refresh")

  command! -nargs=1       -complete=customlist,gdb#session#complete
          \          GGmode    call gdb#remote#__notify("mode", <f-args>)

  command! -nargs=*  GG        call gdb#remote#__notify("exec", <f-args>)
  command! -nargs=?       -complete=customlist,<SID>stdincompl
          \          GGstdin   call gdb#remote#stdin_prompt(<f-args>)
  command! -nargs=+       -complete=customlist,gdb#session#complete
          \          GGsession call gdb#remote#__notify("session", <f-args>)

  nnoremap <silent> <Plug>GGBreakSwitch
          \ :call gdb#remote#__notify("breakswitch", bufnr("%"), getcurpos()[1])<CR>
  vnoremap <silent> <Plug>GGStdInSelected
          \ :<C-U>call gdb#remote#__notify("stdin", gdb#util#get_selection())<CR>
endfun

function! lldb#layout#init_buffers()
  let s:buffers = [ 'backtrace', 'breakpoints', 'disassembly', 'locals', 'registers', 'threads' ]
  let s:buffer_map = {}
  let u_bnr = bufnr('%')
  for bname in s:buffers
    let bnr = bufnr('lldb_' . bname, 1)
    call setbufvar(bnr, '&bt', 'nofile')
    call setbufvar(bnr, '&swf', 0)
    call setbufvar(bnr, '&ma', 0)
    exe 'silent b ' . bnr
    call setbufvar(bnr, '&nu', 0)
    call setbufvar(bnr, '&rnu', 0)
    call setbufvar(bnr, '&bl', 0)
    let s:buffer_map[bname] = bnr
  endfor
  exe 'b ' . u_bnr
  return s:buffer_map
endfun

function! lldb#layout#setup(mode)
  if a:mode != 'debug'
    return
  endif
  let code_buf = bufnr('%')
  if index(s:buffers, code_buf) >= 0
    let code_buf = '[No Name]'
  endif
  exe '0tab sb ' . code_buf
  exe 'belowright vertical sb ' . s:buffer_map['backtrace']
  exe 'belowright sb ' . s:buffer_map['breakpoints']
  exe 'belowright sb ' . s:buffer_map['disassembly']
  exe 'belowright vertical sb ' . s:buffer_map['locals']
  wincmd k
  exe 'belowright vertical sb ' . s:buffer_map['registers']
  wincmd k
  exe 'belowright vertical sb ' . s:buffer_map['threads']
  exe bufwinnr(code_buf) . "wincmd w"
endfun

" ignores all arguments
function! lldb#layout#teardown(...)
  if !exists('s:buffer_map') || empty(s:buffer_map)
    return
  endif
  let tabcount = tabpagenr('$')
  let bufnrs = values(s:buffer_map)
  for i in range(tabcount)
    let tabnr = tabcount - i
    let blist = tabpagebuflist(tabnr)
    let bcount = 0
    exe 'tabn ' . tabnr
    for bnr in blist
      if index(bufnrs, bnr) >= 0
        let bcount += 1
        exe bufwinnr(bnr) . 'close'
      endif
    endfor
    if len(tabpagebuflist(tabnr)) < bcount
      " close tab if majority of windows were lldb buffers
      tabc
    endif
  endfor
endfun

function! lldb#layout#switch_mode(...)
  if !exists('s:buffer_map') || empty(s:buffer_map)
    call lldb#layout#init_buffers()
  endif
  if exists('g:lldb#session#_mode')
    call call(g:lldb#session#mode_teardown, [g:lldb#session#_mode])
    let new_mode = g:lldb#session#_mode
  elseif a:0 == 0
    echom 'No session modes found!'
    return
  endif
  let new_mode = a:0 ? a:1 : new_mode
  call call(g:lldb#session#mode_setup, [new_mode])
  let g:lldb#session#_mode = new_mode
endfun

function! lldb#layout#signjump(bufnr, signid)
  if bufwinnr(a:bufnr) < 0
    let wnr = -1
    let ll_bufnrs = values(s:buffer_map)
    for i in range(winnr('$'))
      if index(ll_bufnrs, winbufnr(i+1)) < 0
        let wnr = i+1
        break
      endif
    endfor
    if wnr < 0
      return
    endif
    exe wnr . "wincmd w"
    exe a:bufnr . 'b'
  endif
  exe 'sign jump ' . a:signid . ' buffer=' . a:bufnr
endfun

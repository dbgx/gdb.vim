let name = expand('%')[5:]
if name == 'logs'
  syn match GGCmdMarker /→/ conceal contained
  syn match GGCmd /→.*$/ contains=GGCmdMarker
  syn match GGCmdOutMarker /✓/ conceal contained
  syn match GGCmdOut /✓.*$/ contains=GGCmdOutMarker
  syn match GGCmdErrMarker /✗/ conceal contained
  syn match GGCmdErr /✗.*$/ contains=GGCmdErrMarker

  hi def link GGCmdMarker Ignore
  hi def link GGCmdOutMarker Ignore
  hi def link GGCmdErrMarker Ignore

  hi def link GGCmd Comment
  hi def link GGCmdOut Debug
  hi def link GGCmdErr Exception
elseif name == 'backtrace'
  syn match GGFrameNumber /frame \zs#[0-9]\+/ contained
  syn match GGSelectedFrame /^  \* .*/ contains=GGFrameNumber
  syn match GGOtherFrame /^    .*/ contains=GGFrameNumber

  hi def link GGFrameNumber Number
  hi def link GGSelectedFrame Statement
  hi def link GGOtherFrame Comment
elseif name == 'breakpoints'
  syn match GGBpId /^[0-9]\+/ contained
  syn match GGBpParams /[a-z]\+ = \zs[^,]\+\|resolved/ contained
  syn match GGBpLine /^[0-9]\+: .*/ contains=GGBpId,GGBpParams
  syn match GGBpLocLine /^  [0-9]\+.[0-9]\+: .*/ contains=GGBpParams

  hi def link GGBpId Number
  hi def link GGBpParams Identifier
  hi def link GGBpLine Statement
  hi def link GGBpLocLine Comment
elseif name == 'locals'
  syn match GGVarType /^(\zs.\+\ze)/ contained
  syn match GGVarIdent /) \zs\i\+\ze = /
  syn match GGVarLine /^([^=]\+\i\+ = .*/ contains=GGVarType,GGVarIdent

  hi def link GGVarType Type
  hi def link GGVarIdent Identifier
elseif name == 'threads'
  syn match GGThreadNumber /thread \zs#[0-9]\+/ contained
  syn match GGThreadParams /[:,] [a-z ]\+ = \zs[^,]\+/ contained
  syn match GGSelectedThread /^\* .*/ contains=GGThreadNumber,GGThreadParams
  syn match GGOtherThread /^  .*/ contains=GGThreadNumber,GGThreadParams

  hi def link GGThreadNumber Number
  hi def link GGThreadParams Identifier
  hi def link GGSelectedThread Statement
  hi def link GGOtherThread Comment
elseif name == 'registers'
  syn match GGRegHex /0x[0-9a-f]\+/
  syn match GGRegIdent /^ \+\zs\i\+\ze = /
  syn cluster GGRegLine contains=GGRegIdent,GGRegIdent

  hi def link GGRegHex Number
  hi def link GGRegIdent Identifier
elseif name == 'disassembly'
  set syntax=asm
endif

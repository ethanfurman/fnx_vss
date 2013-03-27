from fxFNs import hta

def _00(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _01(stmt, vartbl, ptr, retval):
	retval.append("ADD ")
	ptr += 1
	return ptr

def _02(stmt, vartbl, ptr, retval):
	retval.append("ADDR ")
	ptr += 1
	return ptr

def _03(stmt, vartbl, ptr, retval):
	retval.append("BEGIN ")
	ptr += 1
	return ptr

def _04(stmt, vartbl, ptr, retval):
	retval.append("CALL ")
	ptr += 1
	return ptr

def _05(stmt, vartbl, ptr, retval):
	retval.append("CHDIR ")
	ptr += 1
	return ptr

def _06(stmt, vartbl, ptr, retval):
	retval.append("CLEAR ")
	ptr += 1
	return ptr

def _07(stmt, vartbl, ptr, retval):
	retval.append("CLOSE ")
	ptr += 1
	return ptr

def _08(stmt, vartbl, ptr, retval):
	retval.append("DEF ")
	ptr += 1
	return ptr

def _09(stmt, vartbl, ptr, retval):
	retval.append("DELETE ")
	ptr += 1
	return ptr

def _0A(stmt, vartbl, ptr, retval):
	retval.append("DIM ")
	ptr += 1
	return ptr

def _0B(stmt, vartbl, ptr, retval):
	retval.append("DIRECT ")
	ptr += 1
	return ptr

def _0C(stmt, vartbl, ptr, retval):
	retval.append("DISABLE ")
	ptr += 1
	return ptr

def _0D(stmt, vartbl, ptr, retval):
	retval.append("DROP ")
	ptr += 1
	return ptr

def _0E(stmt, vartbl, ptr, retval):
	retval.append("EDIT")
	ptr += 1
	return ptr

def _0F(stmt, vartbl, ptr, retval):
	retval.append("ENABLE ")
	ptr += 1
	return ptr

def _10(stmt, vartbl, ptr, retval):
	retval.append("END")
	ptr += 1
	return ptr

def _11(stmt, vartbl, ptr, retval):
	retval.append("ENDTRACE")
	ptr += 1
	return ptr

def _12(stmt, vartbl, ptr, retval):
	retval.append("ENTER ")
	ptr += 1
	return ptr

def _13(stmt, vartbl, ptr, retval):
	retval.append("ERASE ")
	ptr += 1
	return ptr

def _14(stmt, vartbl, ptr, retval):
	retval.append("*ERR %d* %s " % (ord(stmt[ptr+1]),stmt[ptr+2:]))
	ptr += 2 + len(retval[-1])
	return ptr

def _15(stmt, vartbl, ptr, retval):
	retval.append("ESCAPE")
	ptr += 1
	return ptr

def _16(stmt, vartbl, ptr, retval):
	retval.append("EXECUTE ")
	ptr += 1
	return ptr

def _17(stmt, vartbl, ptr, retval):
	retval.append("EXIT ")
	ptr += 1
	return ptr

def _18(stmt, vartbl, ptr, retval):
	retval.append("EXITTO ")
	ptr += 1
	return ptr

def _19(stmt, vartbl, ptr, retval):
	retval.append("EXTRACT ")
	ptr += 1
	return ptr

def _1A(stmt, vartbl, ptr, retval):
	retval.append("FILE ")
	ptr += 1
	return ptr

def _1B(stmt, vartbl, ptr, retval):
	retval.append("FIND ")
	ptr += 1
	return ptr

def _1C(stmt, vartbl, ptr, retval):
	retval.append("FLOATINGPOINT")
	ptr += 1
	return ptr

def _1D(stmt, vartbl, ptr, retval):
	retval.append("FOR ")
	ptr += 1
	return ptr

def _1E(stmt, vartbl, ptr, retval):
	retval.append("GOSUB ")
	ptr += 1
	ptr = _F6(stmt, vartbl, ptr, retval)
	return ptr

def _1F(stmt, vartbl, ptr, retval):
	retval.append("GOTO ")
	ptr += 1
	ptr = _F6(stmt, vartbl, ptr, retval)
	return ptr

def _20(stmt, vartbl, ptr, retval):
	retval.append("IF ")
	ptr += 1
	return ptr

def _21(stmt, vartbl, ptr, retval):
	retval.append("INDEXED ")
	ptr += 1
	return ptr

def _22(stmt, vartbl, ptr, retval):
	retval.append("INPUT ")
	ptr += 1
	return ptr

def _23(stmt, vartbl, ptr, retval):
	retval.append("IOLIST ")
	ptr += 1
	#ptr = _F6(stmt, vartbl, ptr, retval)
	return ptr

def _24(stmt, vartbl, ptr, retval):
	retval.append("LET ")
	ptr += 1
	return ptr

def _25(stmt, vartbl, ptr, retval):
	retval.append("LIST ")
	ptr += 1
	return ptr

def _26(stmt, vartbl, ptr, retval):
	retval.append("LOAD ")
	ptr += 1
	return ptr

def _27(stmt, vartbl, ptr, retval):
	retval.append("LOCK ")
	ptr += 1
	return ptr

def _28(stmt, vartbl, ptr, retval):
	retval.append("MERGE ")
	ptr += 1
	return ptr

def _29(stmt, vartbl, ptr, retval):
	retval.append("MKDIR ")
	ptr += 1
	return ptr

def _2A(stmt, vartbl, ptr, retval):
	retval.append("NEXT ")
	ptr += 1
	return ptr

def _2B(stmt, vartbl, ptr, retval):
	retval.append("ON ")
	ptr += 1
	return ptr

def _2C(stmt, vartbl, ptr, retval):
	retval.append("OPEN ")
	ptr += 1
	return ptr

def _2D(stmt, vartbl, ptr, retval):
	retval.append("PRECISION ")
	ptr += 1
	return ptr

def _2E(stmt, vartbl, ptr, retval):
	retval.append("PREFIX ")
	ptr += 1
	return ptr

def _2F(stmt, vartbl, ptr, retval):
	retval.append("PRINT ")
	ptr += 1
	return ptr

def _30(stmt, vartbl, ptr, retval):
	retval.append("PROGRAM ")
	ptr += 1
	return ptr

def _31(stmt, vartbl, ptr, retval):
	retval.append("READ ")
	ptr += 1
	return ptr

def _32(stmt, vartbl, ptr, retval):
	retval.append("RELEASE ")
	ptr += 1
	return ptr

def _33(stmt, vartbl, ptr, retval):
	retval.append("REM ")
	ptr += 1
	retval.append(stmt[ptr:])
	ptr += len(retval[-1])
	return ptr

def _34(stmt, vartbl, ptr, retval):
	retval.append("REMOVE ")
	ptr += 1
	return ptr

def _35(stmt, vartbl, ptr, retval):
	retval.append("RENAME ")
	ptr += 1
	return ptr

def _36(stmt, vartbl, ptr, retval):
	retval.append("RESERVE ")
	ptr += 1
	return ptr

def _37(stmt, vartbl, ptr, retval):
	retval.append("RESET")
	ptr += 1
	return ptr

def _38(stmt, vartbl, ptr, retval):
	retval.append("RETURN ")
	ptr += 1
	return ptr

def _39(stmt, vartbl, ptr, retval):
	retval.append("RETRY")
	ptr += 1
	return ptr

def _3A(stmt, vartbl, ptr, retval):
	retval.append("RMDIR ")
	ptr += 1
	return ptr

def _3B(stmt, vartbl, ptr, retval):
	retval.append("RUN ")
	ptr += 1
	return ptr

def _3C(stmt, vartbl, ptr, retval):
	retval.append("SAVE ")
	ptr += 1
	return ptr

def _3D(stmt, vartbl, ptr, retval):
	retval.append("SERIAL ")
	ptr += 1
	return ptr

def _3E(stmt, vartbl, ptr, retval):
	retval.append("SETDRIVE ")
	ptr += 1
	return ptr

def _3F(stmt, vartbl, ptr, retval):
	retval.append("SETDAY ")
	ptr += 1
	return ptr

def _40(stmt, vartbl, ptr, retval):
	retval.append("SETERR ")
	ptr += 1
	ptr = _F6(stmt, vartbl, ptr, retval)
	return ptr

def _41(stmt, vartbl, ptr, retval):
	retval.append("SETESC ")
	ptr += 1
	ptr = _F6(stmt, vartbl, ptr, retval)
	return ptr

def _42(stmt, vartbl, ptr, retval):
	retval.append("SETTIME ")
	ptr += 1
	return ptr

def _43(stmt, vartbl, ptr, retval):
	retval.append("SETTRACE ")
	ptr += 1
	return ptr

def _44(stmt, vartbl, ptr, retval):
	retval.append("SORT ")
	ptr += 1
	return ptr

def _46(stmt, vartbl, ptr, retval):
	retval.append("START ")
	ptr += 1
	return ptr

def _47(stmt, vartbl, ptr, retval):
	retval.append("STOP")
	ptr += 1
	return ptr

def _48(stmt, vartbl, ptr, retval):
	retval.append("STRING ")
	ptr += 1
	return ptr

def _49(stmt, vartbl, ptr, retval):
	retval.append("TABLE ")
	ptr += 1
	for i in stmt[ptr:]:
		retval.append('%s ' % hta(i))
	ptr = len(stmt) + 1
	return ptr

def _4A(stmt, vartbl, ptr, retval):
	retval.append("UNLOCK ")
	ptr += 1
	return ptr

def _4B(stmt, vartbl, ptr, retval):
	retval.append("WAIT ")
	ptr += 1
	return ptr

def _4C(stmt, vartbl, ptr, retval):
	retval.append("WRITE ")
	ptr += 1
	return ptr

def _4D(stmt, vartbl, ptr, retval):
	retval.append("SAVEP ")
	ptr += 1
	return ptr

def _4E(stmt, vartbl, ptr, retval):
	retval.append("SETOPTS ")
	ptr += 1
	return ptr

def _4F(stmt, vartbl, ptr, retval):
	retval.append("DATA ")
	ptr += 1
	return ptr

def _50(stmt, vartbl, ptr, retval):
	retval.append("RESTORE ")
	ptr += 1
	return ptr

def _51(stmt, vartbl, ptr, retval):
	retval.append("DREAD ")
	ptr += 1
	return ptr

def _52(stmt, vartbl, ptr, retval):
	retval.append("MKEYED ")
	ptr += 1
	return ptr

def _53(stmt, vartbl, ptr, retval):
	retval.append("WHILE ")
	ptr += 1
	return ptr

def _54(stmt, vartbl, ptr, retval):
	retval.append("WEND")
	ptr += 1
	return ptr

def _56(stmt, vartbl, ptr, retval):
	retval.append("FIELD ")
	ptr += 1
	return ptr

def _57(stmt, vartbl, ptr, retval):
	retval.append("INPUTE ")
	ptr += 1
	return ptr

def _58(stmt, vartbl, ptr, retval):
	retval.append("BACKGROUND ")
	ptr += 1
	return ptr

def _59(stmt, vartbl, ptr, retval):
	retval.append("INITFILE ")
	ptr += 1
	return ptr

def _5A(stmt, vartbl, ptr, retval):
	retval.append("REPEAT")
	ptr += 1
	return ptr

def _5B(stmt, vartbl, ptr, retval):
	retval.append("UNTIL ")
	ptr += 1
	return ptr

def _5C(stmt, vartbl, ptr, retval):
	retval.append("INPUTN ")
	ptr += 1
	return ptr

def _5D(stmt, vartbl, ptr, retval):
	retval.append("FNEND")
	ptr += 1
	return ptr

def _5E(stmt, vartbl, ptr, retval):
	retval.append("FNERR ")
	ptr += 1
	return ptr

def _5F(stmt, vartbl, ptr, retval):
	retval.append("SELECT ")
	ptr += 1
	return ptr

def _60(stmt, vartbl, ptr, retval):
	retval.append("CISAM ")
	ptr += 1
	return ptr

def _61(stmt, vartbl, ptr, retval):
	retval.append("SQLOPEN ")
	ptr += 1
	return ptr

def _62(stmt, vartbl, ptr, retval):
	retval.append("SQLCLOSE ")
	ptr += 1
	return ptr

def _63(stmt, vartbl, ptr, retval):
	retval.append("SQLPREP ")
	ptr += 1
	return ptr

def _64(stmt, vartbl, ptr, retval):
	retval.append("SQLEXEC ")
	ptr += 1
	return ptr

def _65(stmt, vartbl, ptr, retval):
	retval.append("SQLSET ")
	ptr += 1
	return ptr

def _66(stmt, vartbl, ptr, retval):
	retval.append("SWITCH ")
	ptr += 1
	return ptr

def _67(stmt, vartbl, ptr, retval):
	retval.append("CASE ")
	ptr += 1
	return ptr

def _68(stmt, vartbl, ptr, retval):
	retval.append("DEFAULT")
	ptr += 1
	return ptr

def _69(stmt, vartbl, ptr, retval):
	retval.append("SWEND")
	ptr += 1
	return ptr

def _6A(stmt, vartbl, ptr, retval):
	retval.append("BREAK")
	ptr += 1
	return ptr

def _6B(stmt, vartbl, ptr, retval):
	retval.append("CONTINUE")
	ptr += 1
	return ptr

def _6C(stmt, vartbl, ptr, retval):
	retval.append("FILEOPT ")
	ptr += 1
	return ptr

def _6D(stmt, vartbl, ptr, retval):
	retval.append("CHANOPT ")
	ptr += 1
	return ptr

def _6E(stmt, vartbl, ptr, retval):
	retval.append("RESCLOSE ")
	ptr += 1
	return ptr

def _6F(stmt, vartbl, ptr, retval):
	retval.append("CLIPCLEAR")
	ptr += 1
	return ptr

def _70(stmt, vartbl, ptr, retval):
	retval.append("CLIPFROMFILE ")
	ptr += 1
	return ptr

def _71(stmt, vartbl, ptr, retval):
	retval.append("CLIPFROMSTR ")
	ptr += 1
	return ptr

def _72(stmt, vartbl, ptr, retval):
	retval.append("CLIPLOCK")
	ptr += 1
	return ptr

def _73(stmt, vartbl, ptr, retval):
	retval.append("CLIPTOFILE ")
	ptr += 1
	return ptr

def _74(stmt, vartbl, ptr, retval):
	retval.append("CLIPUNLOCK")
	ptr += 1
	return ptr

def _75(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _76(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _77(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _78(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _79(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _7A(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _7B(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _7C(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _7D(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _7E(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _7F(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _80(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _81(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _82(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _83(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _84(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _85(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _86(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _87(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _88(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _89(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _8A(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _8B(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _8C(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _8D(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _8E(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _8F(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _90(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _91(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _92(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _93(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _94(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _95(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _96(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _97(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _98(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _99(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _9A(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _9B(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _9C(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _9D(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _9E(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _9F(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _A0(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _A1(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _A2(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _A3(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _A4(stmt, vartbl, ptr, retval):
	retval.append("FROM ")
	ptr += 1
	return ptr

def _A5(stmt, vartbl, ptr, retval):
	retval.append("WHERE ")
	ptr += 1
	return ptr

def _A6(stmt, vartbl, ptr, retval):
	retval.append("SORTBY ")
	ptr += 1
	return ptr

def _A7(stmt, vartbl, ptr, retval):
	retval.append("LIMIT ")
	ptr += 1
	return ptr

def _A8(stmt, vartbl, ptr, retval):
	# get function
	ptr += 1
	op = eval('_A8%02X' % ord(stmt[ptr]))
	ptr = op(stmt, vartbl, ptr, retval)
	return ptr

def _A9(stmt, vartbl, ptr, retval):
	# get function
	ptr += 1
	op = eval('_A9%02X' % ord(stmt[ptr]))
	ptr = op(stmt, vartbl, ptr, retval)
	return ptr

def _AA(stmt, vartbl, ptr, retval):
	# functbl lookup - numeric
	ptr += 1
	### funcseq = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	funcseq = ord(stmt[ptr+1]) # this assumes less than 256 func defs
	ptr += 2
	vartype , varname = vartbl[-1][funcseq][:2]
	# types: 0:string, 1:numeric, 4:numeric_array, -127:integer function, -126:string function
	retval.append('FN%s' % (varname))
	return ptr

def _AB(stmt, vartbl, ptr, retval):
	# functbl lookup - string
	ptr += 1
	### funcseq = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	funcseq = ord(stmt[ptr+1]) # this assumes less than 256 func defs
	ptr += 2
	vartype , varname = vartbl[-1][funcseq][:2]
	# types: 0:string, 1:numeric, 4:numeric_array, -127:integer function, -126:string function
	retval.append('FN%s$' % (varname))
	return ptr

def _AC(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _AD(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _AE(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _AF(stmt, vartbl, ptr, retval):
	retval.append(",DOM=")
	ptr += 1
	return ptr

def _B0(stmt, vartbl, ptr, retval):
	retval.append(",END=")
	ptr += 1
	return ptr

def _B1(stmt, vartbl, ptr, retval):
	retval.append(",ERR=")
	ptr += 1
	return ptr

def _B2(stmt, vartbl, ptr, retval):
	retval.append(",IND=")
	ptr += 1
	return ptr

def _B3(stmt, vartbl, ptr, retval):
	retval.append("IOL=")
	ptr += 1
	return ptr

def _B4(stmt, vartbl, ptr, retval):
	retval.append(",ISZ=")
	ptr += 1
	return ptr

def _B5(stmt, vartbl, ptr, retval):
	retval.append(",KEY=")
	ptr += 1
	return ptr

def _B6(stmt, vartbl, ptr, retval):
	retval.append("LEN=")
	ptr += 1
	return ptr

def _B7(stmt, vartbl, ptr, retval):
	retval.append(",MODE=")
	ptr += 1
	return ptr

def _B8(stmt, vartbl, ptr, retval):
	retval.append(",SIZ=")
	ptr += 1
	return ptr

def _B9(stmt, vartbl, ptr, retval):
	retval.append(",TBL=")
	ptr += 1
	return ptr

def _BA(stmt, vartbl, ptr, retval):
	retval.append(",TIM=")
	ptr += 1
	return ptr

def _BB(stmt, vartbl, ptr, retval):
	retval.append(",LEN=")
	ptr += 1
	return ptr

def _BC(stmt, vartbl, ptr, retval):
	retval.append(",KNUM=")
	ptr += 1
	return ptr

def _BD(stmt, vartbl, ptr, retval):
	retval.append(",DIR=")
	ptr += 1
	return ptr

def _BE(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _BF(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _C0(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _C1(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _C2(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _C4(stmt, vartbl, ptr, retval):
	# vartbl lookup - numeric
	ptr += 1
	varseq = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	ptr += 2
	vartype , varname = vartbl[varseq][:2]
	# types: 0:string, 1:numeric, 4:numeric_array, -127:integer function, -126:string function
	retval.append(varname)
	return ptr

def _C5(stmt, vartbl, ptr, retval):
	# vartbl lookup - string
	ptr += 1
	varseq = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	ptr += 2
	vartype , varname = vartbl[varseq][:2]
	# types: 0:string, 1:numeric, 4:numeric_array, -127:integer function, -126:string function
	retval.append('%s$' % varname)
	return ptr

def _C6(stmt, vartbl, ptr, retval):
	# return next int
	ptr += 1
	retval.append('%d' % ord(stmt[ptr]))
	ptr += 1
	return ptr

def _C7(stmt, vartbl, ptr, retval):
	# return 2-byte number
	ptr += 1
	number = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	ptr += 2
	retval.append('%d' % number)
	return ptr

def _C8(stmt, vartbl, ptr, retval):
	# return 3-byte number
	ptr += 1
	number = 256*256*ord(stmt[ptr]) + 256*ord(stmt[ptr+1]) + ord(stmt[ptr+2])
	ptr += 3
	retval.append('%d' % number)
	return ptr

def _C9(stmt, vartbl, ptr, retval):
	# return 4-byte number
	ptr += 1
	number = 256*256*256*ord(stmt[ptr]) + 256*256*ord(stmt[ptr+1]) + 256*ord(stmt[ptr+2]) + ord(stmt[ptr+3])
	ptr += 4
	retval.append('%d' % number)
	return ptr

def _CA(stmt, vartbl, ptr, retval):
	# return next decimal int
	ptr += 1
	postdec = '\x00\x4D\x4C\x4B\x4A\x49\x48'.index(stmt[ptr])
	ptr += 1
	mask = ".%" + '0%d' % postdec + "d"
	number = ord(stmt[ptr])
	predec = len('%d' % ( number / 10 ** postdec))
	if predec:
		mask = "%0" + '%d' % predec +"d" + mask
		number = (number / (10 ** postdec), number % 10 ** postdec)
	rv = mask % number
	if rv[0] == '0': rv = rv [1:]
	retval.append(rv)
	ptr += 1
	return ptr

def _CB(stmt, vartbl, ptr, retval):
	# return decimal 2-byte number
	# CB4C04AF = 11.99
	ptr += 1
	postdec = '\x00\x4D\x4C\x4B\x4A\x49\x48'.index(stmt[ptr])
	ptr += 1
	mask = ".%" + '0%d' % postdec + "d"
	number = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	ptr += 2
	predec = len('%d' % (number / 10 ** postdec))
	if predec:
		mask = "%0" + '%d' % predec +"d" + mask
		number = (number / (10 ** postdec), number % 10 ** postdec)
	rv = mask % number
	if rv[0] == '0': rv = rv [1:]
	retval.append(rv)
	return ptr

def _CC(stmt, vartbl, ptr, retval):
	# return decimal 3-byte number
	# CB4C04AF = 11.99
	ptr += 1
	postdec = '\x00\x4D\x4C\x4B\x4A\x49\x48'.index(stmt[ptr])
	ptr += 1
	mask = ".%" + '0%d' % postdec + "d"
	number = 1L*256*256*ord(stmt[ptr]) + 256*ord(stmt[ptr+1]) + ord(stmt[ptr+2])
	#number = 1L*256*256*256*ord(stmt[ptr]) + 1L*256*256*ord(stmt[ptr+1]) + 256*ord(stmt[ptr+2]) + ord(stmt[ptr+3])
	ptr += 3
	predec = len('%d' % (number / 10 ** postdec))
	if predec:
		mask = "%0" + '%d' % predec +"d" + mask
		number = (number / (10 ** postdec), number % 10 ** postdec)
	rv = mask % number
	if rv[0] == '0': rv = rv [1:]
	retval.append(rv)
	return ptr

def _CD(stmt, vartbl, ptr, retval):
	# return 5-byte number
	ptr += 1
	number = 1L*256*256*256*256*ord(stmt[ptr]) + 1L*256*256*256*ord(stmt[ptr+1]) + 256*256*ord(stmt[ptr+2]) + 256*ord(stmt[ptr+3]) + ord(stmt[ptr+4])
	#retval.append('(*%s*)' % hta(stmt[ptr:ptr+5]))
	ptr += 5
	retval.append('%d' % number)
	return ptr

def _CE(stmt, vartbl, ptr, retval):
	# return 6-byte number (* throw away first byte? *)
	ptr += 1
	number = 0L*256*256*256*256*256*ord(stmt[ptr]) + 1L*256*256*256*256*ord(stmt[ptr+1]) + 1L*256*256*256*ord(stmt[ptr+2]) + 256*256*ord(stmt[ptr+3]) + 256*ord(stmt[ptr+4]) + ord(stmt[ptr+5])
	#retval.append('(*%s*)' % hta(stmt[ptr:ptr+6]))
	ptr += 6
	retval.append('%d' % number)
	return ptr

def _D1(stmt, vartbl, ptr, retval):
	# string constant
	ptr += 1
	strlen = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	ptr += 2
	retval.append('"%s"' % stmt[ptr:ptr+strlen])
	ptr += strlen
	return ptr

def _D2(stmt, vartbl, ptr, retval):
	# hex constant
	ptr += 1
	strlen = 256*ord(stmt[ptr]) + ord(stmt[ptr+1])
	ptr += 2
	retval.append('$%s$' % hta(stmt[ptr:ptr+strlen]))
	ptr += strlen
	return ptr

def _D3(stmt, vartbl, ptr, retval):
	retval.append("(")
	ptr += 1
	return ptr

def _D4x(stmt, vartbl, ptr, retval):
	# 2 position mnemonic constant
	ptr += 1
	retval.append("'%s'" % stmt[ptr:ptr+2])
	ptr += 2
	return ptr

def _D4(stmt, vartbl, ptr, retval):
	# long mnemonic constant
	ptr += 1
	strlen = ord(stmt[ptr])
	if strlen > 16:
		strlen = 2
	else:
		ptr += 1
	retval.append("'%s'" % stmt[ptr:ptr+strlen])
	ptr += strlen
	return ptr

def _D5(stmt, vartbl, ptr, retval):
	retval.append("@")
	ptr += 1
	return ptr

def _D6(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _D7(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _D8(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _D9(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _DA(stmt, vartbl, ptr, retval):
	retval.append("-")
	ptr += 1
	return ptr

def _DB(stmt, vartbl, ptr, retval):
	retval.append("+")
	ptr += 1
	return ptr

def _DC(stmt, vartbl, ptr, retval):
	retval.append("+")
	ptr += 1
	return ptr

def _DD(stmt, vartbl, ptr, retval):
	retval.append("-")
	ptr += 1
	return ptr

def _DE(stmt, vartbl, ptr, retval):
	retval.append("*")
	ptr += 1
	return ptr

def _DF(stmt, vartbl, ptr, retval):
	retval.append("/")
	ptr += 1
	return ptr

def _E0(stmt, vartbl, ptr, retval):
	retval.append("^")
	ptr += 1
	return ptr

def _E1(stmt, vartbl, ptr, retval):
	retval.append("=")
	ptr += 1
	return ptr

def _E2(stmt, vartbl, ptr, retval):
	retval.append("<>")
	ptr += 1
	return ptr

def _E3(stmt, vartbl, ptr, retval):
	retval.append("<")
	ptr += 1
	return ptr

def _E4(stmt, vartbl, ptr, retval):
	retval.append(">")
	ptr += 1
	return ptr

def _E5(stmt, vartbl, ptr, retval):
	retval.append("<=")
	ptr += 1
	return ptr

def _E6(stmt, vartbl, ptr, retval):
	retval.append(">=")
	ptr += 1
	return ptr

def _E7(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _E8(stmt, vartbl, ptr, retval):
	retval.append("EXCEPT ")
	ptr += 1
	return ptr

def _E9(stmt, vartbl, ptr, retval):
	retval.append("FI")
	ptr += 1
	return ptr

def _EA(stmt, vartbl, ptr, retval):
	# - start of sub-statement ?
	#retval.append("")
	ptr += 3
	return ptr

def _EB(stmt, vartbl, ptr, retval):
	retval.append(" AND ")
	ptr += 1
	return ptr

def _EC(stmt, vartbl, ptr, retval):
	retval.append(" OR ")
	ptr += 1
	return ptr

def _ED(stmt, vartbl, ptr, retval):
	retval.append("[")
	ptr += 1
	return ptr

def _EE(stmt, vartbl, ptr, retval):
	retval.append("]")
	ptr += 1
	return ptr

def _EF(stmt, vartbl, ptr, retval):
	retval.append("[ALL]")
	ptr += 1
	return ptr

def _F0(stmt, vartbl, ptr, retval):
	retval.append("=")
	ptr += 1
	return ptr

def _F2(stmt, vartbl, ptr, retval):
	retval.append(",")
	ptr += 1
	return ptr

def _F3(stmt, vartbl, ptr, retval):
	retval.append("; ")
	ptr += 1
	return ptr

def _F4(stmt, vartbl, ptr, retval):
	if len(retval):
		if retval[-1][-1] == ' ':
			retval.append("ELSE ")
	else:
		retval.append(" ELSE ")
	ptr += 1
	return ptr

def _F5(stmt, vartbl, ptr, retval):
	retval.append("*")
	ptr += 1
	return ptr

def _F6(stmt, vartbl, ptr, retval):
	#print ptr, stmt, repr(stmt)
	if stmt[ptr] == '\xF6':
		stmntno = "%05d" % (ord(stmt[ptr+1])*256 + ord(stmt[ptr+2]))
		ptr += 3
	else:
		stmntno = "%05d" % (ord(stmt[ptr+1]))
		ptr += 2
	if stmntno[0] == '0': stmntno = stmntno[1:]
	if stmntno == '0000': stmntno = '0'
	retval.append(stmntno)
	return ptr

def _F7(stmt, vartbl, ptr, retval):
	retval.append(":")
	ptr += 1
	return ptr

def _F8(stmt, vartbl, ptr, retval):
	retval.append(" GOSUB ")
	ptr += 1
	ptr = _F6(stmt, vartbl, ptr, retval)
	return ptr

def _F9(stmt, vartbl, ptr, retval):
	retval.append(" GOTO ")
	ptr += 1
	ptr = _F6(stmt, vartbl, ptr, retval)
	return ptr

def _FA(stmt, vartbl, ptr, retval):
	retval.append("RECORD")
	ptr += 1
	return ptr

def _FB(stmt, vartbl, ptr, retval):
	retval.append(")")
	ptr += 1
	return ptr

def _FC(stmt, vartbl, ptr, retval):
	retval.append(" STEP ")
	ptr += 1
	return ptr

def _FD(stmt, vartbl, ptr, retval):
	retval.append(" THEN ")
	ptr += 1
	return ptr

def _FE(stmt, vartbl, ptr, retval):
	retval.append(" TO ")
	ptr += 1
	return ptr

def _FF(stmt, vartbl, ptr, retval):
	retval.append(":")
	ptr += 1
	return ptr

def _A800(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _A801(stmt, vartbl, ptr, retval):
	retval.append("ABS")
	ptr += 1
	return ptr

def _A802(stmt, vartbl, ptr, retval):
	retval.append("ARGC")
	ptr += 1
	return ptr

def _A803(stmt, vartbl, ptr, retval):
	retval.append("ASC")
	ptr += 1
	return ptr

def _A804(stmt, vartbl, ptr, retval):
	retval.append("ATN")
	ptr += 1
	return ptr

def _A805(stmt, vartbl, ptr, retval):
	retval.append("BSZ")
	ptr += 1
	return ptr

def _A806(stmt, vartbl, ptr, retval):
	retval.append("COS")
	ptr += 1
	return ptr

def _A807(stmt, vartbl, ptr, retval):
	retval.append("CTL")
	ptr += 1
	return ptr

def _A808(stmt, vartbl, ptr, retval):
	retval.append("DEC")
	ptr += 1
	return ptr

def _A809(stmt, vartbl, ptr, retval):
	retval.append("DSZ")
	ptr += 1
	return ptr

def _A80A(stmt, vartbl, ptr, retval):
	retval.append("EPT")
	ptr += 1
	return ptr

def _A80B(stmt, vartbl, ptr, retval):
	retval.append("ERR")
	ptr += 1
	return ptr

def _A80C(stmt, vartbl, ptr, retval):
	retval.append("FDEC")
	ptr += 1
	return ptr

def _A80D(stmt, vartbl, ptr, retval):
	retval.append("FPT")
	ptr += 1
	return ptr

def _A80E(stmt, vartbl, ptr, retval):
	retval.append("HSA")
	ptr += 1
	return ptr

def _A80F(stmt, vartbl, ptr, retval):
	retval.append("IND")
	ptr += 1
	return ptr

def _A810(stmt, vartbl, ptr, retval):
	retval.append("INT")
	ptr += 1
	return ptr

def _A811(stmt, vartbl, ptr, retval):
	retval.append("JUL")
	ptr += 1
	return ptr

def _A812(stmt, vartbl, ptr, retval):
	retval.append("LEN")
	ptr += 1
	return ptr

def _A813(stmt, vartbl, ptr, retval):
	retval.append("LOG")
	ptr += 1
	return ptr

def _A814(stmt, vartbl, ptr, retval):
	retval.append("MASK")
	ptr += 1
	return ptr

def _A815(stmt, vartbl, ptr, retval):
	retval.append("MAX")
	ptr += 1
	return ptr

def _A816(stmt, vartbl, ptr, retval):
	retval.append("MIN")
	ptr += 1
	return ptr

def _A817(stmt, vartbl, ptr, retval):
	retval.append("MOD")
	ptr += 1
	return ptr

def _A818(stmt, vartbl, ptr, retval):
	retval.append("NFIELD")
	ptr += 1
	return ptr

def _A819(stmt, vartbl, ptr, retval):
	retval.append("NUM")
	ptr += 1
	return ptr

def _A81A(stmt, vartbl, ptr, retval):
	retval.append("POS")
	ptr += 1
	return ptr

def _A81B(stmt, vartbl, ptr, retval):
	retval.append("PSZ")
	ptr += 1
	return ptr

def _A81C(stmt, vartbl, ptr, retval):
	retval.append("RND(")
	ptr += 1
	return ptr

def _A81D(stmt, vartbl, ptr, retval):
	retval.append("SCALL")
	ptr += 1
	return ptr

def _A81E(stmt, vartbl, ptr, retval):
	retval.append("SGN")
	ptr += 1
	return ptr

def _A81F(stmt, vartbl, ptr, retval):
	retval.append("SIN")
	ptr += 1
	return ptr

def _A820(stmt, vartbl, ptr, retval):
	retval.append("SQR")
	ptr += 1
	return ptr

def _A821(stmt, vartbl, ptr, retval):
	retval.append("SSZ")
	ptr += 1
	return ptr

def _A822(stmt, vartbl, ptr, retval):
	retval.append("TCB")
	ptr += 1
	return ptr

def _A823(stmt, vartbl, ptr, retval):
	retval.append("TIM")
	ptr += 1
	return ptr

def _A824(stmt, vartbl, ptr, retval):
	retval.append("UNT")
	ptr += 1
	return ptr

def _A825(stmt, vartbl, ptr, retval):
	retval.append("UPK")
	ptr += 1
	return ptr

def _A826(stmt, vartbl, ptr, retval):
	retval.append("ROUND")
	ptr += 1
	return ptr

def _A827(stmt, vartbl, ptr, retval):
	retval.append("NEVAL")
	ptr += 1
	return ptr

def _A828(stmt, vartbl, ptr, retval):
	retval.append("!")
	ptr += 1
	return ptr

def _A829(stmt, vartbl, ptr, retval):
	retval.append("SQLUNT")
	ptr += 1
	return ptr

def _A82A(stmt, vartbl, ptr, retval):
	retval.append("RESOPEN")
	ptr += 1
	return ptr

def _A82B(stmt, vartbl, ptr, retval):
	retval.append("MSGBOX")
	ptr += 1
	return ptr

def _A82C(stmt, vartbl, ptr, retval):
	retval.append("CLIPISFORMAT")
	ptr += 1
	return ptr

def _A82D(stmt, vartbl, ptr, retval):
	retval.append("CLIPREGFORMAT")
	ptr += 1
	return ptr

def _A82E(stmt, vartbl, ptr, retval):
	retval.append("CVT")
	ptr += 1
	return ptr

def _A82F(stmt, vartbl, ptr, retval):
	retval.append("WINFIRST")
	ptr += 1
	return ptr

def _A830(stmt, vartbl, ptr, retval):
	retval.append("WINNEXT")
	ptr += 1
	return ptr

def _A835(stmt, vartbl, ptr, retval):
	retval.append("AND")
	ptr += 1
	return ptr

def _A836(stmt, vartbl, ptr, retval):
	retval.append("ARGV")
	ptr += 1
	return ptr

def _A837(stmt, vartbl, ptr, retval):
	retval.append("ATH(")
	ptr += 1
	return ptr

def _A838(stmt, vartbl, ptr, retval):
	retval.append("BIN(")
	ptr += 1
	return ptr

def _A839(stmt, vartbl, ptr, retval):
	retval.append("CHR(")
	ptr += 1
	return ptr

def _A83A(stmt, vartbl, ptr, retval):
	retval.append("CPL(")
	ptr += 1
	return ptr

def _A83B(stmt, vartbl, ptr, retval):
	retval.append("CRC(")
	ptr += 1
	return ptr

def _A83C(stmt, vartbl, ptr, retval):
	retval.append("CVS(")
	ptr += 1
	return ptr

def _A83D(stmt, vartbl, ptr, retval):
	retval.append("DATE")
	ptr += 1
	return ptr

def _A83E(stmt, vartbl, ptr, retval):
	retval.append("DAY")
	ptr += 1
	return ptr

def _A83F(stmt, vartbl, ptr, retval):
	retval.append("DIR")
	ptr += 1
	return ptr

def _A840(stmt, vartbl, ptr, retval):
	retval.append("DSK")
	ptr += 1
	return ptr

def _A841(stmt, vartbl, ptr, retval):
	retval.append("FATTR")
	ptr += 1
	return ptr

def _A842(stmt, vartbl, ptr, retval):
	retval.append("FBIN")
	ptr += 1
	return ptr

def _A843(stmt, vartbl, ptr, retval):
	retval.append("FID(")
	ptr += 1
	return ptr

def _A844(stmt, vartbl, ptr, retval):
	retval.append("FIELD")
	ptr += 1
	return ptr

def _A845(stmt, vartbl, ptr, retval):
	retval.append("FILL")
	ptr += 1
	return ptr

def _A846(stmt, vartbl, ptr, retval):
	retval.append("FIN(")
	ptr += 1
	return ptr

def _A847(stmt, vartbl, ptr, retval):
	retval.append("GAP(")
	ptr += 1
	return ptr

def _A848(stmt, vartbl, ptr, retval):
	retval.append("HSH(")
	ptr += 1
	return ptr

def _A849(stmt, vartbl, ptr, retval):
	retval.append("HTA(")
	ptr += 1
	return ptr

def _A84A(stmt, vartbl, ptr, retval):
	retval.append("INFO")
	ptr += 1
	return ptr

def _A84B(stmt, vartbl, ptr, retval):
	retval.append("IOR")
	ptr += 1
	return ptr

def _A84C(stmt, vartbl, ptr, retval):
	retval.append("KEY(")
	ptr += 1
	return ptr

def _A84D(stmt, vartbl, ptr, retval):
	retval.append("KEYF(")
	ptr += 1
	return ptr

def _A84E(stmt, vartbl, ptr, retval):
	retval.append("KEYL(")
	ptr += 1
	return ptr

def _A84F(stmt, vartbl, ptr, retval):
	retval.append("KEYN(")
	ptr += 1
	return ptr

def _A850(stmt, vartbl, ptr, retval):
	retval.append("KEYP(")
	ptr += 1
	return ptr

def _A851(stmt, vartbl, ptr, retval):
	retval.append("LRC(")
	ptr += 1
	return ptr

def _A852(stmt, vartbl, ptr, retval):
	retval.append("LST(")
	ptr += 1
	return ptr

def _A853(stmt, vartbl, ptr, retval):
	retval.append("NOT")
	ptr += 1
	return ptr

def _A854(stmt, vartbl, ptr, retval):
	retval.append("OPTS")
	ptr += 1
	return ptr

def _A855(stmt, vartbl, ptr, retval):
	retval.append("PCK")
	ptr += 1
	return ptr

def _A856(stmt, vartbl, ptr, retval):
	retval.append("PFX")
	ptr += 1
	return ptr

def _A857(stmt, vartbl, ptr, retval):
	retval.append("PGM(")
	ptr += 1
	return ptr

def _A858(stmt, vartbl, ptr, retval):
	retval.append("PUB")
	ptr += 1
	return ptr

def _A859(stmt, vartbl, ptr, retval):
	retval.append("REV")
	ptr += 1
	return ptr

def _A85A(stmt, vartbl, ptr, retval):
	retval.append("SSN")
	ptr += 1
	return ptr

def _A85B(stmt, vartbl, ptr, retval):
	retval.append("STBL")
	ptr += 1
	return ptr

def _A85C(stmt, vartbl, ptr, retval):
	retval.append("STR(")
	ptr += 1
	return ptr

def _A85D(stmt, vartbl, ptr, retval):
	retval.append("SWAP")
	ptr += 1
	return ptr

def _A85E(stmt, vartbl, ptr, retval):
	retval.append("SYS")
	ptr += 1
	return ptr

def _A85F(stmt, vartbl, ptr, retval):
	retval.append("TBL")
	ptr += 1
	return ptr

def _A860(stmt, vartbl, ptr, retval):
	retval.append("TSK(")
	ptr += 1
	return ptr

def _A861(stmt, vartbl, ptr, retval):
	retval.append("XOR")
	ptr += 1
	return ptr

def _A862(stmt, vartbl, ptr, retval):
	retval.append("CHN")
	ptr += 1
	return ptr

def _A863(stmt, vartbl, ptr, retval):
	retval.append("KGEN")
	ptr += 1
	return ptr

def _A864(stmt, vartbl, ptr, retval):
	retval.append("SSORT")
	ptr += 1
	return ptr

def _A865(stmt, vartbl, ptr, retval):
	retval.append("ADJN")
	ptr += 1
	return ptr

def _A866(stmt, vartbl, ptr, retval):
	retval.append("SQLLIST")
	ptr += 1
	return ptr

def _A867(stmt, vartbl, ptr, retval):
	retval.append("SQLTABLES")
	ptr += 1
	return ptr

def _A868(stmt, vartbl, ptr, retval):
	retval.append("SQLTMPL")
	ptr += 1
	return ptr

def _A869(stmt, vartbl, ptr, retval):
	retval.append("SQLERR")
	ptr += 1
	return ptr

def _A86A(stmt, vartbl, ptr, retval):
	retval.append("SQLFETCH")
	ptr += 1
	return ptr

def _A900(stmt, vartbl, ptr, retval):
	retval.append("")
	ptr += 1
	return ptr

def _A901(stmt, vartbl, ptr, retval):
	retval.append("AND")
	ptr += 1
	return ptr

def _A902(stmt, vartbl, ptr, retval):
	retval.append("ARGV")
	ptr += 1
	return ptr

def _A903(stmt, vartbl, ptr, retval):
	retval.append("ATH")
	ptr += 1
	return ptr

def _A904(stmt, vartbl, ptr, retval):
	retval.append("BIN")
	ptr += 1
	return ptr

def _A905(stmt, vartbl, ptr, retval):
	retval.append("CHR")
	ptr += 1
	return ptr

def _A906(stmt, vartbl, ptr, retval):
	retval.append("CPL")
	ptr += 1
	return ptr

def _A907(stmt, vartbl, ptr, retval):
	retval.append("CRC")
	ptr += 1
	return ptr

def _A908(stmt, vartbl, ptr, retval):
	retval.append("CVS")
	ptr += 1
	return ptr

def _A909(stmt, vartbl, ptr, retval):
	retval.append("DATE")
	ptr += 1
	return ptr

def _A90A(stmt, vartbl, ptr, retval):
	retval.append("DAY")
	ptr += 1
	return ptr

def _A90B(stmt, vartbl, ptr, retval):
	retval.append("DIR")
	ptr += 1
	return ptr

def _A90C(stmt, vartbl, ptr, retval):
	retval.append("DSK")
	ptr += 1
	return ptr

def _A90D(stmt, vartbl, ptr, retval):
	retval.append("FATTR")
	ptr += 1
	return ptr

def _A90E(stmt, vartbl, ptr, retval):
	retval.append("FBIN")
	ptr += 1
	return ptr

def _A90F(stmt, vartbl, ptr, retval):
	retval.append("FID")
	ptr += 1
	return ptr

def _A910(stmt, vartbl, ptr, retval):
	retval.append("FIELD")
	ptr += 1
	return ptr

def _A911(stmt, vartbl, ptr, retval):
	retval.append("FILL")
	ptr += 1
	return ptr

def _A912(stmt, vartbl, ptr, retval):
	retval.append("FIN")
	ptr += 1
	return ptr

def _A913(stmt, vartbl, ptr, retval):
	retval.append("GAP( ")
	ptr += 1
	return ptr

def _A914(stmt, vartbl, ptr, retval):
	retval.append("HSH")
	ptr += 1
	return ptr

def _A915(stmt, vartbl, ptr, retval):
	retval.append("HTA")
	ptr += 1
	return ptr

def _A916(stmt, vartbl, ptr, retval):
	retval.append("INFO")
	ptr += 1
	return ptr

def _A917(stmt, vartbl, ptr, retval):
	retval.append("IOR")
	ptr += 1
	return ptr

def _A918(stmt, vartbl, ptr, retval):
	retval.append("KEY")
	ptr += 1
	return ptr

def _A919(stmt, vartbl, ptr, retval):
	retval.append("KEYF")
	ptr += 1
	return ptr

def _A91A(stmt, vartbl, ptr, retval):
	retval.append("KEYL")
	ptr += 1
	return ptr

def _A91B(stmt, vartbl, ptr, retval):
	retval.append("KEYN")
	ptr += 1
	return ptr

def _A91C(stmt, vartbl, ptr, retval):
	retval.append("KEYP")
	ptr += 1
	return ptr

def _A91D(stmt, vartbl, ptr, retval):
	retval.append("LRC")
	ptr += 1
	return ptr

def _A91E(stmt, vartbl, ptr, retval):
	retval.append("LST")
	ptr += 1
	return ptr

def _A91F(stmt, vartbl, ptr, retval):
	retval.append("NOT")
	ptr += 1
	return ptr

def _A920(stmt, vartbl, ptr, retval):
	retval.append("OPTS")
	ptr += 1
	return ptr

def _A921(stmt, vartbl, ptr, retval):
	retval.append("PCK")
	ptr += 1
	return ptr

def _A922(stmt, vartbl, ptr, retval):
	retval.append("PFX")
	ptr += 1
	return ptr

def _A923(stmt, vartbl, ptr, retval):
	retval.append("PGM")
	ptr += 1
	return ptr

def _A924(stmt, vartbl, ptr, retval):
	retval.append("PUB")
	ptr += 1
	return ptr

def _A925(stmt, vartbl, ptr, retval):
	retval.append("REV")
	ptr += 1
	return ptr

def _A926(stmt, vartbl, ptr, retval):
	retval.append("SSN")
	ptr += 1
	return ptr

def _A927(stmt, vartbl, ptr, retval):
	retval.append("STBL")
	ptr += 1
	return ptr

def _A928(stmt, vartbl, ptr, retval):
	retval.append("STR")
	ptr += 1
	return ptr

def _A929(stmt, vartbl, ptr, retval):
	retval.append("SWAP")
	ptr += 1
	return ptr

def _A92A(stmt, vartbl, ptr, retval):
	retval.append("SYS")
	ptr += 1
	return ptr

def _A92B(stmt, vartbl, ptr, retval):
	retval.append("TBL")
	ptr += 1
	return ptr

def _A92C(stmt, vartbl, ptr, retval):
	retval.append("TSK")
	ptr += 1
	return ptr

def _A92D(stmt, vartbl, ptr, retval):
	retval.append("XOR")
	ptr += 1
	return ptr

def _A92E(stmt, vartbl, ptr, retval):
	retval.append("CHN")
	ptr += 1
	return ptr

def _A92F(stmt, vartbl, ptr, retval):
	retval.append("KGEN")
	ptr += 1
	return ptr

def _A930(stmt, vartbl, ptr, retval):
	retval.append("SSORT")
	ptr += 1
	return ptr

def _A931(stmt, vartbl, ptr, retval):
	retval.append("ADJN")
	ptr += 1
	return ptr

def _A932(stmt, vartbl, ptr, retval):
	retval.append("SQLLIST")
	ptr += 1
	return ptr

def _A933(stmt, vartbl, ptr, retval):
	retval.append("SQLTABLES")
	ptr += 1
	return ptr

def _A934(stmt, vartbl, ptr, retval):
	retval.append("SQLTMPL")
	ptr += 1
	return ptr

def _A935(stmt, vartbl, ptr, retval):
	retval.append("SQLERR")
	ptr += 1
	return ptr

def _A936(stmt, vartbl, ptr, retval):
	retval.append("SQLFETCH")
	ptr += 1
	return ptr

def _A937(stmt, vartbl, ptr, retval):
	retval.append("FILEOPT")
	ptr += 1
	return ptr

def _A938(stmt, vartbl, ptr, retval):
	retval.append("CHANOPT")
	ptr += 1
	return ptr

def _A939(stmt, vartbl, ptr, retval):
	retval.append("SEVAL")
	ptr += 1
	return ptr


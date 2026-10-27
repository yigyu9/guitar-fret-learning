set pagination off
set print thread-events off
set confirm off
handle SIGFPE stop print pass
handle SIGPIPE nostop noprint pass
run
python
if gdb.selected_inferior().pid:
    signal_number = int(gdb.parse_and_eval("$_siginfo.si_signo"))
    for command in ["p $_siginfo", "info float", "p/x $fctrl", "p/x $fstat", "p/x $mxcsr", "p/x $rbp", "x/16hx $rsp+0x20", "info proc mappings", "thread apply all bt 30"]:
        try:
            gdb.execute(command)
        except gdb.error as error:
            gdb.write(str(error)+"\n")
    gdb.execute("continue")
    gdb.execute("quit %d" % (128+signal_number))
else:
    gdb.execute("quit %d" % int(gdb.parse_and_eval("$_exitcode")))
end

set pagination off
set print thread-events off
set confirm off
handle SIGFPE stop print nopass
run
python
if gdb.selected_inferior().pid:
    for command in ('p $_siginfo', 'bt 12', 'info registers fctrl fstat ftag mxcsr rbp rsp rip', 'x/hx $rsp+0x36', 'x/hx $rsp+0x40', 'x/12i $pc-24', 'frame 2', 'info args', 'frame 3', 'info args', 'p/x obj', 'x/3gx obj'):
        try:
            gdb.execute(command)
        except gdb.error as error:
            gdb.write(str(error)+'\n')
end
quit

set pagination off
set confirm off
set print thread-events off
set follow-fork-mode parent
set detach-on-fork on
handle SIGFPE stop print pass
handle SIGSEGV stop print pass
handle SIGABRT stop print pass
handle SIGBUS stop print pass
handle SIGILL stop print pass
handle SIGINT nostop noprint pass
handle SIGTERM nostop print pass
python
import gdb
import signal
transition_exit_code = None
transition_stop_signal = None
def transition_exited(event):
    global transition_exit_code
    transition_exit_code = getattr(event, 'exit_code', None)
def transition_stopped(event):
    global transition_stop_signal
    if isinstance(event, gdb.SignalEvent):
        transition_stop_signal = event.stop_signal
gdb.events.exited.connect(transition_exited)
gdb.events.stop.connect(transition_stopped)
end
run
python
inferior = gdb.selected_inferior()
if inferior.pid:
    gdb.write('\n=== FIRST FATAL STOP: '+str(transition_stop_signal)+'; NO CONTINUATION ===\n')
    for command in ['p $_siginfo', 'info all-registers', 'info float', 'p/x $rbp', 'p/x $rsp', 'x/16hx $rsp+0x20', 'p/x *(unsigned short*)($rsp+0x36)', 'x/16i $pc-24', 'disassemble /r format_float_short', 'bt full', 'thread apply all bt']:
        try:
            gdb.execute(command)
        except gdb.error as error:
            gdb.write('Diagnostic command error: '+str(error)+'\n')
    number = getattr(signal, transition_stop_signal, None) if transition_stop_signal else None
    result = 128+int(number) if number is not None else 1
else:
    result = int(transition_exit_code) if transition_exit_code is not None else 1
    gdb.write('\n=== INFERIOR EXITED: exit_code='+str(result)+'; PRODUCER RESULT REMAINS AUTHORITATIVE ===\n')
gdb.write('SUPERVISOR_EXIT_CODE='+str(result)+'\n')
gdb.execute('quit '+str(result))
end

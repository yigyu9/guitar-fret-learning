set pagination off
set print thread-events off
set confirm off
handle SIGFPE stop print pass
run
python
if gdb.selected_inferior().pid:
    gdb.execute("p $_siginfo")
    gdb.execute("thread apply all bt 25")
    gdb.execute("continue")
end

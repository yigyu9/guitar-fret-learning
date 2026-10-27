set pagination off
set confirm off
set breakpoint pending on
set print thread-events off
python
import gdb
class Marker(gdb.Breakpoint):
    def stop(self):
        self.enabled=False
        gdb.Breakpoint('format_float_short')
        gdb.Breakpoint('_Py_dg_strtod')
        gdb.write('HOTSPOT_TRAPS_ARMED_AFTER_ADAPTER_INSTALL\n')
        return False
Marker('transition_serializer_hotspot_marker')
end
run
python
inferior=gdb.selected_inferior()
if inferior.pid:
    gdb.write('UNEXPECTED_HOTSPOT_OR_SIGNAL_STOP\n')
    gdb.execute('bt 8')
    gdb.execute('quit 2')
else:
    gdb.write('NO_CPYTHON_FLOAT_FORMAT_PARSE_HOTSPOT_REACHED\n')
    gdb.execute('quit 0')
end

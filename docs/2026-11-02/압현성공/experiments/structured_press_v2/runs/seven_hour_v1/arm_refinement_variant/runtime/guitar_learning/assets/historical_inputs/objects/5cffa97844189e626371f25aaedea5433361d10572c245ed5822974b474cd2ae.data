"""Bounded, rate-limited finger closure targets; contact cache only stops closure."""
import numpy as np

DIGITS = ('index','middle','ring','pinky')


class FingerGripControl:
    def __init__(self, mode, cap):
        if mode not in ('off','ramp','contact') or not np.isfinite(cap) or not 0<=cap<=.6:
            raise ValueError('finger mode and closure cap must be valid')
        self.mode, self.cap = mode, cap
        self.amount = {digit:0. for digit in DIGITS}

    def update(self, contacts, dt):
        if not np.isfinite(dt) or dt<=0:
            raise ValueError('positive finite control dt required')
        blocked = {digit:[] for digit in DIGITS}
        for contact in contacts:
            if contact['lambda']<=0:
                continue
            a,b = contact['body0_name'],contact['body1_name']
            for digit in DIGITS:
                prefix = 'human/LH:'+digit
                other = b if a.startswith(prefix) else a if b.startswith(prefix) else None
                if other and (other.startswith('guitar/') or (other.startswith('human/') and not other.startswith('human/LH:'))):
                    blocked[digit].append(other)
        for digit in DIGITS:
            if self.mode!='off' and not (self.mode=='contact' and blocked[digit]):
                self.amount[digit] = min(self.cap,self.amount[digit]+6*dt)
        offsets = {'LH:'+digit+suffix:self.amount[digit]*weight for digit in DIGITS
                   for suffix,weight in (('1_x',.7),('2',1.),('3',.6))}
        return offsets, {'closure_amount_rad':dict(self.amount),'blocked_by_contact':blocked,
                         'mode':self.mode,'rate_rad_s':6.,'cap_rad':self.cap}


import math
import time

def fast_bin(fft):

    cdef int b0 = 0
    cdef int i = 0
    cdef int b1 = 0
    cdef float peak
    cdef float outp
    cdef int BANDS = 24

    pspec = []


    while i < BANDS:
        peak = 0
        b1 = pow(2, i * 10.0 / (BANDS - 1))
        if b1 > 511:
            b1 = 511
        if b1 <= b0:
            b1 = b0 + 1
        while b0 < b1 and b0 < 511:
            if peak < fft[1 + b0]:
                peak = fft[1 + b0]
            b0 += 1

        outp = math.sqrt(peak)
        # print(int(outp*20))
        pspec.append(int(outp * 45))
        i += 1

    return pspec

def checkEqual(lst):
    return not lst or lst.count(lst[0]) == len(lst)

def fast_display(spec, sspec):

    cdef int i = 0

    while i < 24:
        if spec[i] > sspec[i]:
            sspec[i] += 1
            if abs(spec[i] - sspec[i]) > 4:
                sspec[i] += 1
            if abs(spec[i] - sspec[i]) > 6:
                sspec[i] += 1
            if abs(spec[i] - sspec[i]) > 8:
                sspec[i] += 1

        elif spec[i] == sspec[i]:
            pass
        elif spec[i] < sspec[i] > 0:
            sspec[i] -= 1
            if abs(spec[i] - sspec[i]) > 4:
                sspec[i] -= 1
            if abs(spec[i] - sspec[i]) > 6:
                sspec[i] -= 1
            if abs(spec[i] - sspec[i]) > 8:
                sspec[i] -= 1
        i += 1

    return sspec
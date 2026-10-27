#include <stdint.h>

/* Observe only: no exception clearing, mask changes, or control-state loads. */
uint64_t read_fp_state(void) {
    uint16_t control, status;
    uint32_t mxcsr;
    __asm__ volatile ("fnstcw %0" : "=m" (control));
    __asm__ volatile ("fnstsw %0" : "=m" (status));
    __asm__ volatile ("stmxcsr %0" : "=m" (mxcsr));
    return ((uint64_t) mxcsr << 32) | ((uint64_t) status << 16) | control;
}

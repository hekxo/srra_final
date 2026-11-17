"""Расчёты заданий 4, 5, 6 по данным варианта 29 (стр. 37 задания)."""
import math

HOURS_YEAR = 8760

# --- Задание 4: доступность ---
A_mtbf, A_mttr = 1720, 4      # A: диспетчерский сервер (FMS)
B_mtbf, B_mttr = 4100, 1      # B: база данных парка
C_sla = 0.999                 # C: внешний канал связи (SLA), не дублируется

a = A_mtbf / (A_mtbf + A_mttr)
b = B_mtbf / (B_mtbf + B_mttr)
c = C_sla
serial = a * b * c
a2 = 1 - (1 - a) ** 2
b2 = 1 - (1 - b) ** 2
serial_dup = a2 * b2 * c
print("Задание 4")
print(f"  A_A = {a:.6f}, A_B = {b:.6f}, A_C = {c:.6f}")
print(f"  Последовательно A->B->C: {serial:.6f}  простой {(1-serial)*HOURS_YEAR:.1f} ч/год")
print(f"  Дублированы A и B: A_A2 = {a2:.8f}, A_B2 = {b2:.9f}")
print(f"  После дублирования: {serial_dup:.6f}  простой {(1-serial_dup)*HOURS_YEAR:.2f} ч/год")
print(f"  Предел (только C): простой {(1-c)*HOURS_YEAR:.2f} ч/год")

# --- Задание 5: FAIR ---
pert = lambda mn, ml, mx: (mn + 4 * ml + mx) / 6
lef = pert(3, 6, 9)
lm = pert(2, 5, 49)
lm_after = pert(0.3, 0.6, 6.3)
measure = 39
ale = lef * lm
ale_after = lef * lm_after
rosi = (ale - ale_after - measure) / measure
print("Задание 5")
print(f"  LEF = {lef:.2f}/год, LM = {lm:.2f} млн, LM после = {lm_after:.2f} млн")
print(f"  ALE до = {ale:.1f} млн/год, ALE после = {ale_after:.1f} млн/год, мера = {measure}")
print(f"  ROSI = {rosi:.2f}")

# --- Задание 6: POFOD / ROCOF / AVAIL по испытаниям 720 ч ---
req, req_fail, srv_fail, down = 16000, 8, 6, 5.4
print("Задание 6")
print(f"  POFOD = {req_fail}/{req} = {req_fail/req:.4f}")
print(f"  ROCOF = {srv_fail}/720 = {srv_fail/720:.4f} 1/ч (1 отказ в {720/srv_fail/24:.1f} сут)")
print(f"  AVAIL = (720-{down})/720 = {(720-down)/720:.4f}")

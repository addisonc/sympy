"""
   This example shows how to simulate quantum teleportation in sympy
"""

from sympy.physics.quantum.gate import *
from sympy.physics.quantum.qubit import Qubit, measure_partial
from sympy.physics.quantum.applyops import apply_operators
from sympy.physics.quantum.circuitplot import circuit_plot
from sympy import symbols
from sympy.interactive import init_printing
from sympy import sqrt, pprint

"""
   Run this branch on Addison's normalize_fix branch: git co addison/normalize_fix

*Alice and Bob meet and entangle qubits; Alice takes Qubit 1, Bob takes 2
*Some time later, Alice takes an arbitrary state (Qubit 0) and applies a similair entangling operator
*Alice then measures Qubits 1 and 0
*Alice tells Bob to apply an XGate and/or a ZGate based on measurement
*Bob now has the arbitrary state 
"""

a,b = symbols('ab', real=True)
state = Qubit('000')*a + Qubit('001')*b; state

#This operator will entangle bits 1 and 2
entangle1_2 = CNOT(1,2)*HadamardGate(1); entangle1_2
state = apply_operators(entangle1_2*state); state

#Bit 1 goes to Alice and bit 2 goes to Bob

#Now, some time later, Alics entangles Qubit 1 and Qubit 0 
entangle0_1 = HadamardGate(0)*CNOT(0,1); entangle0_1
circuit_plot(entangle0_1*entangle1_2, nqubits=3)
state = apply_operators(entangle0_1*state); state

#Alice now measures both of her qubits
measured_result = measure_partial(state, (0,1), normalize=False); measured_result

#lets say she measured 10
state = (measured_result[2][0]*2).expand(); state

#she tells bob to apply a Not Operator to his bit, so that bob has the original state
state = apply_operators(XGate(2)*state); state


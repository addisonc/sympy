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

init_printing()

#make a state that is a superposition of 0 and 1 for 3 qubits
#This is an arbitrary symbolic superposition
a,b = symbols('ab')
state = Qubit('000')*a + Qubit('001')*b
pprint(state)

#This operator will entangle bits 1 and 2
Entangle1_2 = CNOT(1,2)*HadamardGate(1)
circuit_plot(Entangle1_2, nqubits=3)
state = apply_operators(Entangle1_2*state)
pprint(state)

#Bit one goes to Alice and bit 2 goes to Bob

#Now, some time later, Alics entangles Qubit 1 and Qubit 0 
Entangle0_1 = HadamardGate(0)*CNOT(0,1)
circuit_plot(Entangle0_1, nqubits=3)
state = apply_operators(Entangle0_1*state)
pprint(state)

#Alice now measures both of her qubits
measured_result = measure_partial(state, (0,1))
#These are possible results with given probabilities
pprint(measured_result)

#lets say she measured 1,0 for her bits
state = measured_result[2][0]
pprint(state)

#she tells bob to apply a Not Operator to his bit
state = apply_operators(XGate(2)*state)
pprint(state)



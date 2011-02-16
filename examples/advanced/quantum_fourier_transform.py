
"""
This is an example file that will demonstrate how to use the Sympy's QFT
"""

from sympy.physics.quantum.qft import QFT, IQFT, Fourier
from sympy.physics.quantum.qubit import Qubit
from sympy.physics.quantum.represent import represent
from sympy.physics.quantum.applyops import apply_operators
from sympy.physics.quantum.circuitplot import circuit_plot
from sympy.interactive import init_printing
from sympy import sqrt, pprint

"""
   Sympy has the ability to apply discrete fourier transforms to states
   Function useful for period finding subroutines
   Can decompose both Quantum Fourier and it's inverse into elementary gates
   Can represent Discrete Fourier transform matrix
"""


fourier = QFT(0,3).decompose(); fourier

close('all'); circuit_plot(fourier, nqubits=3)

represent(Fourier(0,3), nqubits=3)*4/sqrt(2)

state = (Qubit('000') + Qubit('010') + Qubit('100') + Qubit('110'))/sqrt(4); state
apply_operators(fourier*state)


"""
This is an example file that will demonstrate how to use the Sympy's QFT
To do circuit ploting, matplotlib [and other libraries] needs to be installed.
Run ipython with the --pylab flag
"""

from sympy.physics.quantum.qft import QFT, IQFT
from sympy.physics.quantum.qubit import Qubit
from sympy.physics.quantum.represent import represent
from sympy.physics.quantum.applyops import apply_operators
from sympy.physics.quantum.circuitplot import circuit_plot
from sympy.interactive import init_printing
from sympy import sqrt, pprint

#First, initialize pretty printing
init_printing()

#We can create a QFT operator and decompose it in terms of elementary gates
Fourier = QFT(0,3).decompose()
pprint(Fourier)

#We can also plot the Fourier gate
circuit_plot(Fourier, nqubits=3)

#We can represent the QFT in a three qubit space
pprint(represent(QFT(0,3), nqubits=3))

#We can apply the QFT to a state to put state into the frequency basis
#The following state is something akin to what we would find in an order-finding
#subroutine
state = (Qubit('000') + Qubit('010') + Qubit('100') + Qubit('110'))/sqrt(4)
pprint(apply_operators(Fourier*state))


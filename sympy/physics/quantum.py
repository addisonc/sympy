from sympy import Expr, sympify, Add, Mul, Function, S, Matrix
from sympy.printing.pretty.stringpict import prettyForm
from sympy.core.containers import Tuple
from sympy.physics.qexpr import (
    QuantumError, QExpr, split_commutative_parts, split_qexpr_parts
)
from sympy.physics.hilbert import HilbertSpace, HilbertSpaceError

"""
Questions:

* What does doit do and should be use it to do things like apply operators?
* How should we handle assumptions?  New or old system?
* How should we handle different types of operators like symmetric, hermitian,
  etc? Assumptions?
* What should a basis set consist of?  Somehow it needs to know about a set
  of states and maybe the operator they are eigenvectors of. We need a way
  of labeling these states by name and index: |a[0]>, |a[1]>, etc.
"""

__all__ = [
    'KetBase',
    'BraBase',
    'StateBase',
    'State',
    'Ket',
    'Bra',
    'TimeDepState',
    'TimeDepBra',
    'TimeDepKet',
    'Operator',
    'HermitianOperator',
    'UnitaryOperator',
    'OuterProduct',
    'InnerProduct',
    'Dagger',
    'KroneckerDelta',
    'Commutator',
    'AntiCommutator',
]

#-----------------------------------------------------------------------------
# Abstract base classes
#-----------------------------------------------------------------------------

class Representable(object):
    """An object that can be represented.
    """

    def represent(self, basis, **options):
        rep_method = '_represent_%s' % basis.__class__.__name__
        if hasattr(self, rep_method):
            f = getattr(self, rep_method)
            rep = f(basis, **options)
            return rep
        else:
            raise NotImplementedError("Can't represent %r in basis: %r" % (
                self, basis
            ))

#-----------------------------------------------------------------------------
# States, bras and kets.
#-----------------------------------------------------------------------------

class StateBase(QExpr, Representable):
    """Abstract base class for general abstract states in quantum mechanics.

    All other state classes defined will need to inherit from this class. It
    carries the basic structure for all other states such as dual, _eval_dagger
    and label.

    This is an abstract base class and you should not instantiate it directly,
    instead use State.
    """

    is_continuous = False
    is_discrete = False

    #-------------------------------------------------------------------------
    # Properties
    #-------------------------------------------------------------------------

    @property
    def label(self):
        """The label is the unique set of identifiers for the state.

        The label of a state is what distinguishes it from other states. For
        eigenstates, the label is usually a sympy.core.containers.Tuple of the
        quantum numbers. For an abstract state, it would just be a single
        element Tuple of the symbol of the state.
        """
        return self.args[0]

    @property
    def dual(self):
        """Return the dual state of this one."""
        raise NotImplementedError('dual must be implemented in a subclass')

    @property
    def is_symbolic(self):
        return True

    #-------------------------------------------------------------------------
    # _eval_* methods
    #-------------------------------------------------------------------------

    @classmethod
    def _eval_label(cls, label):
        """Make sure that label is a sympy.core.containers.Tuple.

        The elements of the Tuple must be run through sympify.
        """
        if not isinstance(label, Tuple):
            if isinstance(label, (list, tuple)):
                # Convert a raw tuple or list to a Tuple
                newlabel = Tuple(*label)
            else:
                # Single element label gets wrapped into a tuple.
                newlabel = Tuple(label)
        else:
            newlabel = label
        newlabel = Tuple(*[sympify(item) for item in newlabel])
        return newlabel

    @classmethod
    def _eval_hilbert_space(cls, label):
        """Compute the Hilbert space instance from the label."""
        return HilbertSpace()

    def _eval_dagger(self):
        """Compute the Dagger of this state."""
        return self.dual

    def _eval_innerproduct(self, other, **hints):
        return None

    @classmethod
    def _default_acts_like(cls):
        return StateBase

    #-------------------------------------------------------------------------
    # Printing
    #-------------------------------------------------------------------------

    def _print_label(self, printer, *args):
        result = []
        for item in self.label:
            result.append(printer._print(item, *args))
        return ''.join(result)

    def _print_label_repr(self, printer, *args):
        return printer._print(self.label, *args)

    def _print_label_pretty(self, printer, *args):
        pform = printer._print(self.label[0], *args)
        for item in self.label[1:]:
            nextpform = printer._print(item, *args)
            pform = prettyForm(*pform.right((nextpform)))
        return pform

    def _print_contents(self, printer, *args):
        return self._print_label(printer, *args)

    def _print_contents_repr(self, printer, *args):
        return self._print_label_repr(printer, *args)

    def _print_contents_pretty(self, printer, *args):
        return self._print_label_pretty(printer, *args)

    def _sympystr(self, printer, *args):
        return '%s%s%s' % (self.lbracket, self._print_contents(printer, *args),
                           self.rbracket)

    def _sympyrepr(self, printer, *args):
        return '%s(%s)' % (
            self.__class__.__name__, self._print_contents_repr(printer, *args)
        )

    def _pretty(self, printer, *args):
        from sympy.printing.pretty.stringpict import prettyForm
        pform = self._print_contents_pretty(printer, *args)
        pform = prettyForm(*pform.left((self.lbracket_pretty)))
        pform = prettyForm(*pform.right((self.rbracket_pretty)))
        return pform

    #-------------------------------------------------------------------------
    # Methods from Basic and Expr
    #-------------------------------------------------------------------------
    
    def doit(self, **kw_args):
        return self


class KetBase(StateBase):
    """Base class for Kets.

    This class defines the dual property and the brackets for printing. This
    is an abstract base class and you should not instantiate it directly,
    instead use Ket.
    """

    lbracket = '|'
    rbracket = '>'
    lbracket_pretty = prettyForm(u'\u2758')
    rbracket_pretty = prettyForm(u'\u27E9')

    @property
    def dual(self):
        return BraBase(*self.args)

    @classmethod
    def _default_acts_like(cls):
        return KetBase

    def apply_operator(self, op):
        if not isinstance(op, Operator):
            raise TypeError('Operator expected, got: %r' % op)
        apply_method = '_apply_operator_%s' % op.__class__.__name__
        if hasattr(self, apply_method):
            f = getattr(self, apply_method)
            result = f(op)
            return result
        else:
            NotImplementedError(
            "Don't know how apply operator %r to Ket %r" % (op, self)
        )


class BraBase(StateBase):
    """Base class for Bras.

    This class defines the dual property and the brackets for printing. This
    is an abstract base class and you should not instantiate it directly,
    instead use Bra.
    """

    lbracket = '<'
    rbracket = '|'
    lbracket_pretty = prettyForm(u'\u27E8')
    rbracket_pretty = prettyForm(u'\u2758')

    @property
    def dual(self):
        return KetBase(*self.args)

    @classmethod
    def _default_acts_like(cls):
        return BraBase


class State(StateBase):
    """General abstract quantum state."""

    def __new__(cls, label, **old_assumptions):
        # First compute args and call Expr.__new__ to create the instance
        label = cls._eval_label(label)
        inst = Expr.__new__(cls, label, **{'commutative':False})
        # Now set the slots on the instance
        inst.hilbert_space = cls._eval_hilbert_space(label)
        inst.acts_like = cls._default_acts_like()
        return inst


class Ket(State, KetBase):
    """A Ket state for quantum mechanics.

    Inherits from State and KetBase. In a state represented by a ray in Hilbert
    space, a Ket is a vector that points along that ray [1].

    A Ket takes in a label as its argument in order to be differentiated from
    other Kets.

    Examples
    ========

    Creating and using a Ket:

        >>> from sympy.physics.quantum import Ket
        >>> psi = Ket('psi')
        >>> psi
        |psi>
        >>> psi.label
        psi
        >>> psi.dual
        <psi|


    References
    ==========

    [1] http://en.wikipedia.org/wiki/Bra-ket_notation
    """

    @property
    def dual(self):
        return Bra(*self.args)


class Bra(State, BraBase):
    """A Bra state for quantum mechanics.

    Inherits from State and BraBase. A Bra is the dual of a Ket [1].

    A Bra takes in a label as its argument in order to be differentiated from
    other Bras.

    Examples
    ========

    Creating and using a Bra:

        >>> from sympy.physics.quantum import Bra
        >>> b = Bra('bus')
        >>> b
        <bus|
        >>> b.label
        bus
        >>> b.dual
        |bus>


    References
    ==========

    [1] http://en.wikipedia.org/wiki/Bra-ket_notation
    """

    @property
    def dual(self):
        return Ket(*self.args)

#-----------------------------------------------------------------------------
# Time dependent states, bras and kets.
#-----------------------------------------------------------------------------

class TimeDepState(StateBase):
    """General abstract time dependent quantum state.

    Used for sub-classing time dependent states in quantum mechanics.

    Takes in label and time arguments.
    """
    def __new__(cls, label, time, **old_assumptions):
        # First compute args and call Expr.__new__ to create the instance
        label = cls._eval_label(label)
        time = cls._eval_time(time)
        inst = Expr.__new__(cls, label, time, **{'commutative':False})
        # Now set the slots on the instance
        inst.hilbert_space = cls._eval_hilbert_space(label)
        inst.acts_like = cls._default_acts_like()
        return inst

    @property
    def time(self):
        return self.args[1]

    @classmethod
    def _eval_time(cls, time):
        return sympify(time)

    def _print_time(self, printer, *args):
        return printer._print(self.time, *args)

    def _print_time_repr(self, printer, *args):
        return printer._print(self.time, *args)

    def _print_time_pretty(self, printer, *args):
        pform = printer._print(self.time, *args)
        return pform

    def _print_contents(self, printer, *args):
        label = self._print_label(printer, *args)
        time = self._print_time(printer, *args)
        return '%s;%s' % (label, time)

    def _print_contents_repr(self, printer, *args):
        label = self._print_label_repr(printer, *args)
        time = self._print_time_repr(printer, *args)
        return '%s,%s' % (label, time)

    def _print_contents_pretty(self, printer, *args):
        pform = self._print_label_pretty(printer, *args)
        pform = prettyForm(*pform.right((';')))
        nextpform = self._print_time_pretty(printer, *args)
        pform = prettyForm(*pform.right((nextpform)))
        return pform


class TimeDepKet(TimeDepState, KetBase):
    """A time dependent Ket state for quantum mechanics.

    Inherits from TimeDepState and KetBase. Its dual is a time dependent
    Bra state.

    Takes in label and time arguments.
    """

    @property
    def dual(self):
        return TimeDepBra(*self.args)


class TimeDepBra(TimeDepState, BraBase):
    """A time dependent Bra state for quantum mechanics.

    Inherits from TimeDepState and BraBase. Its dual is a time dependent
    Ket state.

    Takes in label and time arguments.
    """

    @property
    def dual(self):
        return TimeDepKet(*self.args)

#-----------------------------------------------------------------------------
# Operators and outer products
#-----------------------------------------------------------------------------

class Operator(QExpr, Representable):
    """Base class for non-commuting quantum operators.

    An operator is a map from one vector space to another [1]. In quantum
    mechanics, operators correspond to observables [2].

    An operator takes in a name argument to differentiate it from other
    operators.

    Examples
    ========

    Creating and using an Operator.

        >>> from sympy import sympify
        >>> from sympy.physics.quantum import Operator
        >>> a = Operator('A')
        >>> a
        A
        >>> a.name
        A

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Operator
    [2] http://en.wikipedia.org/wiki/Observable
    """

    def __new__(cls, label, **old_assumptions):
        label = sympify(label)
        obj = Expr.__new__(cls, label, **{'commutative': False})
        obj.hilbert_space = cls._eval_hilbert_space(label)
        obj.acts_like = cls._default_acts_like()
        return obj

    @classmethod
    def _eval_hilbert_space(cls, label):
        return HilbertSpace()

    @classmethod
    def _default_acts_like(cls):
        return Operator

    @property
    def label(self):
        return self.args[0]

    @property
    def is_symbolic(self):
        return True

    def _sympyrepr(self, printer, *args):
        return '%s(%s)' % (self.__class__.__name__, printer._print(self.label,\
        *args))

    def _sympystr(self, printer, *args):
        return printer._print(self.label, *args)

    def _pretty(self, printer, *args):
        return printer._print(self.label, *args)

    def doit(self,**kw_args):
        return self

    def _eval_commutator(self, other):
        """Evaluate [self, other] if known, return None if not known."""
        return None

    def _eval_rcommutator(self, other):
        """Evaluate [other, self] if known, return None if not known."""
        return None

    def _eval_anticommutator(self, other):
        """Evaluate [self, other] if known."""
        return None

    def _eval_ranticommutator(self, other):
        """Evaluate [other, self] if known."""
        return None


class HermitianOperator(Operator):
    """A Hermitian operator"""

    def _eval_dagger(self):
        return self


class UnitaryOperator(Operator):
    """A unitary operator."""

    def _eval_dagger(self):
        return self**(-1)


class OuterProduct(Operator):
    """An unevaluated outer product between a Ket and Bra.

    Because a Ket is essentially a column vector and a Bra is essentially a row
    vector, the outer product evaluates (acts_like) to an operator
    (i.e. a matrix) [1].

    An InnerProduct takes first a Ket and then a Bra as its arguments.

    Examples
    ========

    Create an OuterProduct and check its properties:

        >>> from sympy.physics.quantum import Ket, Bra, OuterProduct
        >>> op = OuterProduct(Ket('a'), Bra('b'))
        >>> op
        |a><b|
        >>> op.ket
        |a>
        >>> op.bra
        <b|

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Outer_product
    """

    def __new__(cls, ket, bra, **old_assumptions):
        if not isinstance(ket, KetBase):
            raise TypeError('KetBase subclass expected, got: %r' % ket)
        if not isinstance(bra, BraBase):
            raise TypeError('BraBase subclass expected, got: %r' % ket)
        if not ket.hilbert_space == bra.hilbert_space:
            raise HilbertSpaceError(
                'Incompatible hilbert spaces: %r and %r' % (ket, bra)
            )
        obj = Expr.__new__(cls, *(ket, bra), **{'commutative': False})
        obj.hilbert_space = ket.hilbert_space
        obj.acts_like = cls._default_acts_like()
        return obj

    @property
    def ket(self):
        return self.args[0]

    @property
    def bra(self):
        return self.args[1]

    def _eval_dagger(self):
        return OuterProduct(Dagger(self.bra), Dagger(self.ket))

    def _sympyrepr(self, printer, *args):
        return '%s(%s,%s)' % (self.__class__.__name__, 
            printer._print(self.ket, *args), printer._print(self.bra, *args))

    def _sympystr(self, printer, *args):
        return str(self.ket)+str(self.bra)

    def _pretty(self, printer, *args):
        pform = self.ket._pretty(printer, *args)
        return prettyForm(*pform.right(self.bra._pretty(printer, *args)))

    def doit(self,**kw_args):
        return self


class Commutator(Operator):
    """The commutator function for quantum mechanics.

    This function behaves as such: [A, B] = A*B - B*A

    The arguments are ordered according to .__cmp__()

    Examples
    ========

    >>> from sympy import symbols
    >>> from sympy.physics.quantum import Commutator
    >>> A, B = symbols('A B', **{'commutative':False})
    >>> Commutator(B, A)
    -1*Commutator(A, B)

    Evaluate the commutator with .doit()

    >>> comm = Commutator(A,B); comm
    Commutator(A, B)
    >>> comm.doit()
    A*B - B*A

    References
    ==========

    http://en.wikipedia.org/wiki/Commutator
    """

    def __new__(cls, A, B, **old_assumptions):
        # Only check these things if A, B are QExprs. This allows commutators
        # to work with scalars (Expr), even though they will always vanish. 
        # This happens when you take the expectation values of a commutator.
        if isinstance(A, QExpr) and isinstance(B, QExpr):
            if not issubclass(A.acts_like, Operator):
                raise TypeError('Acts like Operator expected, got: %r' % A)
            if not issubclass(B.acts_like, Operator):
                raise TypeError('Acts like Operator expected, got: %r' % B)
            if not A.hilbert_space == B.hilbert_space:
                raise HilbertSpaceError(
                    'Incompatible hilbert spaces: %r and %r' % (A, B)
                )
        r = cls.eval(A, B)
        if r is not None:
            # TODO: do I need to set the hilbert_space attribute of this?
            return r
        obj = Expr.__new__(cls, *(A, B), **{'commutative': False})
        obj.hilbert_space = A.hilbert_space
        obj.acts_like = cls._default_acts_like()
        return obj

    @classmethod
    def eval(cls, a, b):
        """The Commutator [A,B] is on canonical form if A < B.
        """
        if not (a and b): return S.Zero
        if a == b: return S.Zero
        if a.is_commutative or b.is_commutative:
            return S.Zero

        # [xA,yB]  ->  xy*[A,B]
        from sympy.physics.qmul import QMul
        e_part = e_part2 = []
        qec_part = qec_part2 = []
        qenc_part = qenc_part2 = []
        if isinstance(a, (Mul, QMul)):
            e_part, qec_part, qenc_part = split_qexpr_parts(a)
        if isinstance(b, (Mul, QMul)):
            e_part2, qec_part2, qenc_part2 = split_qexpr_parts(b)
            e_part.extend(e_part2)
            qec_part.extend(qec_part2)
        if e_part or qec_part:
            a = qenc_part or [a]
            b = qenc_part2 or [b]
            return QMul(Mul(*e_part), QMul(*qec_part), cls(QMul(*a), QMul(*b)))

        #
        # Canonical ordering of arguments
        #
        if a.compare(b) == 1:
            return S.NegativeOne*cls(b,a)

    def _eval_expand_commutator(self, **hints):
        from sympy.physics.qadd import QAdd
        from sympy.physics.qmul import QMul

        A = self.args[0].expand(**hints)
        B = self.args[1].expand(**hints)

        # [A+B,C]  ->  [A,C] + [B,C]
        if isinstance(A, (Add, QAdd)):
            return QAdd(*[Commutator(term,B) for term in A.args])
        if isinstance(B, (Add, QAdd)):
            return QAdd(*[Commutator(A,term) for term in B.args])

        if isinstance(A, QMul):
            # [a*b,c] -> a*[b,c] + [a,c]*b
            a = A.args[0]
            b = QMul(*A.args[1:])
            c = B
            first = QMul(a, Commutator(b, c))
            second = QMul(Commutator(a, c), b)
            return QAdd(first, second)
        if isinstance(B, QMul):
            # [a,b*c] -> [a,b]*c + b*[a,c]
            a = A
            b = B.args[0]
            c = QMul(*B.args[1:])
            first = QMul(Commutator(a, b), c)
            second = QMul(b, Commutator(a, c))
            return QAdd(first, second)

        # No changes, so return self
        return self

    def doit(self, **hints):
        A = self.args[0]
        B = self.args[1]
        if isinstance(A, Operator) and isinstance(B, Operator):
            comm = A._eval_commutator(B)
            if comm is None:
                comm = B._eval_rcommutator(A)
            if comm is not None:
                return comm.doit(**hints)
        return (A*B - B*A).doit(**hints)

    def _eval_dagger(self):
        return Commutator(Dagger(self.args[1]), Dagger(self.args[0]))

    def _sympyrepr(self, printer, *args):
        return "%s(%s,%s)" % (self.__class__.__name__, self.args[0],\
        self.args[1])

    def _sympystr(self, printer, *args):
        return "[%s,%s]" % (self.args[0], self.args[1])

    def _pretty(self, printer, *args):
        pform = printer._print(self.args[0], *args)
        pform = prettyForm(*pform.right((prettyForm(u','))))
        pform = prettyForm(*pform.right((printer._print(self.args[1], *args))))
        pform = prettyForm(*pform.parens(left='[', right=']'))
        return pform

    def _latex_(self,printer):
        return "\\left[%s,%s\\right]"%tuple([
            printer._print(arg) for arg in self.args])


class AntiCommutator(Operator):
    """The commutator function for quantum mechanics.

    This function behaves as such: [A, B] = A*B - B*A

    The arguments are ordered according to .__cmp__()

    Examples
    ========

    >>> from sympy import symbols
    >>> from sympy.physics.quantum import Commutator
    >>> A, B = symbols('A B', **{'commutative':False})
    >>> Commutator(B, A)
    -1*Commutator(A, B)

    Evaluate the commutator with .doit()

    >>> comm = Commutator(A,B); comm
    Commutator(A, B)
    >>> comm.doit()
    A*B - B*A

    References
    ==========

    http://en.wikipedia.org/wiki/Commutator
    """

    def __new__(cls, A, B, **old_assumptions):
        # Only check these things if A, B are QExprs. This allows commutators
        # to work with scalars (Expr), even though they will always vanish. 
        # This happens when you take the expectation values of a commutator.
        if isinstance(A, QExpr) and isinstance(B, QExpr):
            if not issubclass(A.acts_like, Operator):
                raise TypeError('Acts like Operator expected, got: %r' % A)
            if not issubclass(B.acts_like, Operator):
                raise TypeError('Acts like Operator expected, got: %r' % B)
            if not A.hilbert_space == B.hilbert_space:
                raise HilbertSpaceError(
                    'Incompatible hilbert spaces: %r and %r' % (A, B)
                )
        r = cls.eval(A, B)
        if r is not None:
            # TODO: do I need to set the hilbert_space attribute of this?
            return r
        obj = Expr.__new__(cls, *(A, B), **{'commutative': False})
        obj.hilbert_space = A.hilbert_space
        obj.acts_like = cls._default_acts_like()
        return obj

    @classmethod
    def eval(cls, a, b):
        """The Commutator [A,B] is on canonical form if A < B.
        """
        if not (a and b): return S.Zero
        if a == b: return sympify(2)*a**2
        if a.is_commutative or b.is_commutative:
            return sympify(2)*a*b

        # [xA,yB]  ->  xy*[A,B]
        from sympy.physics.qmul import QMul
        c_part = []
        nc_part = []
        nc_part2 = []
        if isinstance(a, (Mul, QMul)):
            c_part, nc_part = split_commutative_parts(a)
        if isinstance(b, (Mul, QMul)):
            c_part2, nc_part2 = split_commutative_parts(b)
            c_part.extend(c_part2)
        if c_part:
            a = nc_part or [a]
            b = nc_part2 or [b]
            return QMul(Mul(*c_part), cls(QMul(*a), QMul(*b)))

        # Canonical ordering of arguments
        if a.compare(b) == 1:
            return cls(b,a)

    def _eval_expand_anticommutator(self, **hints):
        # No changes, so return self
        return self

    def doit(self, **hints):
        A = self.args[0]
        B = self.args[1]
        if isinstance(A, Operator) and isinstance(B, Operator):
            comm = A._eval_anticommutator(B)
            if comm is None:
                comm = B._eval_ranticommutator(A)
            if comm is not None:
                return comm.doit(**hints)
        return (A*B + B*A).doit(**hints)

    def _eval_dagger(self):
        return Commutator(Dagger(self.args[0]), Dagger(self.args[1]))

    def _sympyrepr(self, printer, *args):
        return "%s(%s,%s)" % (self.__class__.__name__, self.args[0],\
        self.args[1])

    def _sympystr(self, printer, *args):
        return "{%s,%s}" % (self.args[0], self.args[1])

    def _pretty(self, printer, *args):
        pform = printer._print(self.args[0], *args)
        pform = prettyForm(*pform.right((prettyForm(u','))))
        pform = prettyForm(*pform.right((printer._print(self.args[1], *args))))
        pform = prettyForm(*pform.parens(left='{', right='}'))
        return pform

    def _latex_(self,printer):
        return "\\left{%s,%s\\right}"%tuple([
            printer._print(arg) for arg in self.args])

#-----------------------------------------------------------------------------
# Other subclases of QExpr
#-----------------------------------------------------------------------------

class Dagger(QExpr):
    """General Hermitian conjugate operation.

    When an object is daggered it is transposed and then the complex conjugate
    is taken [1].

    A Dagger can take in any quantum object as its argument.

    Examples
    ========

    Daggering various quantum objects:

        >>> from sympy.physics.quantum import Dagger, Ket, Bra, InnerProduct,\
        OuterProduct, Operator
        >>> Dagger(Ket('psi'))
        <psi|
        >>> Dagger(Bra('bus'))
        |bus>
        >>> Dagger(InnerProduct(Bra('a'), Ket('b')))
        <b|a>
        >>> Dagger(OuterProduct(Ket('a'), Bra('b')))
        |b><a|
        >>> Dagger(Operator('A'))
        Dagger(A)

    Notice how daggering the operator 'A' results in isympy returning an
    unevaluated Dagger object (because A had no _eval_dagger method).

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Hermitian_transpose
    """

    def __new__(cls, arg, **old_assumptions):
        if isinstance(arg, Matrix):
            return arg.H
        arg = sympify(arg)
        r = cls.eval(arg)
        if isinstance(r, Expr):
            return r
        #make unevaluated dagger commutative or non-commutative depending on arg
        if arg.is_commutative:
            obj = Expr.__new__(cls, arg)
        else:
            obj = Expr.__new__(cls, arg, **{'commutative':False})
        if isinstance(obj, QExpr):
            obj.hilbert_space = arg.hilbert_space
            obj.acts_like = arg.acts_like
        return obj

    @classmethod
    def eval(cls, arg):
        """
        Evaluates the Dagger instance.
        """
        if hasattr(arg, '_eval_dagger'):
            return arg._eval_dagger()
        elif not isinstance(arg, (InnerProduct, OuterProduct, Operator,\
        StateBase)):
            return arg.conjugate()
        elif isinstance(arg, Matrix):
            arg = arg.T
            for i in range(arg.rows*arg.cols):
                arg[i] = Dagger(arg[i])
            return arg
        else:
            return None

    def _eval_subs(self, old, new):
        r = Dagger(self.args[0].subs(old, new))
        return r

    def _eval_dagger(self):
        return self.args[0]

    def _sympyrepr(self, printer, *args):
        return '%s(%s)' % (self.__class__.__name__, self.args[0])

    def _sympystr(self, printer, *args):
        return '%s(%s)' % (self.__class__.__name__, self.args[0])

    def _pretty(self, printer, *args):
        from sympy.printing.pretty.stringpict import prettyForm
        pform = printer._print(self.args[0], *args)
        pform = pform**prettyForm(u'\u2020')
        return pform

#-----------------------------------------------------------------------------
# Misc classes
#-----------------------------------------------------------------------------

class KroneckerDelta(Function):
    """The discrete delta function.

    A function that takes in two integers i and j. It returns 0 if i and j are
    not equal or it returns 1 if i and j are equal.

    Examples
    ========

        >>> from sympy.physics.quantum import KroneckerDelta
        >>> KroneckerDelta(1,2)
        0
        >>> KroneckerDelta(3,3)
        1

    References
    ==========

    http://en.wikipedia.org/wiki/Kronecker_delta
    """

    nargs = 2
    is_commutative=True

    @classmethod
    def eval(cls, i, j):
        """
        Evaluates the discrete delta function.
        """
        if i > j:
            return cls(j,i)
        diff = i-j
        if diff == 0:
            return S.One
        elif diff.is_number:
            return S.Zero

    def _eval_subs(self, old, new):
        r = KroneckerDelta(self.args[0].subs(old, new), self.args[1].subs(old,\
        new))
        return r

    def _eval_dagger(self):
        return self

    def _latex_(self,printer):
        return "\\delta_{%s%s}"% (self.args[0].name,self.args[1].name)

    def _sympyrepr(self, printer, *args):
        return "%s(%s,%s)"% (self.__class__.__name__, self.args[0],\
        self.args[1])

    def _sympystr(self, printer, *args):
        return 'd(%s,%s)'% (self.args[0],self.args[1])

# InnerProduct is not an QExpr because it is really just a regular comutative
# number. We have gone back and forth about this, but we gain a lot by having
# this. The main challenges were getting Dagger to work (we use _eval_conjugate)
# and represent (we can use atoms and subs). Having it be an Expr, mean that
# there are no commutative QExpr subclasses, which simplifies the logic in QMul
# a lot.

class InnerProduct(Expr, Representable):
    """An unevaluated inner product between a Bra and a Ket.

    Because a Bra is essentially a row vector and a Ket is essentially a column
    vector, the inner product evaluates (acts_like) to a complex number.

    An InnerProduct takes first a Bra and then a Ket as its arguments.

    Examples
    ========

    Create an InnerProduct and check its properties:

        >>> from sympy.physics.quantum import Bra, Ket, InnerProduct
        >>> ip = InnerProduct(Bra('a'), Ket('b'))
        >>> ip
        <a|b>
        >>> ip.bra
        <a|
        >>> ip.ket
        |b>

    References
    ==========

    http://en.wikipedia.org/wiki/Inner_product
    """

    def __new__(cls, bra, ket, **old_assumptions):
        if not isinstance(ket, KetBase):
            raise TypeError('KetBase subclass expected, got: %r' % ket)
        if not isinstance(bra, BraBase):
            raise TypeError('BraBase subclass expected, got: %r' % ket)
        if not ket.hilbert_space == bra.hilbert_space:
            raise HilbertSpaceError(
                'Incompatible hilbert spaces: %r and %r' % (ket, bra)
        )
        obj = Expr.__new__(cls, *(bra, ket))
        return obj

    @property
    def bra(self):
        return self.args[0]

    @property
    def ket(self):
        return self.args[1]

    def _eval_dagger(self):
        return InnerProduct(Dagger(self.ket), Dagger(self.bra))

    def _eval_conjugate(self):
        return self._eval_dagger()

    def _sympyrepr(self, printer, *args):
        return '%s(%s,%s)' % (self.__class__.__name__, 
            printer._print(self.bra, *args), printer._print(self.ket, *args))

    def _sympystr(self, printer, *args):
        sbra = str(self.bra)
        sket = str(self.ket)
        return '%s|%s' % (sbra[:-1], sket[1:])

    def _pretty(self, printer, *args):
        pform = prettyForm(u'\u276C')
        pform = prettyForm(*pform.right(self.bra._print_label_pretty(printer, *args)))
        return prettyForm(*pform.right(self.ket._pretty(printer, *args)))

    def doit(self, **hints):
        r = self.bra._eval_innerproduct(self.ket, **hints)
        if r is None:
            r = self.ket._eval_innerproduct(self.bra, **hints)
        if r is not None:
            return r
        return self

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def represent(expr, basis, **options):
    """Represent the quantum expression in the given basis.
    """
    from sympy.physics.qadd import QAdd
    from sympy.physics.qmul import QMul
    from sympy.physics.qpow import QPow
    if isinstance(expr, Representable):
        return expr.represent(basis, **options)
    elif isinstance(expr, QAdd):
        result = S.Zero
        for args in expr.args:
            if not result:
                result = represent(args, basis, **options)
            else:
                result += represent(args, basis, **options)
        return result
    elif isinstance(expr, QPow):
        return represent(expr.base, basis, **options)**expr.exp
    elif not isinstance(expr, QMul):
        return expr

    if not isinstance(expr, QMul):
        raise TypeError('QMul expected, got: %r' % expr)

    result = S.One
    for arg in reversed(expr.args):
        result = represent(arg, basis, **options)*result
    return result
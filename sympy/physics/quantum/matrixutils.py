"""Utilities to deal with sympy.Matrix, numpy and scipy.sparse."""

from sympy import Matrix, I, Expr
from sympy.matrices import matrices


__all__ = [
    'numpy_ndarray',
    'scipy_sparse_matrix',
    'sympy_to_numpy',
    'sympy_to_scipy_sparse',
    'numpy_to_sympy',
    'scipy_sparse_to_sympy',
    'flatten_scalar',
    'matrix_dagger',
    'to_sympy',
    'to_numpy',
    'to_scipy_sparse',
    'matrix_tensor_product'
]

# Conditionally define the base classes for numpy and scipy.sparse arrays
# for use in isinstance tests.

try:
    import numpy as np
except ImportError:
    class numpy_ndarray(object):
        pass
else:
    numpy_ndarray = np.ndarray

try:
    from scipy import sparse
except ImportError:
    class scipy_sparse_matrix(object):
        pass
else:
    scipy_sparse_matrix = sparse.base.spmatrix


def sympy_to_numpy(m, **options):
    """Convert a sympy Matrix/complex number to a numpy matrix or scalar."""
    import numpy as np
    dtype = options.get('dtype','complex')
    if isinstance(m, Matrix):
        return np.matrix(m.tolist(), dtype=dtype)
    elif isinstance(m, Expr):
        if m.is_Number or m.is_NumberSymbol or m == I:
            return complex(m)
    raise TypeError('Expected Matrix or complex scalar, got: %r' % m)


def sympy_to_scipy_sparse(m, **options):
    """Convert a sympy Matrix/complex number to a numpy matrix or scalar."""
    from scipy import sparse
    import numpy as np
    dtype = options.get('dtype','complex')
    if isinstance(m, Matrix):
        return sparse.csr_matrix(np.matrix(m.tolist(), dtype=dtype))
    elif isinstance(m, Expr):
        if m.is_Number or m.is_NumberSymbol or m == I:
            return complex(m)
    raise TypeError('Expected Matrix or complex scalar, got: %r' % m)


def scipy_sparse_to_sympy(m, **options):
    """Convert a scipy.sparse matrix to a sympy matrix."""
    return Matrix(m.todense())


def numpy_to_sympy(m, **options):
    """Convert a numpy matrix to a sympy matrix."""
    return Matrix(m)


def to_sympy(m, **options):
    """Convert a numpy/scipy.sparse matrix to a sympy matrix."""
    if isinstance(m, Matrix):
        return m
    elif isinstance(m, numpy_ndarray):
        return numpy_to_sympy(m)
    elif isinstance(m, scipy_sparse_matrix):
        return scipy_sparse_to_sympy(m)
    elif isinstance(m, Expr):
        return m
    raise TypeError('Expected sympy/numpy/scipy.sparse matrix, got: %r' % m)

def to_numpy(m, **options):
    """Convert a sympy/scipy.sparse matrix to a numpy matrix."""
    dtype = options.get('dtype','complex')
    if isinstance(m, (Matrix, Expr)):
        return sympy_to_numpy(m, dtype=dtype)
    elif isinstance(m, numpy_ndarray):
        return m
    elif isinstance(m, scipy_sparse_matrix):
        return m.todense()
    raise TypeError('Expected sympy/numpy/scipy.sparse matrix, got: %r' % m)


def to_scipy_sparse(m, **options):
    """Convert a sympy/numpy matrix to a scipy.sparse matrix."""
    dtype = options.get('dtype','complex')
    if isinstance(m,  (Matrix, Expr)):
        return sympy_to_scipy_sparse(m, dtype=dtype)
    elif isinstance(m, numpy_ndarray):
        from scipy import sparse
        return sparse.csr_matrix(m)
    elif isinstance(m, scipy_sparse_matrix):
        return m
    raise TypeError('Expected sympy/numpy/scipy.sparse matrix, got: %r' % m)


def flatten_scalar(e):
    """Flatten a 1x1 matrix to a scalar, return larger matrices unchanged."""
    if isinstance(e, Matrix):
        if e.shape == (1,1):
            e = e[0]
    if isinstance(e, (numpy_ndarray, scipy_sparse_matrix)):
        if e.shape == (1,1):
            e = complex(e[0,0])
    return e


def matrix_dagger(e):
    """Return the dagger of a sympy/numpy/scipy.sparse matrix."""
    if isinstance(e, Matrix):
        return e.H
    elif isinstance(e, (numpy_ndarray, scipy_sparse_matrix)):
        return e.conjugate().transpose()
    raise TypeError('Expected sympy/numpy/scipy.sparse matrix, got: %r' % e)


# TODO: Move this into sympy.matricies.
def _sympy_tensor_product(*matrices):
    """Compute the tensor product of a sequence of sympy Matrices.

    This is the standard Kronecker product of matrices [1].

    Parameters
    ==========
    matrices : tuple of Matrix instances
        The matrices to take the tensor product of.

    Returns
    =======
    matrix : Matrix
        The tensor product matrix.

    Examples
    ========

        >>> from sympy import I, Matrix, symbols
        >>> from sympy.physics.quantum.matrixutils import _sympy_tensor_product

        >>> m1 = Matrix([[1,2],[3,4]])
        >>> m2 = Matrix([[1,0],[0,1]])
        >>> _sympy_tensor_product(m1, m2)
        [1, 0, 2, 0]
        [0, 1, 0, 2]
        [3, 0, 4, 0]
        [0, 3, 0, 4]
        >>> _sympy_tensor_product(m2, m1)
        [1, 2, 0, 0]
        [3, 4, 0, 0]
        [0, 0, 1, 2]
        [0, 0, 3, 4]

    References
    ==========

    [1] http://en.wikipedia.org/wiki/Kronecker_product
    """
    # Make sure we have a sequence of Matrices
    testmat = [isinstance(m, Matrix) for m in matrices]
    if not all(testmat):
        raise TypeError(
            'Sequence of Matrices expected, got: %s' % repr(matrices)
        )

    # Pull out the first element in the product.
    matrix_expansion  = matrices[-1]
    # Do the tensor product working from right to left.
    for mat in reversed(matrices[:-1]):
        rows = mat.rows
        cols = mat.cols
        # Go through each row appending tensor product to.
        # running matrix_expansion.
        for i in range(rows):
            start = matrix_expansion*mat[i*cols]
            # Go through each column joining each item
            for j in range(cols-1):
                start = start.row_join(
                    matrix_expansion*mat[i*cols+j+1]
                )
            # If this is the first element, make it the start of the
            # new row.
            if i == 0:
                next = start
            else:
                next = next.col_join(start)
        matrix_expansion = next
    return matrix_expansion


def _numpy_tensor_product(*product):
    """numpy version of tensor product of multiple arguments."""
    import numpy as np
    answer = product[0]
    for item in product[1:]:
        answer = np.kron(answer, item)
    return answer


def _scipy_sparse_tensor_product(*product):
    """scipy.sparse version of tensor product of multiple arguments."""
    from scipy import sparse
    answer = product[0]
    for item in product[1:]:
        answer = sparse.kron(answer, item)
    # The final matrices will just be multiplied, so csr is a good final
    # sparse format.
    return sparse.csr_matrix(answer)


def matrix_tensor_product(*product):
    """Compute the matrix tensor product of sympy/numpy/scipy.sparse matrices."""
    if isinstance(product[0], Matrix):
        return _sympy_tensor_product(*product)
    elif isinstance(product[0], numpy_ndarray):
        return _numpy_tensor_product(*product)
    elif isinstance(product[0], scipy_sparse_matrix):
        return _scipy_sparse_tensor_product(*product)


def _numpy_eye(n):
    """numpy version of complex eye."""
    import numpy as np
    return np.matrix(np.eye(n, dtype='complex'))


def _scipy_sparse_eye(n):
    """scipy.sparse version of complex eye."""
    from scipy import sparse
    return sparse.eye(n, n, dtype='complex')


def matrix_eye(n, **options):
    """Get the version of eye and tensor_product for a given format."""
    format = options.get('format','sympy')
    if format == 'sympy':
        return matrices.eye(n)
    elif format == 'numpy':
        return _numpy_eye(n)
    elif format == 'scipy.sparse':
        return _scipy_sparse_eye(n)
    raise NotImplementedError('Invalid format: %r' % format)


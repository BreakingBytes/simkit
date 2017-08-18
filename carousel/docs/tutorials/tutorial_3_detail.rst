.. _tutorial-3-detail:

Tutorial 3: More Detail on Units and Uncertainty
================================================
In order to understand how to use units and uncertainty, let's take a careful
look at the following example of a simple formula::

    from uncertainty_wrapper import *
    from pint import UnitRegistry
    import numpy as np

    UREG = UnitRegistry()  # Pint unit registry

    def f(a, b):
        """
        Pythagorean theorem

        :param a: first leg
        :type a: int, float, np.ndarray
        :param n: second leg
        :type a: int, float, np.ndarray
        :returns: hypotenuse
        :type a: np.float64, np.ndarray
        """
        return np.sqrt(a * a + b * b)

    # test with scalar
    f(5., 12.)
    # 13.0  <- returns np.float64

    # test with vector (a Python list will raise TypeError)
    f(np.array([3., 5.]), np.array([4., 12.]))
    # array([  5.,  13.])  <- returns np.ndarray

If this formula were used in Carousel, and its attributes were set to propagate
uncertainty for all arguments by setting ``isconstant=[]``, then the formulas
would be automatically wrapped by
:func:`uncertainty_wrapper.core.unc_wrapper_args`. We'll show how this is done
explicitly to understand more about
`UncertaintyWrapper <http://pythonhosted.org/UncertaintyWrapper/>`_. ::

    # wrap function with uncertainty wrapper
    # NOTE: set `covariance_keys=None` or else uncertainaty wrapper assumes
    # arguments are grouped into a 2-D NumPy array
    g = unc_wrapper_args(None)(f)

    # test with scalar
    cov = np.array([[0.01, 0], [0, 0.01]])  # covariance fractions w/ no-units
    g(3., 4., __covariance__=cov)
    # 5.0  <- hypotenuse np.float64
    # array([[[ 0.1348]]])  <- variance = (stdev [same units as hypotenuse])^2
    # array([[[ 0.6,  0.8]]])  <- sensitivities df/da and df/db

    # test with vector
    cov = np.array([[[0.01, 0], [0, 0.01]], [[0.01, 0], [0, 0.01]]])
    try:
        g(np.array([3., 5.]), np.array([4., 12.]), __covariance__=cov)
    except ValueError as err:
        err
    # ValueError: could not broadcast input array from shape (2) into shape (2,1)

Uncertainty wrapper thinks there are two return values and only one observation,
so it tries to calculate the derivatives with respect to two return values but
there's actually the opposite. The number of observations refers to vectorized
calculations that repeat the same calculation for each independent observation,
*ie*: observations do not depend on each other. The uncertainty wrapper always
looks at the second dimension of the output to determine the number of
observations. Therefore to fix the formulas in our example, all we have to do is
reshape the output. ::

    def f_fixed(a, b):
        """
        fixed Pythagorean function for uncertainty wrapper with nobs > 1
        """
        # cast a, b to NumPy arrays so we can do vector multiplication on lists
        a, b = np.asarray(a), np.asarray(b)
        # reshape output so that it is 1 X Nobs, the number of observations
        return f(a, b).reshape(1, -1)

    # test Python list
    f_fixed([3., 5.], [4., 12.])
    # array([[  5.,  13.]])  <- returns 1 X 2 np.ndarray

    # wrap fixed function
    # NOTE: remember to set `covariance_keys=None` or else!
    g = unc_wrapper_args(None)(f_fixed)

    # test scalar
    cov = np.array([[0.01, 0], [0, 0.01]])
    g(5., 12., __covariance__=cov)
    # [13.0]  <- returns 1-D np.ndarray
    # array([[[ 1.2639645]]])
    # array([[[ 0.38461538,  0.92307692]]])

    # test vector
    # NOTE: specify covariance for each observation or else uncertainty
    # wrapper assumes there's only one argument
    cov = np.array([[[0.01, 0], [0, 0.01]], [[0.01, 0], [0, 0.01]]])
    g([3., 5.], [4., 12.], __covariance__=cov)
    # [5.0, 13.0]  <- returns 1-D np.ndarray
    # array([[[ 0.1348   ]],
    #        [[ 1.2639645]]])
    # array([[[ 0.6       ,  0.8       ]],
    #        [[ 0.38461538,  0.92307692]]])

Now that we've got uncertainty wrapper working the way we want for both scalars
and vectors, for multiple arguments, and possibly multiple return values, we can
use the Pint unit wrapper::

    # wrap the wrapped function with Pint units wrapper
    # NOTE: Carousel adds `None` units for covariance and sensitivity for you
    # but in this example we have to do it ourselves
    h = UREG.wraps(('=A', None, None), ['=A', '=A'])(g)
    # make some quantities
    a, b = [3., 5.] * UREG.cm, [4., 12.] * UREG.cm
    # don't forget to specify covariance for each observation
    cov = np.array([[[0.01, 0], [0, 0.01]], [[0.01, 0], [0, 0.01]]])
    h(a, b, __covariance__=cov)
    # <Quantity([  5.  13.], 'centimeter')>
    # array([[[ 0.1348   ]],
    #        [[ 1.2639645]]])
    # array([[[ 0.6       ,  0.8       ]],
    #        [[ 0.38461538,  0.92307692]]])

So the key takeaway is that vectorized calculations should always return a 2-D
array with the number of observations in the 2nd dimension.

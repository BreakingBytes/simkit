"""
Calculators are used to execute calculations.
"""

from carousel.core import logging, UREG
import numpy as np

LOGGER = logging.getLogger(__name__)


def index_registry(args, reg, ts=None, idx=None):
    """
    Index into a :class:`~carousel.core.Registry` to return arguments
    from :class:`~carousel.core.data_sources.DataRegistry` and
    :class:`~carousel.core.outputs.OutputRegistry` based on the
    calculation parameter file.

    :param args: Arguments field from the calculation parameter file.
    :param reg: Registry in which to index to get the arguments.
    :type reg: :class:`~carousel.core.data_sources.DataRegistry`,
        :class:`~carousel.core.outputs.OutputRegistry`
    :param ts: Time step [units of time].
    :param idx: [None] Index of current time step for dynamic calculations.

    Required arguments for static and dynamic calculations are specified in the
    calculation parameter file by the "args" key. Arguments can be from
    either the data registry or the outputs registry, which is denoted by the
    "data" and "outputs" keys. Each argument is a dictionary whose key is the
    name of the argument in the formula specified and whose value can be one of
    the following:

    * The name of the argument in the registry ::

        {"args": {"outputs": {"T_bypass": "T_bypass_diode"}}}

      maps the formula argument "T_bypass" to the outputs registry item
      "T_bypass_diode".

    * A list with the name of the argument in the registry as the first element
      and a negative integer denoting the index relative to the current
      timestep as the second element ::

        {"args": {"data": {"T_cell": ["Tcell", -1]}}}

      indexes the previous timestep of "Tcell" from the data registry.

    * A list with the name of the argument in the registry as the first element
      and a list of positive integers denoting the index into the item from the
      registry as the second element ::

        {"args": {"data": {"cov": ["bypass_diode_covariance", [2]]}}}

      indexes the third element of "bypass_diode_covariance".

    * A list with the name of the argument in the registry as the first
      element, a negative real number denoting the time relative to the current
      timestep as the second element, and the units of the time as the third ::

        {"args": {"data": {"T_cell": ["Tcell", -1, 'day']}}}

      indexes the entire previous day of "Tcell".
    """
    # TODO: move this to new Registry method or __getitem__
    # TODO: replace idx with datetime object and use timeseries to interpolate
    #       into data, not necessary for outputs since that will conform to idx
    rargs = dict.fromkeys(args)  # make dictionary from arguments
    # iterate over arguments
    for k, v in args.iteritems():
        # var           ------------------ states ------------------
        # idx           ===== not None =====    ======= None =======
        # isconstant    True    False   None    True    False   None
        # is_dynamic    no      yes     yes     no      no      no
        is_dynamic = idx and not reg.isconstant.get(v)
        # switch based on string type instead of sequence
        if isinstance(v, basestring):
            # the default assumes the current index
            rargs[k] = reg[v][idx] if is_dynamic else reg[v]
        elif len(v) < 3:
            if reg.isconstant[v[0]]:
                # only get indices specified by v[1]
                # tuples interpreted as a list of indices, see
                # NumPy basic indexing: Dealing with variable
                # numbers of indices within programs
                rargs[k] = reg[v[0]][tuple(v[1])]
            elif v[1] < 0:
                # specified offset from current index
                rargs[k] = reg[v[0]][idx + v[1]]
            else:
                # get indices specified by v[1] at current index
                rargs[k] = reg[v[0]][idx][tuple(v[1])]
        else:
            # specified timedelta from current index
            dt = 1 + (v[1] * UREG(str(v[2])) / ts).item()
            # TODO: deal with fractions of timestep
            rargs[k] = reg[v[0]][(idx + dt):(idx + 1)]
    return rargs


class Calculator(object):
    """
    Base class for calculators. Must implement ``calculate`` method.
    """
    shortname = ''

    @staticmethod
    def get_covariance(datargs, outargs, vargs, datvar, outvar):
        """
        Get covariance matrix.

        :param datargs: data arguments
        :param outargs: output arguments
        :param vargs: variable arguments
        :param datvar: variance of data arguments
        :param outvar: variance of output arguments
        :return: covariance
        """
        # number of formula arguments that are not constant
        argn = len(vargs)
        # number of observations must be the same for all vargs
        nobs = 1
        for m in xrange(argn):
            a = vargs[m]
            try:
                a = datargs[a]
            except (KeyError, TypeError):
                a = outargs[a]
                avar = outvar[a]
            else:
                avar = datvar[a]
            for n in xrange(argn):
                b = vargs[n]
                try:
                    b = datargs[b]
                except (KeyError, TypeError):
                    b = outargs[b]
                c = avar.get(b, 0.0)
                try:
                    nobs = max(nobs, len(c))
                except (TypeError, ValueError):
                    LOGGER.debug('c of %s vs %s = %g', a, b, c)
        # covariance matrix is initially zeros
        cov = np.zeros((nobs, argn, argn))
        # loop over arguments in both directions, fill in covariance
        for m in xrange(argn):
            a = vargs[m]
            try:
                a = datargs[a]
            except (KeyError, TypeError):
                a = outargs[a]
                avar = outvar[a]
            else:
                avar = datvar[a]
            for n in xrange(argn):
                b = vargs[n]
                try:
                    b = datargs[b]
                except (KeyError, TypeError):
                    b = outargs[b]
                cov[:, m, n] = avar.get(b, 0.0)
        if nobs == 1:
            cov = cov.squeeze()  # squeeze out any extra dimensions
        LOGGER.debug('covariance:\n%r', cov)
        return cov

    @classmethod
    def calculate(cls, calc, formula_reg, data_reg, out_reg,
                  timestep=None, idx=None):
        """
        Execute calculation

        :param calc: calculation, with formula, args and return keys
        :type calc: dict
        :param formula_reg: Registry of formulas.
        :type formula_reg: :class:`~carousel.core.FormulaRegistry`
        :param data_reg: Data registry.
        :type data_reg: :class:`~carousel.core.data_sources.DataRegistry`
        :param out_reg: Outputs registry.
        :type out_reg: :class:`~carousel.core.outputs.OutputRegistry`
        :param timestep: simulation interval length [time], default is ``None``
        :param idx: interval index, default is ``None``
        :type idx: int
        """
        # get the formula-key from each static calc
        formula = calc['formula']  # name of formula in calculation
        func = formula_reg[formula]  # formula function object
        fargs = formula_reg.args.get(formula, [])  # formula arguments
        constants = formula_reg.isconstant.get(formula)  # constant args
        # formula arguments that are not constant
        vargs = [] if constants is None else [a for a in fargs if a not in constants]
        args = calc['args']  # calculation arguments
        # separate data and output arguments
        datargs, outargs = args.get('data', {}), args.get('outputs', {})
        data = index_registry(datargs, data_reg, timestep, idx)
        outputs = index_registry(outargs, out_reg, timestep, idx)
        kwargs = dict(data, **outputs)  # combined data and output args
        args = [kwargs.pop(a) for a in fargs if a in kwargs]
        returns = calc['returns']  # return arguments
        # if constants is None then the covariance should also be None
        # TODO: except other values, eg: "all" to indicate no covariance
        if constants is None:
            cov = None  # do not propagate uncertainty
        else:
            # get covariance matrix
            cov = cls.get_covariance(datargs, outargs, vargs,
                                     data_reg.variance, out_reg.variance)
            # update kwargs with covariance if it exists
            kwargs['__covariance__'] = cov
        retval = func(*args, **kwargs)  # calculate function
        # update output registry with covariance and jacobian
        if cov is not None:
            # split uncertainty and jacobian from return values
            cov, jac = retval[-2:]
            retval = retval[:-2]
            # scale covariance
            scale = np.asarray(
                [1 / r.m if isinstance(r, UREG.Quantity) else 1 / r
                 for r in retval]
            )  # use magnitudes if quantities
            cov = (np.swapaxes((cov.T * scale), 0, 1) * scale).T
            nret = len(retval)  # number of return output
            for m in xrange(nret):
                a = returns[m]  # name in output registry
                out_reg.variance[a] = {}
                out_reg.uncertainty[a] = {}
                out_reg.jacobian[a] = {}
                for n in xrange(nret):
                    b = returns[n]
                    out_reg.variance[a][b] = cov[:, m, n]
                    if a == b:
                        unc = np.sqrt(cov[:, m, n]) * 100 * UREG.percent
                        out_reg.uncertainty[a][b] = unc
                for n in xrange(len(vargs)):
                    b = vargs[n]
                    try:
                        b = datargs[b]
                    except (KeyError, TypeError):
                        b = outargs[b]
                    out_reg.jacobian[a][b] = jac[:, m, n]
                LOGGER.debug('%s cov:\n%r', a, out_reg.variance[a])
                LOGGER.debug('%s jac:\n%r', a, out_reg.jacobian[a])
                LOGGER.debug('%s unc:\n%r', a, out_reg.uncertainty[a])
        # if there's only one return value, squeeze out extra dimensions
        if len(retval) == 1:
            retval = retval[0]
        # put return values into output registry
        if len(returns) > 1:
            # more than one return, zip them up
            if idx is None:
                out_reg.update(zip(returns, retval))
            else:
                for k, v in zip(returns, retval):
                    out_reg[k][idx] = v
        else:
            # only one return, get it by index at 0
            if idx is None:
                out_reg[returns[0]] = retval
            else:
                out_reg[returns[0]][idx] = retval

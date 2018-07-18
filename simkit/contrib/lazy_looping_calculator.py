"""
A lazy calculator that just loops over formulas.
"""

from simkit.core.calculators import Calculator, index_registry
from simkit.core import logging, Q_
import numpy as np

LOGGER = logging.getLogger(__name__)


# TODO: this is a hack to avoid writing a new registry indexer
# FIXME: replace this with an index_registry() method for repeat args
def reg_copy(reg, keys=None):
    """
    Make a copy of a subset of a registry.

    :param reg: source registry
    :param keys: keys of registry items to copy
    :return: copied registry subset
    """
    if keys is None:
        keys = reg.keys()
    reg_cls = type(reg)
    new_reg = reg_cls()
    mk = {}  # empty dictionary for meta keys
    # loop over registry meta names
    for m in reg_cls.meta_names:
        mstar = getattr(reg, m, None)  # current value of metakey in registry
        if not mstar:
            # if there is no value, the value is empty or None, set it to None
            # it's never false or zero, should be dictionary of reg items
            mk[m] = None
            continue
        mk[m] = {}  # emtpy dictionary of registry meta
        # loop over keys to copy and set values of meta keys for each reg item
        for k in keys:
            kstar = mstar.get(k)
            # if key exists in registry meta and is not None, then copy it
            if kstar is not None:
                mk[m][k] = kstar
    new_reg.register({k: reg[k] for k in keys}, **mk)
    return new_reg


class LazyLoopingCalculator(Calculator):
    """
    calculator that just loops over formulas
    """

    def __init__(self, repeat_args, series_arg=None):
        # TODO: change Calculations to pass parameters & meta to calculators
        # #: parameters to be read by calculator
        # self.parameters = parameters
        # #: meta if any
        # self.meta = meta
        # TODO: get repeat args from extras or meta
        #: repeat formula arguments, must be the same shape
        self.repeat_args = repeat_args
        #: argument that determines the number observations (2nd dim of retval)
        self.series_arg = series_arg

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
        c = []
        # FIXME: can just loop ver varg, don't need indices I think, do we?
        for m in xrange(argn):
            a = vargs[m]  # get the variable formula arg in vargs at idx=m
            try:
                a = datargs[a]  # get the calculation data arg
            except (KeyError, TypeError):
                a = outargs[a]  # get the calculation output arg
                if not isinstance(a, basestring):
                    # calculation arg might be sequence (arg, idx, [unit])
                    a = a[0]  # if a is a sequence, get just the arg from a[0]
                    LOGGER.debug('using output variance key: %r', a)
                avar = outvar[a]  # get variance from output registry
            else:
                if not isinstance(a, basestring):
                    # calculation arg might be sequence (arg, idx, [unit])
                    a = a[0]  # if a is a sequence, get just the arg from a[0]
                    LOGGER.debug('using data variance key: %r', a)
                avar = datvar[a]  # get variance from data registry
            d = []
            # avar is a dictionary with the variance of "a" vs all other vargs
            for n in xrange(argn):
                # FIXME: just get all of the calculation args one time
                b = vargs[n]  # get the variable formula arg in vargs at idx=n
                try:
                    b = datargs[b]  # get the calculation data arg
                except (KeyError, TypeError):
                    b = outargs[b]  # get variance from output registry
                if not isinstance(b, basestring):
                    # calculation arg might be sequence (arg, idx, [unit])
                    b = b[0]  # if a is a sequence, get just the arg from b[0]
                    LOGGER.debug('using variance key: %r', b)
                d.append(avar.get(b, 0.0))  # add covariance to sequence
                # figure out number of observations from longest covariance
                # only works if nobs is in one of the covariance
                # fails if nobs > 1, but covariance shape doesn't have nobs!!!
                # eg: if variance for data is uniform for all observations!!!
                try:
                    nobs = max(nobs, len(d[-1]))
                except (TypeError, ValueError):
                    LOGGER.debug('c of %s vs %s = %g', a, b, d[-1])
            LOGGER.debug('d:\n%r', d)
            c.append(d)
        # covariance matrix is initially zeros
        cov = np.zeros((nobs, argn, argn))
        # loop over arguments in both directions, fill in covariance
        for m in xrange(argn):
            d = c.pop()
            LOGGER.debug('pop row %d:\n%r', argn-1-m, d)
            for n in xrange(argn):
                LOGGER.debug('pop col %d:\n%r', argn - 1 - n, d[-1])
                cov[:, argn-1-m, argn-1-n] = d.pop()
        if nobs == 1:
            cov = cov.squeeze()  # squeeze out any extra dimensions
        LOGGER.debug('covariance:\n%r', cov)
        return cov

    def calculate(self, calc, formula_reg, data_reg, out_reg,
                  timestep=None, idx=None):
        """
        Calculate looping over specified repeat arguments.

        :param calc: Calculation to loop over.
        :param formula_reg: Formula registry
        :param data_reg: Data registry
        :param out_reg: Outputs registry
        :param timestep: timestep used for dynamic calcs
        :param idx: index used in dynamic calcs
        """
        # the superclass Calculator.calculate() method
        base_calculator = super(LazyLoopingCalculator, self).calculate
        # call base calculator and return if there are no repeat args
        if not self.repeat_args:
            base_calculator(calc, formula_reg, data_reg, out_reg, timestep, idx)
            return
        # make dictionaries of the calculation data and outputs argument maps
        # this maps what the formulas and registries call the repeats arguments
        data_rargs, out_rargs = {}, {}  # allocate dictionaries for repeat args
        calc_data = calc['args'].get('data')
        calc_outs = calc['args'].get('outputs')
        # get dictionaries of repeat args from calculation data and outputs
        for rarg in self.repeat_args:
            # rarg could be either data or output so try both
            try:
                data_rargs[rarg] = calc_data[rarg]
            except (KeyError, TypeError):
                out_rargs[rarg] = calc_outs[rarg]
        # get values of repeat data and outputs from registries
        rargs = dict(index_registry(data_rargs, data_reg, timestep, idx),
                     **index_registry(out_rargs, out_reg, timestep, idx))
        rargkeys, rargvals = zip(*rargs.iteritems())  # split keys and values
        rargvals = zip(*rargvals)  # reshuffle values, should be same size?
        # allocate dictionary of empty numpy arrays for each return value
        returns = calc['returns']  # return keys
        retvals = {rv: [] for rv in returns}  # empty dictionary of return vals
        retvalu = {rv: None for rv in returns}  # dictionary of return units
        ret_var = {rv: {rv: [] for rv in returns}
                   for rv in returns}  # variances
        ret_unc = {rv: {rv: [] for rv in returns}
                   for rv in returns}  # uncertainty
        ret_jac = dict.fromkeys(returns)  # jacobian
        # get calc data and outputs keys to copy from registries
        try:
            calc_data_keys = calc_data.values()
        except (AttributeError, TypeError):
            calc_data_keys = []  # if there are no data, leave it empty
        try:
            calc_outs_keys = calc_outs.values()
        except (AttributeError, TypeError):
            calc_outs_keys = []  # if there are no outputs, leave it empty
        # copy returns and this calculations output arguments from output reg
        data_reg_copy = reg_copy(data_reg, calc_data_keys)
        out_reg_copy = reg_copy(out_reg, returns + calc_outs_keys)
        # loop over first repeat arg values and enumerate numpy indices as n
        for vals in rargvals:
            rargs_keys = dict(zip(rargkeys, vals))
            # this is the magic or garbage depending on how you look at it,
            # change the registry copies to only contain the values for this
            # iteration of the repeats
            # TODO: instead of using copies rewrite index_registry to do this
            # copies means that calculations can't use a registry backend that
            # uses shared memory, which will limit ability to run asynchronously
            for k, v in data_rargs.iteritems():
                data_reg_copy[v] = rargs_keys[k]
            for k, v in out_rargs.iteritems():
                out_reg_copy[v] = rargs_keys[k]
            # run base calculator to get retvals, var, unc and jac
            base_calculator(calc, formula_reg, data_reg_copy, out_reg_copy,
                            timestep, idx)
            # re-assign retvals for this index of repeats
            for rv, rval in retvals.iteritems():
                rval.append(out_reg_copy[rv].m)  # append magnitude to returns
                retvalu[rv] = out_reg_copy[rv].u  # save units for this repeat
                # re-assign variance for this index of repeats
                if out_reg_copy.variance.get(rv) is None:
                    continue
                for rv2, rval2 in ret_var.iteritems():
                    rval2[rv].append(out_reg_copy.variance[rv2][rv])
                    # uncertainty only on diagonal of variance
                    if rv == rv2:
                        ret_unc[rv][rv2].append(out_reg_copy.uncertainty[rv][rv2])
                    else:
                        # FIXME: inefficient to get length every iteration!
                        unc_size = len(out_reg_copy.uncertainty[rv][rv])
                        ret_unc[rv][rv2].append(Q_([0.]*unc_size, 'percent'))
                # jacobian is dictionary of returns versus arguments
                if ret_jac[rv] is None:
                    # first time through create dictionary of sensitivities
                    ret_jac[rv] = {o: v for o, v in
                                   out_reg_copy.jacobian[rv].iteritems()}
                else:
                    # next time through, vstack the sensitivities to existing
                    for o, v in out_reg_copy.jacobian[rv].iteritems():
                        ret_jac[rv][o] = np.vstack((ret_jac[rv][o], v))
        LOGGER.debug('ret_jac:\n%r', ret_jac)
        # TODO: handle jacobian for repeat args and for dynamic simulations
        # apply units if they were
        for k in retvals:
            if retvalu[k] is not None:
                if retvalu[k] == out_reg[k].u:
                    retvals[k] = Q_(retvals[k], retvalu[k])
                else:
                    retvals[k] = Q_(retvals[k], retvalu[k]).to(out_reg[k].u)
        # put return values into output registry
        if idx is None:
            out_reg.update(retvals)
            out_reg.variance.update(ret_var)
            out_reg.uncertainty.update(ret_unc)
            out_reg.jacobian.update(ret_jac)
        else:
            for k, v in retvals:
                out_reg[k][idx] = v
        # FIXME: uncertainty, variance and jacobians not propagated for dynamic

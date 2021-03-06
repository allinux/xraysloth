#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DataGroup: generic container for data objects (=groups in Larch, =generic Python class)

TODO
----
- [] REFACTOR THE WHOLE THING!!!
- [] move self.getkwsd() to the respective data objects
- [] move 1D parts to datagroup1D
- [] use map() instead of for loops...
- [] use update() for kwsd: see https://github.com/xraypy/xraylarch/issues/66#issuecomment-30948135
- [] control multiple plot windows ('win' keyword argument) when
     plotting with PyMca

"""
import os, sys
import numpy as np
from datetime import datetime
from collections import deque
import glob
from scipy.interpolate import interp1d

# Larch
HAS_LARCH = False
try:
    from larch import use_plugin_path, Group
    # load Larch Plugins
    use_plugin_path('io')
    from columnfile import _read_ascii
    use_plugin_path('wx')
    from plotter import _plot, _scatterplot, _plot_text
    use_plugin_path('math')
    from mathutils import _interp
    use_plugin_path('xafs')
    from xafsft import xftf, xftr, xftf_prep, xftf_fast, xftr_fast, ftwindow
    from pre_edge import pre_edge
    HAS_LARCH = True
except ImportError:
    pass

# PyMca
HAS_PYMCA = False
try:
    from PyMca import ScanWindow
    HAS_PYMCA = True
except ImportError:
    pass

from ..io.specfile_reader import _str2rng as str2rng
from ..io.specfile_reader import spec_getmap2group, spec_getmrg2group

### GLOBAL VARIABLES ###
MODNAME = '_contrib'
DEBUG = 0

def _getfnames(grepstr, rpath=os.getcwd(), substr1=None):
    """get a list of filenames

    Arguments
    ---------
    grepstr : pattern according to the rules used by the Unix shell
    
    Keyword arguments
    -----------------
    rpath : [os.getcwd()] root path
    substr1 : [None] if given, search first level of subdirs
    
    """
    if substr1 is not None:
        return glob.glob(os.path.join(rpath, substr1, grepstr))
    else:
        return glob.glob(os.path.join(rpath, grepstr))

def _getefermi(fn):
    """get the Fermi level energy from a FDMNES out file"""
    try:
        f = open(fn)
    except:
        return 0
    l = f.readline()
    f.close()
    ef = float(l.split()[6])
    if DEBUG: print('Calculated Fermi level: {0}'.format(ef))
    return ef

def _norm(y, norm=None, **kws):
    """collection of simple normalization methods

    Parameters
    ==========
    y : array of float, to normalize
    norm : string, available options
           "max"     -> y / np.max(y)
           "max-min" -> (y - np.min(y)) / (np.max(y) - np.min(y))
           "area"    -> (y - np.min(y)) / np.trapz(y, x=kws.get('x'))
           "sum"     ->  (y - np.min(y)) / np.sum(y)
           "larch"   -> TODO!!!

    Returns
    =======
    ynorm : array of float

    """
    if norm == "max":
        return y / np.max(y)
    elif norm == "max-min":
        return (y - np.min(y)) / (np.max(y) - np.min(y))
    elif norm == "area":
        try:
            return (y - np.min(y)) / np.trapz(y, x=kws.get('x'))
        except:
            return (y - np.min(y)) / np.trapz(y)
    elif norm == "sum":
        return (y - np.min(y)) / np.sum(y)
    elif norm == "larch":
        print("TODO!")
        return y
        # try:
        #     d = DataGroupXanes()
        #     d.gs.append(Group(_larch=d._larch))
        #     d.gs[-1].x = kws.get('x')
        #     d.gs[-1].y = y
        #     d.norxafs(d.gs[-1], xattr='x', yattr='y', outattr='flat', **kws)
        #     return d.gs[-1].flat
        # except:
        #     print('ERROR: Larch normalization failed')
        #     return y
    else:
        print("WARNING: normalization method not known")
        return y

### CLASS ###
class DataGroup(object):
    """a list of groups with some wrapped methods from Larch & friends"""
    
    def __init__(self, kwsd=None, _larch=None):
        if _larch is None:
            if HAS_LARCH:
                from larch import Interpreter
                self._larch = Interpreter()
                self._inlarch = False
            else:
                raise NameError('DataGroup requires Larch')
        else:
            self._larch = _larch
            self._inlarch = True
        self.gs = deque() #deque is faster than standard lists
        ### init keyword arguments ###
        self.sel = []
        if kwsd is not None:
            self.kwsd = kwsd
        else:
            self.kwsd = self.getkwsd()

    def getigfromlabel(self, grepstr):
        """return a list of indexes where 'grepstr' is in
        self.gs.label"""
        igs = []
        for ig, g in enumerate(self.gs):
            if grepstr in g.label:
                igs.append(ig)
        igs.reverse()
        return igs

    def getfnames(self, grepstr, rpath=os.getcwd(), substr1=None):
        return _getfnames(grepstr, rpath=rpath, substr1=substr1)

    def selector(self, sel):
        """initialize a selected list of objects, self.gs_sel"""
        if sel == '*':
            self.sel = range(len(self.gs))
        elif type(sel) is str:
            self.sel = self.getigfromlabel(sel)
        elif type(sel) is list:
            self.sel = sel
        else:
            return
        self.gs_sel = deque(self.gs[_s] for _s in self.sel)

    def show(self, attr='label', sel=None, none_value=None):
        """show a given attribute ['label']"""
        if sel is not None: self.selector(sel)
        print("(sel) gs[#] : {0}".format(attr))
        for ig, g in enumerate(self.gs):
            # get the attribute
            try:
                _attr = getattr(g, attr)
            except AttributeError:
                _attr = none_value
            # check if selected
            if (ig in self.sel):
                flag_sel = '*'
            else:
                flag_sel = ' '
            # then show
            print("({0}) {1} : {2}".format(flag_sel, ig, _attr))

    def kick(self, selrng):
        """delete a given element in self.gs list"""
        def _dlist(slist):
            for ig in slist:
                try:
                    del self.gs[ig]
                except:
                    print('Error deleting gs[{}] ({})'.format(ig, self.gs[ig].label))
        if type(selrng) is list:
            if (selrng[0] < selrng[1]): selrng.reverse()
            _dlist(selrng)
        elif type(selrng) is str:
            _dlist(self.getigfromlabel(selrng))
        elif type(selrng) is int:
            _dlist([selrng])
        else:
            return

    def get(self, attr='label', sel=None, none_value=None):
        """get given attribute

        Keyword arguments
        -----------------
        attr :  ['label'] attribute to get
        sel : ['*'] selection of groups
        none_value : [None] value if the attribute does not exist
                     'pass' -> pass the AttributeError

        Returns
        -------
        List of attribute values
        """
        if sel is not None: self.selector(sel)
        def _safe_getattr(g):
            try:
                return getattr(g, attr)
            except AttributeError:
                if none_value == 'pass': pass
                else: return none_value
        return map(_safe_getattr, self.gs_sel)

    def setgroup(self, attr, value, sel=None):
        """set attribute to selected list of groups """
        if sel is not None: self.selector(sel)
        def _safe_setattr(g):
            try:
                setattr(g, str(attr), value)
            except:
                print('Error setting {0} in {1}'.format(attr, g.label))
        map(_safe_setattr, self.gs_sel)
        
    def copyattr(self, attr1, attr2):
        """copy attr1 to attr2""" 
        for _n, _g in enumerate(self.gs):
            try:
                setattr(_g, str(attr2), getattr(_g, attr1))
            except AttributeError:
                print("Attribute {0} does not exist in group {1}".format(attr1, _g.label))
        
    def getkwsd(self):
        """return a dictionary with default keyword arguments"""
        # globally setted kws:
        # self.sel = '*'
        kwsd = {'spec' : {'cntx' : 1,
                          'cnty' : None,
                          'csig' : None,
                          'cmon' : None,
                          'csec' : None,
                          'norm' : None,
                          'action' : 'average',
                          'xystep' : 0.02},
                'plot' : {'xattr' : 'x',
                          'yattr' : 'y',
                          'norm' : None,
                          'replace' : True,
                          'win' : 1,
                          'title' : None,
                          'show_legend' : True,
                          'legend_loc' : 'ur',
                          'xlabel' : None,
                          'ylabel' : None,
                          'xlabelE' : r'Energy (eV)',
                          'ylabelE' : r'$\mu(E)$',
                          'xlabelK' : r'$k \rm\, (\AA^{-1})$',
                          'ylabelK' : r'$k^2\chi(k)$',
                          'xlabelR' : r'$R \rm\, (\AA)$',
                          'ylabelR' : r'$|\chi(R)|\rm\,(\AA^{-3})$',
                          'xlabelQ' : r'$k \rm\, (\AA^{-1})$',
                          'ylabelQ' : r'$|\chi(q)|\rm\, (\AA^{-2})$',
                          'xshift' : 0,
                          'ystack' : 0,
                          'xscale' : 1,
                          'yscale' : 1,
                          'xmin' : None,
                          'xmax' : None,
                          'ymin' : None,
                          'ymax' : None},
                'interp' : {'xmin' : None,
                            'xmax' : None,
                            'xstep' : None,
                            'kind' : 'linear'},
                'pre_edge' : {'e0' : None,
                              'pre1' : -50,
                              'pre2' : -20,
                              'norm1' : 100,
                              'norm2' : 400,
                              'nvict' : 0,
                              'nnorm' : 3},
                'xftf' : {'xattr' : 'k',
                          'yattr' : 'chi',
                          'kweight' : 2,
                          'kmin' : 2.5,
                          'kmax' : 12,
                          'dk' : 1,
                          'window' : 'hanning'}}
        return kwsd

    ### DEPRECATED METHODS ###
    def _deprecated_msg(self):
        print("Deprecated: moved to DataGroup1D (update your script!)")
    def mkftf(self, *args, **kwargs):
        return self._deprecated_msg()
    def mkchikw(self, *args, **kwargs):
        return self._deprecated_msg()
    def getcom(self, *args, **kwargs):
        return self._deprecated_msg()
    def norint(self, *args, **kwargs):
        return self._deprecated_msg()        
    def normax(self, *args, **kwargs):
        return self._deprecated_msg()
    def norxafs(self, *args, **kwargs):
        return self._deprecated_msg()
    def scale_kwin(self, *args, **kwargs):
        return self._deprecated_msg()
    def plotexa(self, *args, **kwargs):
        return self._deprecated_msg()
    def read_ascii(self, *args, **kwargs):
        return self._deprecated_msg()
    def getxy(self, *args, **kwargs):
        return self._deprecated_msg()
    def getspecscan(self, *args, **kwargs):
        return self._deprecated_msg()
    def getspecmap(self, *args, **kwargs):
        return self._deprecated_msg()
    def xcalib(self, *args, **kwargs):
        return self._deprecated_msg()
    def mkiads(self, *args, **kwargs):
        return self._deprecated_msg()
    def plotxy(self, *args, **kwargs):
        return self._deprecated_msg()
    def plotiads(self, *args, **kwargs):
        return self._deprecated_msg()
    def load(self, *args, **kwargs):
        return self._deprecated_msg()

### LARCH ###    
def datagroup(kwsd=None, _larch=None):
    """ utility to perform common operations on a list of data groups """
    return DataGroup(kwsd=kwsd, _larch=_larch)
   
def registerLarchPlugin():
    return (MODNAME, {'datagroup': datagroup})

if __name__ == '__main__':
    pass

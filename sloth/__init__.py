#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sloth: some utilies for x-ray spectroscopists

Naming
======

* classes MixedUpperCase
* varables lowerUpper _or_ lower
* functions underscore_separated _or_ lowerUpper

"""
from __future__ import absolute_import, print_function, division

__author__ = "Mauro Rovezzi"
__version__ = "0.2.0"

import os, sys
_libDir = os.path.dirname(os.path.realpath(__file__))
#sys.path.append(_libDir)

__pkgs__ = ['sloth',
            'sloth.collects',   #data containers
            'sloth.io',         #input-output
            'sloth.fit',        #fit
            'sloth.gui',        #graphical user interface widgets
            'sloth.math',       #math&friends
            'sloth.raytracing', #ray tracing
            'sloth.rixs',       #rixs
            'sloth.test',       #test suite
            'sloth.utils'       #utilities
            ]


#__all__ = ['a', 'b', 'c']

if __name__ == '__main__':
    pass

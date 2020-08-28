#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 13:59:11 2018
pri
@author: oscartinney
"""

state_vars = ['lastCMDvalid',
              'elDeg',
              'elSteps',
              'azDeg',
              'azSteps',
              'axis',
              'mode',
              'sense',
              'elEnable',
              'azEnable',
              'voltage',
              'el_lower_limit',
              'ax',
              'ay',
              'az',
              'mx',
              'my',
              'mz',
              'pitch',
              'roll',
              'heading'
              ]

state_dtypes=['<U16', #'string',
              'float64',
              'int64',
              'float64',
              'int64',
              '<U16', #'string',,
              '<U16', #'string',
              'int64',
              'int',
              'int',
              'float64',
              'int',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64'
             ]

state = {}
for state_var in state_vars:
    state[state_var] = []

offsets = {'azoff': 0.0,
           'eloff': 0.0}

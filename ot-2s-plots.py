#!/usr/bin/env python2

""" Extract all plots from Middleware scan. """

from plots import plots

if __name__ == "__main__":

    plots = plots('rootfiles/Commissioning_fitS0_CBCall_maskNone_0.root', 'test01/')
    #plots.getAllPlots()
    plots.getScurvePerCbc([0, 1])

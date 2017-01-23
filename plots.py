#!/usr/bin/env python

""" Extract all plots from Middleware scan. """

from os import makedirs, chdir, getcwd, path
from ROOT import TFile, TCanvas

class plots(object):

    """ Extract all plots from Middleware scan. """

    def __init__(self, inputfile, outputfolder=''):

        """ Initialize object variables. """

        self._rootfile = TFile(inputfile)
        self._directory = outputfolder
        self._canvas = TCanvas()
        makedirs(outputfolder)

    def getAllPlots(self):

        """ Get all the plots. """

        for kname in self._getKeys():

            # Clear all objects from canvas
            self._canvas.Clear()

            # Get histogram and draw it
            histo = self._rootfile.Get(kname)
            histo.Draw()

            # Save it as pdf
            self._save(kname)

    def _getKeys(self, subdir=None):

        """ Loop over all keys in a given subfolder. """

        # If subdir is defined, loop over keys in folder, otherwise loop over
        # keys in rootfile
        if subdir:

            obj = self._rootfile.Get(subdir)
        else:
            obj = self._rootfile

        # Loop over all keys
        for key in obj.GetListOfKeys():

            if subdir:
                kname = '{}/{}'.format(subdir, key.GetName())
            else:
                kname = key.GetName()

            # If key is a folder, go into that folder and loop over all keys
            if key.IsFolder():
                for knamesub in self._getKeys(kname):
                    yield knamesub
            else:
                yield kname

    def _save(self, name):

        """ Save histogram as *.pdf. """

        # Go into directory if it is defined
        if self._directory:
            cwd = getcwd()

            # Create directory on filesystem
            if not path.exists(self._directory):
                makedirs(self._directory)
            chdir(self._directory)

        # If canvas is to be stored in a subdirectory, create it
        if '/' in name:
            subdir = name[:name.find('/')]
            if not path.exists(subdir):
                makedirs(subdir)

        self._canvas.SaveAs('{}.pdf'.format(name))

        # Go back to original working directories
        if self._directory:
            chdir(cwd)

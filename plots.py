#!/usr/bin/env python

""" Extract all plots from Middleware scan. """

from os import makedirs, chdir, getcwd, path
from ROOT import TFile, TCanvas, Math, TF1, TH1F

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

    def getScurvePerCbc(self, cbcs=range(0, 8)):

        """ Fit all Scurves and put them into one histogram. Also plot shifts
        (offsets) and widths (noise).
        Parameters:
            cbcs: List of CBC's to plot
        """

        for cbc in cbcs:
            self._drawScurves(cbc)

    def _drawScurves(self, cbc):

        """ Make the fits to draw the Scurves.
        Parameters:
            cbc: CBC to plot
        """

        dirname = 'Final0'

        # Need to make histograms persistens
        histos = []

        # Also store fit results
        shifts = []  # offset
        widths = []  # noise

        # Loop over all keys in subdirectory
        for kname in self._getKeys(dirname):

            # Only select S-Curves
            if not kname.startswith('{}/Scurve_Be0_Fe0_Cbc{}'
                                    .format(dirname, cbc)):
                continue

            # Error function with guessed parameters
            errf = TF1('errf', '.5 + .5*erf((x-[0])/[1])', 0., 254.)
            errf.SetParameter(0, 120.)  # shift
            errf.SetParameter(1, 10.)  # width

            # Fit
            histo = self._rootfile.Get(kname)
            histo.Fit('errf', 'RQ')

            histo.Draw()

            # Save it as pdf
            self._save('{}_fit'.format(kname))

            # Save values for future use
            histos.append(histo)
            shifts.append(histo.GetFunction('errf').GetParameter(0))
            widths.append(histo.GetFunction('errf').GetParameter(1))

        # Draw all error functions in one histogram
        self._draw_all_errf(histos, shifts, widths, cbc)

        # Draw all fitted error functions in one histogram
        self._draw_all_errf_fit(histos, shifts, widths, cbc)

    def _draw_all_errf(self, histos, shifts, widths, cbc):

        """ Draw all error functions in one histogram
        Parameters:
            histos: List of histograms with fitted error functions
            shifts: List of shifts used for fitting error functions
            widths: List of widths used for fitting error functions
            cbc: CBC to plot
        """

        self._canvas.Clear()

        for idx, histo in enumerate(histos):

            # Dynamically set plot range
            histo.GetXaxis().SetRangeUser(min([shift-2*width for shift, width
                                               in zip(shifts, widths)]),
                                          max([shift+2*width for shift, width
                                               in zip(shifts, widths)]))
            # Colors!
            histo.SetLineColor(self._getColor(idx))

            if idx == 0:
                histo.Draw('C HIST')
                histo.SetTitle('S-curves for CBC {}'.format(cbc))
                histo.GetXaxis().SetTitle('VCth units')
                histo.GetYaxis().SetTitle('Occupancy')
            else:
                histo.Draw('C HIST SAME')

        self._save('scurves_cbc{}'.format(cbc))
        self._canvas.SetLogy()
        self._save('scurves_cbc{}_log'.format(cbc))
        self._canvas.SetLogy(False)

    def _draw_all_errf_fit(self, histos, shifts, widths, cbc):

        """ Draw all error functions in one histogram
        Parameters:
            histos: List of histograms with fitted error functions
            shifts: List of shifts used for fitting error functions
            widths: List of widths used for fitting error functions
            cbc: CBC to plot
        """

        self._canvas.Clear()

        for idx, histo in enumerate(histos):

            # Get fitted function
            func = histo.GetFunction('errf')
            # Dynamically set plot range
            func.SetRange(min([shift-2*width for shift, width
                               in zip(shifts, widths)]),
                          max([shift+2*width for shift, width
                               in zip(shifts, widths)]))

            # Colors!
            func.SetLineColor(self._getColor(idx))

            if idx == 0:
                func.Draw()
                func.SetTitle('Fitted S-curves for CBC {}'.format(cbc))
                func.GetXaxis().SetTitle('VCth units')
                func.GetYaxis().SetTitle('Occupancy')
            else:
                func.Draw('SAME')

        self._save('scurves_cbc{}_fit'.format(cbc))

    def _getKeys(self, subdir=None):

        """ Loop over all keys in a given subfolder.
        Parameters:
            subdir: Get keys only from that directory, including all
                    subdirectories
        """

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

        """ Save histogram as *.pdf.
        Parameters:
            name: Name of *.pdf, possibly including path; directories are
                  created on the fly
        """

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

    def _getColor(self, idx):

        """ Get color for a given index (channel).
        Parameters:
            idx: Channel number
        """

        # List with all colors
        colors = []
        colors.extend(range(390, 405))
        colors.extend(range(406, 421))
        colors.extend(range(422, 437))
        colors.extend(range(590, 605))
        colors.extend(range(606, 621))
        colors.extend(range(622, 637))
        colors.extend(range(791, 911))
        return colors[idx % len(colors)]

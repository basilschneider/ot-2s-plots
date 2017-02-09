#!/usr/bin/env python

""" Extract all plots from Middleware scan. """

import logging
from os import makedirs, chdir, getcwd, path
from ROOT import TFile, TCanvas, Math, TF1, gStyle

# Set up logger
# DEBUG (10), INFO (20), WARNING(30), ERROR(40), CRITICAL(50)
logging.basicConfig(format='%(levelname)-8s - %(message)s',
                    level=logging.INFO)
LGR = logging.getLogger(__name__)

class plots(object):

    """ Extract all plots from Middleware scan. """

    def __init__(self, inputfile, outputfolder=''):

        """ Initialize object variables. """

        self._rootfile = TFile(inputfile)
        self._directory = outputfolder
        self._canvas = TCanvas()
        self._histos = []
        self._shifts = []
        self._widths = []
        makedirs(outputfolder)
        gStyle.SetOptStat(000000000)

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

    def getScurvePerCbc(self, cbcs=range(0, 8), channels=-1):

        """ Fit all Scurves and put them into one histogram. Also plot shifts
        (offsets) and widths (noise).
        Parameters:
            cbcs: List of CBC's to plot
            channels: Number of channels to plot; -1 for all
        """

        for cbc in cbcs:
            self._drawScurves(cbc, channels)

    def _drawScurves(self, cbc, channels):

        """ Make the fits to draw the Scurves.
        Parameters:
            cbc: CBC to plot
            channels: Number of channels to plot; -1 for all
        """

        dirname = 'Final0'

        count = 0

        # Loop over all keys in subdirectory
        for kname in self._getKeys(dirname):

            # Only plot a limited number of channels
            if channels > 0 and count >= channels:
                break

            # Only select S-Curves of a given CBC
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

            # If fit failed, skip it
            try:
                histo.GetFunction('errf').GetParameter(0)
            except TypeError:
                continue

            # Colors!
            histo.SetLineColor(self._getColor(count, (channels>0 and channels<19)))
            histo.SetMarkerColor(self._getColor(count, (channels>0 and channels<19)))
            histo.GetFunction('errf').SetLineColor(self._getColor(count, (channels>0 and channels<19)))

            # Markers!
            histo.SetMarkerStyle(count % 15 + 20)
            histo.SetMarkerSize(.8)

            # Save values for future use
            # Only save them if the fit worked
            self._shifts.append(histo.GetFunction('errf').GetParameter(0))
            self._widths.append(histo.GetFunction('errf').GetParameter(1))
            self._histos.append(histo)

            # Save histogram with fit
            histo.Draw()
            self._save('{}_fit'.format(kname))

            # Save smoothed histogram
            histo.Draw('C HIST')
            self._save('{}_smooth'.format(kname))

            # Count the number of histograms
            count += 1

        # Draw all error functions in one histogram
        self._draw_all_errf(cbc)

        # Draw all fitted error functions in one histogram
        self._draw_all_errf_fit(cbc)

        # Draw all fitted error functions and measurements in one histogram
        self._draw_all_errf_fit_meas(cbc)

    def _draw_all_errf(self, cbc):

        """ Draw all error functions in one histogram
        Parameters:
            cbc: CBC to plot
        """

        self._canvas.Clear()

        for idx, histo in enumerate(self._histos):

            if idx == 0:
                # Dynamically set plot range
                histo.GetXaxis().SetRangeUser(self._getXmin(), self._getXmax())
                histo.Draw('C HIST')
                histo.SetTitle('S-curves for CBC {}'.format(cbc))
                histo.GetXaxis().SetTitle('VCth units')
                histo.GetYaxis().SetTitle('Occupancy')
            else:
                histo.Draw('C HIST SAME')

        self._save('scurves_cbc{}'.format(cbc))
        self._save('scurves_cbc{}_log'.format(cbc), True)

    def _draw_all_errf_fit(self, cbc):

        """ Draw all error functions in one histogram
        Parameters:
            cbc: CBC to plot
        """

        self._canvas.Clear()

        for idx, histo in enumerate(self._histos):

            # Get fitted function
            func = histo.GetFunction('errf')

            if idx == 0:
                # Dynamically set plot range
                func.SetRange(self._getXmin(), self._getXmax())
                func.Draw()
                func.SetTitle('Fitted S-curves for CBC {}'.format(cbc))
                func.GetXaxis().SetTitle('VCth units')
                func.GetYaxis().SetTitle('Occupancy')
            else:
                func.Draw('SAME')

        self._save('scurves_cbc{}_fit'.format(cbc))
        self._save('scurves_cbc{}_fit_log'.format(cbc), True)

    def _draw_all_errf_fit_meas(self, cbc):

        """ Draw all error functions in one histogram
        Parameters:
            cbc: CBC to plot
        """

        self._canvas.Clear()

        for idx, histo in enumerate(self._histos):

            if idx == 0:
                # Dynamically set plot range
                histo.GetXaxis().SetRangeUser(self._getXmin(), self._getXmax())
                histo.Draw('P')
                histo.SetTitle('Fitted S-curves for CBC {}'.format(cbc))
                histo.GetXaxis().SetTitle('VCth units')
                histo.GetYaxis().SetTitle('Occupancy')
            else:
                histo.Draw('P SAME')

        self._save('scurves_cbc{}_fit_meas'.format(cbc))
        self._save('scurves_cbc{}_fit_meas_log'.format(cbc), True)

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

    def _save(self, name, logy=False):

        """ Save histogram as *.pdf.
        Parameters:
            name: Name of *.pdf, possibly including path; directories are
                  created on the fly
            logy: Plot Y-axis in log
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

        # Set Y-axis to log if requested
        if logy:
            self._canvas.SetLogy()
            # This is probably not failsafe, empirically, the first primitive
            # is the frame, the second one an object, if this is not the case,
            # it might fail
            try:
                self._canvas.GetListOfPrimitives().At(1).GetYaxis().SetRangeUser(1e-7, 2.)
            except AttributeError:
                LGR.warning('Cannot set Y-Axis to log')

        # Save as *.pdf
        self._canvas.SaveAs('{}.pdf'.format(name))

        # Unset log scale
        if logy:
            self._canvas.SetLogy(False)
            try:
                self._canvas.GetListOfPrimitives().At(1).GetYaxis().SetRangeUser(1e-7, 1.05)
            except AttributeError:
                pass

        # Go back to original working directories
        if self._directory:
            chdir(cwd)

    def _getXmin(self):

        """ Get minimum on X-Axis to plot.
        """

        return min([shift-5*width for shift, width in
                    zip(self._shifts, self._widths)])

    def _getXmax(self):

        """ Get maximum on X-Axis to plot.
        """

        return max([shift+5*width for shift, width in
                    zip(self._shifts, self._widths)])

    def _getColor(self, idx, nice=False):

        """ Get color for a given index (channel).
        Parameters:
            idx: Channel number
            nice: if True, get a handful of easily distinguishable colors; if
                  False, get all colors
        """

        # List with all colors
        colors = []
        if nice:
            colors.extend(range(2, 10))
        else:
            #colors.extend(range(390, 405))
            colors.extend(range(394, 405))
            colors.extend(range(406, 421))
            colors.extend(range(422, 437))
            colors.extend(range(590, 605))
            colors.extend(range(606, 621))
            colors.extend(range(622, 637))
            colors.extend(range(791, 911))

        return colors[idx % len(colors)]

# Copyright 2021 Mechanics of Microstructures Group
#    at The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from matplotlib.widgets import Button, TextBox
from matplotlib.collections import LineCollection
from matplotlib_scalebar.scalebar import ScaleBar
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import FuncFormatter

from skimage import morphology as mph

from defdap import defaults
from defdap import quat

# TODO: add plot parameter to add to current figure


class Plot(object):
    """ Class used for creating and manipulating plots.

    """

    def __init__(self, ax=None, ax_params={}, fig=None, make_interactive=False,
                 title=None, **kwargs):
        self.interactive = make_interactive
        if make_interactive:
            if fig is not None and ax is not None:
                self.fig = fig
                self.ax = ax
            else:
                # self.fig, self.ax = plt.subplots(**kwargs)
                self.fig = plt.figure(**kwargs)
                self.ax = self.fig.add_subplot(111, **ax_params)
            self.btnStore = []
            self.txtStore = []
            self.txtBoxStore = []
            self.p1 = []
            self.p2 = []

        else:
            self.fig = fig
            # TODO: flag for new figure
            if ax is None:
                self.fig = plt.figure(**kwargs)
                self.ax = self.fig.add_subplot(111, **ax_params)
            else:
                self.ax = ax
        self.colour_bar = None
        self.arrow = None

        if title is not None:
            self.set_title(title)

    def check_interactive(self):
        """Checks if current plot is interactive.

        Raises
        -------
        Exception
            If plot is not interactive

        """
        if not self.interactive:
            raise Exception("Plot must be interactive")

    def add_event_handler(self, eventName, eventHandler):
        self.check_interactive()

        self.fig.canvas.mpl_connect(eventName, lambda e: eventHandler(e, self))

    def add_axes(self, loc, proj='2d'):
        """Add axis to current plot

        Parameters
        ----------
        loc
            Location of axis.
        proj : str, {2d, 3d}
            2D or 3D projection.

        Returns
        -------
        matplotlib.Axes.axes

        """
        if proj == '2d':
            return self.fig.add_axes(loc)
        if proj == '3d':
            return Axes3D(self.fig, rect=loc, proj_type='ortho', azim=270, elev=90)

    def add_button(self, label, click_handler, loc=(0.8, 0.0, 0.1, 0.07), **kwargs):
        """Add a button to the plot.

        Parameters
        ----------
        label : str
            Label for the button.
        click_handler
            Click handler to assign.
        loc : list(float), len 4
            Left, bottom, width, height.
        kwargs
            All other arguments passed to :class:`matplotlib.widgets.Button`.

        """
        self.check_interactive()
        btnAx = self.fig.add_axes(loc)
        btn = Button(btnAx, label, **kwargs)
        btn.on_clicked(lambda e: click_handler(e, self))

        self.btnStore.append(btn)

    def add_text_box(self, label, submit_handler=None, change_handler=None, loc=(0.8, 0.0, 0.1, 0.07), **kwargs):
        """Add a text box to the plot.

        Parameters
        ----------
        label : str
            Label for the button.
        submit_handler
            Submit handler to assign.
        change_handler
            Change handler to assign.
        loc : list(float), len 4
            Left, bottom, width, height.
        kwargs
            All other arguments passed to :class:`matplotlib.widgets.TextBox`.

        Returns
        -------
        matplotlotlib.widgets.TextBox

        """
        self.check_interactive()
        txtBoxAx = self.fig.add_axes(loc)
        txtBox = TextBox(txtBoxAx, label, **kwargs)
        if submit_handler != None:
            txtBox.on_submit(lambda e: submit_handler(e, self))
        if change_handler != None:
            txtBox.on_text_change(lambda e: change_handler(e, self))

        self.txtBoxStore.append(txtBox)

        return txtBox

    def add_text(self, ax, x, y, txt, **kwargs):
        """Add text to the plot.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Matplotlib axis to plot on.
        x : float
            x position.
        y : float
            y position.
        txt : str
            Text to write onto the plot.

        kwargs :
            All other arguments passed to :func:`matplotlib.pyplot.text`.

        """
        txt = ax.text(x, y, txt, **kwargs)
        self.txtStore.append(txt)

    def add_arrow(self, start_end, persistent=False, clear_previous=True, label=None):
        """Add arrow to grain plot.

        Parameters
        ----------
        start_end: 4-tuple
            Starting (x, y), Ending (x, y).
        persistent :
            If persistent, do not clear arrow with clearPrev.
        clear_previous :
            Clear all non-persistent arrows.
        label
            Label to place near arrow.

        """

        arrow_params = {
            'xy': start_end[0:2],  # Arrow start coordinates
            'xycoords': 'data',
            'xytext': start_end[2:4],  # Arrow end coordinates
            'textcoords': 'data',
            'arrowprops': dict(arrowstyle="<-", connectionstyle="arc3",
                               color='red', alpha=0.7, linewidth=2,
                               shrinkA=0, shrinkB=0)
        }

        # If persisent, add the arrow onto the plot directly
        if persistent:
            self.ax.annotate("", **arrow_params)

        # If not persistent, save a reference so that it can be removed later
        if not persistent:
            if clear_previous and (self.arrow is not None): self.arrow.remove()
            if None not in start_end:
                self.arrow = self.ax.annotate("", **arrow_params)

        # Add a label if specified
        if label is not None:
            self.ax.annotate(label, xy=start_end[2:4], xycoords='data',
                             xytext=(15, 15), textcoords='offset pixels',
                             c='red', fontsize=14, fontweight='bold')

    def set_size(self, size):
        """Set size of plot.

        Parameters
        ----------
        size : float, float
            Width and height in inches.

        """
        self.fig.set_size_inches(size[0], size[1], forward=True)

    def set_title(self, txt):
        """Set title of plot.

        Parameters
        ----------
        txt : str
            Title to set.

        """
        if self.fig.canvas.manager is not None:
            self.fig.canvas.manager.set_window_title(txt)

    def line_slice(self, event, plot, action=None):
        """ Catch click and drag then draw an arrow.

        Parameters
        ----------
        event :
            Click event.
        plot : defdap.plotting.Plot
            Plot to capture clicks from.
        action
            Further action to perform.

        Examples
        ----------
        To use, add a click and release event handler to your plot, pointing to this function:

        >>> plot.add_event_handler('button_press_event',lambda e, p: line_slice(e, p))
        >>> plot.add_event_handler('button_release_event', lambda e, p: line_slice(e, p))

        """
        # check if click was on the map
        if event.inaxes is not self.ax:
            return

        if event.name == 'button_press_event':
            self.p1 = (event.xdata, event.ydata)  # save 1st point
        elif event.name == 'button_release_event':
            self.p2 = (event.xdata, event.ydata)  # save 2nd point
            self.add_arrow(start_end=(self.p1[0], self.p1[1], self.p2[0], self.p2[1]))
            self.fig.canvas.draw_idle()

            if action is not None:
                action(plot=self, startEnd=(self.p1[0], self.p1[1], self.p2[0], self.p2[1]))

    @property
    def exists(self):
        self.check_interactive()

        return plt.fignum_exists(self.fig.number)

    def clear(self):
        """Clear plot.

        """
        self.check_interactive()

        if self.colour_bar is not None:
            self.colour_bar.remove()
            self.colour_bar = None
        self.ax.clear()
        self.draw()

    def draw(self):
        """Draw plot

        """
        self.fig.canvas.draw()


class MapPlot(Plot):
    """ Class for creating a map plot.

    """

    def __init__(self, calling_map, fig=None, ax=None, ax_params={},
                 make_interactive=False, **kwargs):
        """Initialise a map plot.

        Parameters
        ----------
        calling_map : Map
            DIC or EBSD map which called this plot.
        fig : matplotlib.figure.Figure
            Matplotlib figure to plot on
        ax : matplotlib.axes.Axes
            Matplotlib axis to plot on
        ax_params :
            Passed to defdap.plotting.Plot as ax_params.
        make_interactive : bool, optional
            If true, make interactive
        kwargs
            Other arguments passed to :class:`defdap.plotting.Plot`.
        """
        super(MapPlot, self).__init__(
            ax, ax_params=ax_params, fig=fig, make_interactive=make_interactive,
            **kwargs
        )

        self.calling_map = calling_map
        self.img_layers = []
        self.highlightsLayerID = None
        self.points_layer_ids = []

        self.ax.set_xticks([])
        self.ax.set_yticks([])

    def add_map(self, map_data, vmin=None, vmax=None, cmap='viridis', **kwargs):
        """Add a map to a plot.

        Parameters
        ----------
        map_data : numpy.ndarray
            Map data to plot.
        vmin : float
            Minimum value for the colour scale.
        vmax : float
            Maximum value for the colour scale.
        cmap
            Colour map.
        kwargs
            Other arguments are passed to :func:`matplotlib.pyplot.imshow`.

        Returns
        -------
        matplotlib.image.AxesImage

        """
        img = self.ax.imshow(map_data, vmin=vmin, vmax=vmax,
                             interpolation='None', cmap=cmap, **kwargs)
        self.draw()

        self.img_layers.append(img)

        return img

    def add_colour_bar(self, label, layer=0, **kwargs):
        """Add a colour bar to plot.

        Parameters
        ----------
        label : str
            Label for the colour bar.
        layer : int
            Layer ID.
        kwargs
            Other arguments are passed to :func:`matplotlib.pyplot.colorbar`.

        """
        img = self.img_layers[layer]
        self.colour_bar = plt.colorbar(img, ax=self.ax, label=label, **kwargs)

    def add_scale_bar(self, scale=None):
        """Add scale bar to plot.

        Parameters
        ----------
        scale : float
            Size of a pixel in microns.

        """
        if scale is None:
            scale = self.calling_map.scale
        self.ax.add_artist(ScaleBar(scale * 1e-6))

    def add_grain_boundaries(self, kind="pixel", boundaries=None, colour=None,
                             dilate=False, draw=True, **kwargs):
        """Add grain boundaries to the plot.

        Parameters
        ----------
        kind : str, {"pixel", "line"}
            Type of boundaries to plot, either a boundary image or a
            collection of line segments.
        boundaries : various, optional
            Boundaries to plot, either a boundary image or a list of pairs
            of coordinates representing the start and end of each boundary 
            segment. If not provided the boundaries are loaded from the 
            calling map.
        colour : various
            One of:
              - Colour of all boundaries as a string (only option pixel kind)
              - Colour of all boundaries as RGBA tuple
              - List of values to represent colour of each line relative to a
                `norm` and `cmap`
        dilate : bool
            If true, dilate the grain boundaries.
        kwargs
            If line kind then other arguments are passed to 
            :func:`matplotlib.collections.LineCollection`.

        Returns
        -------
        Various :
            matplotlib.image.AxesImage if type is pixel

        """
        if colour is None:
            colour = "white"

        if boundaries is None:
            boundaries = self.calling_map.data.grain_boundaries

        if kind == "line":
            if isinstance(colour, str):
                colour = mpl.colors.to_rgba(colour)

            boundary_lines = boundaries
            if boundary_lines is None:
                boundary_lines = self.callingMap.boundaryLines
            
            if len(colour) == len(boundary_lines):
                colour_array = colour
                colour_lc = None
            elif len(colour) == 4:
                colour_array = None
                colour_lc = colour
            else:
                ValueError('Issue with passed colour')
                
            boundary_lines = boundaries
            if boundary_lines is None:
                boundary_lines = self.callingMap.boundaryLines

            lc = LineCollection(boundary_lines, colors=colour_lc, **kwargs)
            lc.set_array(colour_array)
            img = self.ax.add_collection(lc)

        else:
            boundaries_image = boundaries.image.astype(int)

            if dilate:
                boundaries_image = mph.binary_dilation(boundaries_image)

            # create colourmap for boundaries going from transparent to
            # opaque of the given colour
            boundaries_cmap = mpl.colors.LinearSegmentedColormap.from_list(
                'my_cmap', ['white', colour], 256
            )
            boundaries_cmap._init()
            boundaries_cmap._lut[:, -1] = np.linspace(0, 1, boundaries_cmap.N + 3)

            img = self.ax.imshow(boundaries_image, cmap=boundaries_cmap,
                                 interpolation='None', vmin=0, vmax=1)

        if draw:
            self.draw()
        self.imgLayers.append(img)
        return img

    def add_grain_highlights(self, grain_ids, grain_colours=None, alpha=None,
                             new_layer=False):
        """Highlight grains in the plot.

        Parameters
        ----------
        grain_ids : list
            List of grain IDs to highlight.
        grain_colours :
            Colour to use for grain highlight.
        alpha : float
            Alpha (transparency) to use for grain highlight.
        new_layer : bool
            If true, make a new layer in img_layers.

        Returns
        -------
        matplotlib.image.AxesImage

        """
        if grain_colours is None:
            grain_colours = ['white']
        if alpha is None:
            alpha = self.calling_map.highlight_alpha

        outline = np.zeros(self.calling_map.shape, dtype=int)
        for i, grainId in enumerate(grain_ids, start=1):
            if i > len(grain_colours):
                i = len(grain_colours)

            # outline of highlighted grain
            grain = self.calling_map.grains[grainId]
            grainOutline = grain.grainOutline(bg=0, fg=i)
            x0, y0, xmax, ymax = grain.extreme_coords

            # add to highlight image
            outline[y0:ymax + 1, x0:xmax + 1] += grainOutline

        # Custom colour map where 0 is transparent white for bg and
        # then a patch for each grain colour
        grain_colours.insert(0, 'white')
        highlightsCmap = mpl.colors.ListedColormap(grain_colours)
        highlightsCmap._init()
        alphaMap = np.full(highlightsCmap.N + 3, alpha)
        alphaMap[0] = 0
        highlightsCmap._lut[:, -1] = alphaMap

        if self.highlightsLayerID is None or new_layer:
            img = self.ax.imshow(outline, interpolation='none',
                                 cmap=highlightsCmap)
            if self.highlightsLayerID is None:
                self.highlightsLayerID = len(self.img_layers)
            self.img_layers.append(img)
        else:
            img = self.img_layers[self.highlightsLayerID]
            img.set_data(outline)
            img.set_cmap(highlightsCmap)
            img.autoscale()

        self.draw()

        return img

    def addGrainNumbers(self, fontsize=10, **kwargs):
        """Add grain numbers to a map.

        Parameters
        ----------
        fontsize : float
            Font size.
        kwargs
            Pass other arguments to :func:`matplotlib.pyplot.text`.

        """
        for grainID, grain in enumerate(self.calling_map):
            xCentre, yCentre = grain.centreCoords(centreType="com",
                                                  grainCoords=False)

            self.ax.text(xCentre, yCentre, grainID,
                         fontsize=fontsize, **kwargs)
        self.draw()

    def add_legend(self, values, labels, layer=0, **kwargs):
        """Add a legend to a map.

        Parameters
        ----------
        values : list
            Values to find colour patched for.
        labels : list
            Labels to assign to values.
        layer : int
            Image layer to generate legend for.
        kwargs
            Pass other arguments to :func:`matplotlib.pyplot.legend`.

        """
        # Find colour values for given values
        img = self.img_layers[layer]
        colors = [img.cmap(img.norm(value)) for value in values]

        # Get colour patches for each phase and make legend
        patches = [mpl.patches.Patch(
            color=colors[i], label=labels[i]
        ) for i in range(len(values))]

        self.ax.legend(handles=patches, **kwargs)

    def add_points(self, x, y, updateLayer=None, **kwargs):
        """Add points to plot.

        Parameters
        ----------
        x : list of float
            x coordinates
        y : list of float
            y coordinates
        updateLayer : int, optional
            Layer to place points on
        kwargs
            Other arguments passed to :func:`matplotlib.pyplot.scatter`.

        """
        x, y = np.array(x), np.array(y)
        if len(self.points_layer_ids) == 0 or updateLayer is None:
            points = self.ax.scatter(x, y, **kwargs)
            self.points_layer_ids.append(len(self.img_layers))
            self.img_layers.append(points)
        else:
            points = self.img_layers[self.points_layer_ids[updateLayer]]
            points.set_offsets(np.hstack((x[:, np.newaxis], y[:, np.newaxis])))

        self.draw()

        return points

    @classmethod
    def create(
            cls, callingMap, mapData,
            fig=None, fig_params={}, ax=None, ax_params={},
            plot=None, make_interactive=False,
            plot_colour_bar=False, vmin=None, vmax=None, cmap=None, clabel="",
            plotGBs=False, dilateBoundaries=False, boundaryColour=None,
            plot_scale_bar=False, scale=None,
            highlightGrains=None, highlightColours=None, highlightAlpha=None,
            **kwargs
    ):
        """Create a plot for a map.

        Parameters
        ----------
        callingMap : base.Map
            DIC or EBSD map which called this plot.
        mapData : numpy.ndarray
            Data to be plotted.
        fig : matplotlib.figure.Figure
            Matplotlib figure to plot on.
        fig_params :
            Passed to defdap.plotting.Plot.
        ax : matplotlib.axes.Axes
            Matplotlib axis to plot on.
        ax_params :
            Passed to defdap.plotting.Plot as ax_params.
        plot : defdap.plotting.Plot
            If none, use current plot.
        make_interactive :
            If true, make plot interactive
        plot_colour_bar : bool
            If true, plot a colour bar next to the map.
        vmin : float, optional
            Minimum value for the colour scale.
        vmax : float, optional
            Maximum value for the colour scale.
        cmap : str
            Colour map.
        clabel : str
            Label for the colour bar.
        plotGBs : bool
            If true, plot the grain boundaries on the map.
        dilateBoundaries : bool
            If true, dilate the grain boundaries.
        boundaryColour : str
            Colour to use for the grain boundaries.
        plot_scale_bar : bool
            If true, plot a scale bar in the map.
        scale : float
            Size of pixel in microns.
        highlightGrains : list(int)
            List of grain IDs to highlight.
        highlightColours : str
            Colour to highlight grains.
        highlightAlpha : float
            Alpha (transparency) by which to highlight grains.
        kwargs :
            All other arguments passed to :func:`defdap.plotting.MapPlot.add_map`

        Returns
        -------
        defdap.plotting.MapPlot

        """
        if plot is None:
            plot = cls(callingMap, fig=fig, ax=ax, ax_params=ax_params,
                       make_interactive=make_interactive, **fig_params)

        if mapData is not None:
            plot.add_map(mapData, cmap=cmap, vmin=vmin, vmax=vmax, **kwargs)

        if plot_colour_bar:
            plot.add_colour_bar(clabel)

        if plotGBs:
            plot.add_grain_boundaries(
                colour=boundaryColour, dilate=dilateBoundaries, kind=plotGBs
            )

        if highlightGrains is not None:
            plot.add_grain_highlights(
                highlightGrains,
                grain_colours=highlightColours, alpha=highlightAlpha
            )

        if plot_scale_bar:
            plot.add_scale_bar(scale=scale)

        return plot


class GrainPlot(Plot):
    """ Class for creating a map for a grain.

    """

    def __init__(self, callingGrain, fig=None, ax=None, ax_params={},
                 make_interactive=False, **kwargs):
        super(GrainPlot, self).__init__(
            ax, ax_params=ax_params, fig=fig, make_interactive=make_interactive,
            **kwargs
        )

        self.callingGrain = callingGrain
        self.img_layers = []

        self.ax.set_xticks([])
        self.ax.set_yticks([])

    def addMap(self, mapData, vmin=None, vmax=None, cmap='viridis', **kwargs):
        """Add a map to a grain plot.

        Parameters
        ----------
        mapData : numpy.ndarray
            Grain data to plot
        vmin : float
            Minimum value for the colour scale.
        vmax : float
            Maximum value for the colour scale.
        cmap
            Colour map to use.
        kwargs
            Other arguments are passed to :func:`matplotlib.pyplot.imshow`.

        Returns
        -------
        matplotlib.image.AxesImage

        """
        img = self.ax.imshow(mapData, vmin=vmin, vmax=vmax,
                             interpolation='None', cmap=cmap, **kwargs)
        self.draw()

        self.img_layers.append(img)

        return img

    def add_colour_bar(self, label, layer=0, **kwargs):
        """Add colour bar to grain plot.

        Parameters
        ----------
        label : str
            Label to add to colour bar.
        layer : int
            Layer on which to add colourbar.
        kwargs
            Other arguments passed to :func:`matplotlib.pyplot.colorbar`.

        """
        img = self.img_layers[layer]
        self.colour_bar = plt.colorbar(img, ax=self.ax, label=label, **kwargs)

    def add_scale_bar(self, scale=None):
        """Add scale bar to grain plot.

        Parameters
        ----------
        scale : float
            Size of pixel in micron.

        """
        if scale is None:
            scale = self.callingGrain.owner_map.scale * 1e-6
        self.ax.add_artist(ScaleBar(scale))

    def addTraces(self, angles, colours, topOnly=False, pos=None, **kwargs):
        """Add slip trace angles to grain plot. Illustrated by lines
        crossing through central pivot point to create a circle.

        Parameters
        ----------
        angles : list
            Angles of slip traces.
        colours : list
            Colours to plot.
        topOnly : bool, optional
            If true, plot only a semicircle instead of a circle.
        pos : tuple
            Position of slip traces.
        kwargs
            Other arguments are passed to :func:`matplotlib.pyplot.quiver`

        """
        if pos is None:
            pos = self.callingGrain.centreCoords()
        traces = np.array((-np.sin(angles), np.cos(angles)))

        # When plotting top half only, move all 'traces' to +ve y
        # and set the pivot to be in the tail instead of centre
        if topOnly:
            pivot = 'tail'
            for idx, (x, y) in enumerate(zip(traces[0], traces[1])):
                if x < 0 and y < 0:
                    traces[0][idx] *= -1
                    traces[1][idx] *= -1
            self.ax.set_ylim(pos[1] - 0.001, pos[1] + 0.1)
            self.ax.set_xlim(pos[0] - 0.1, pos[0] + 0.1)
        else:
            pivot = 'middle'

        for i, trace in enumerate(traces.T):
            colour = colours[len(colours) - 1] if i >= len(colours) else colours[i]
            self.ax.quiver(
                pos[0], pos[1],
                trace[0], trace[1],
                scale=1, pivot=pivot,
                color=colour, headwidth=1,
                headlength=0, **kwargs
            )
            self.draw()

    def add_slip_traces(self, topOnly=False, colours=None, pos=None, **kwargs):
        """Add slip traces to plot, based on the calling grain's slip systems.

        Parameters
        ----------
        colours : list
            Colours to plot.
        topOnly : bool, optional
            If true, plot only a semicircle instead of a circle.
        pos : tuple
            Position of slip traces.
        kwargs
            Other arguments are passed to :func:`matplotlib.pyplot.quiver`

        """

        if colours is None:
            colours = self.callingGrain.ebsd_grain.phase.slipTraceColours
        slipTraceAngles = self.callingGrain.slip_traces

        self.addTraces(slipTraceAngles, colours, topOnly, pos=pos, **kwargs)

    def add_slip_bands(self, topOnly=False, grainMapData=None, angles=None, pos=None,
                     thres=None, min_dist=None, **kwargs):
        """Add lines representing slip bands detected by Radon transform
        in :func:`~defdap.hrdic.grain.calcSlipBands`.

        Parameters
        ----------
        topOnly : bool, optional
            If true, plot only a semicircle instead of a circle.
        grainMapData :
            Map data to pass to :func:`~defdap.hrdic.Grain.calcSlipBands`.
        angles : list(float), optional
            List of angles to plot, otherwise, use angles
            detected in :func:`~defdap.hrdic.Grain.calcSlipBands`.
        pos : tuple
            Position in which to plot slip traces.
        thres : float
            Threshold to use in :func:`~defdap.hrdic.Grain.calcSlipBands`.
        min_dist :
            Minimum angle between bands in :func:`~defdap.hrdic.Grain.calcSlipBands`.
        kwargs
            Other arguments are passed to :func:`matplotlib.pyplot.quiver`.

        """

        if angles is None:
            slipBandAngles = self.callingGrain.calcSlipBands(grainMapData,
                                                             thres=thres,
                                                             min_dist=min_dist)
        else:
            slipBandAngles = angles

        self.addTraces(slipBandAngles, ["black"], topOnly, pos=pos, **kwargs)

    @classmethod
    def create(
            cls, callingGrain, mapData,
            fig=None, fig_params={}, ax=None, ax_params={},
            plot=None, make_interactive=False,
            plot_colour_bar=False, vmin=None, vmax=None, cmap=None, clabel="",
            plot_scale_bar=False, scale=None,
            plot_slip_traces=False, plot_slip_bands=False, **kwargs
    ):
        """Create grain plot.

        Parameters
        ----------
        callingGrain : base.Grain
            DIC or EBSD grain which called this plot.
        mapData :
            Data to be plotted.
        fig : matplotlib.figure.Figure
            Matplotlib figure to plot on.
        fig_params :
            Passed to defdap.plotting.Plot.
        ax : matplotlib.axes.Axes
            Matplotlib axis to plot on.
        ax_params :
            Passed to defdap.plotting.Plot as ax_params.
        plot : defdap.plotting.Plot
            If none, use current plot.
        make_interactive :
            If true, make plot interactive
        plot_colour_bar : bool
            If true, plot a colour bar next to the map.
        vmin : float
            Minimum value for the colour scale.
        vmax : float
            Maximum value for the colour scale.
        cmap :
            Colour map.
        clabel : str
            Label for the colour bar.
        plot_scale_bar : bool
            If true, plot a scale bar in the map.
        scale : float
            Size of pizel in microns.
        plot_slip_traces : bool
            If true, plot slip traces with :func:`~defdap.plotting.GrainPlot.add_slip_traces`
        plot_slip_bands : bool
            If true, plot slip traces with :func:`~defdap.plotting.GrainPlot.add_slip_bands`
        kwargs :
            All other arguments passed to :func:`defdap.plotting.GrainPlot.add_map`

        Returns
        -------
        defdap.plotting.GrainPlot

        """
        if plot is None:
            plot = cls(callingGrain, fig=fig, ax=ax, ax_params=ax_params,
                       make_interactive=make_interactive, **fig_params)
        plot.addMap(mapData, cmap=cmap, vmin=vmin, vmax=vmax, **kwargs)

        if plot_colour_bar:
            plot.add_colour_bar(clabel)

        if plot_scale_bar:
            plot.add_scale_bar(scale=scale)

        if plot_slip_traces:
            plot.add_slip_traces()

        if plot_slip_bands:
            plot.add_slip_bands(grainMapData=mapData)

        return plot


class PolePlot(Plot):
    """ Class for creating an inverse pole figure plot.

    """

    def __init__(self, plot_type, crystal_sym, projection=None,
                 fig=None, ax=None, ax_params={}, make_interactive=False,
                 **kwargs):
        super(PolePlot, self).__init__(
            ax, ax_params=ax_params, fig=fig, make_interactive=make_interactive,
            **kwargs)

        self.plot_type = plot_type
        self.crystal_sym = crystal_sym
        self.projection = self._validateProjection(projection)

        self.img_layers = []

        self.add_axis()

    def add_axis(self):
        """Draw axes on the IPF based on crystal symmetry.

        Raises
        -------
        NotImplementedError
            If a crystal type other than 'cubic' or 'hexagonal' are selected.

        """
        if self.plot_type == "IPF" and self.crystal_sym == "cubic":
            # line between [001] and [111]
            self.addLine([0, 0, 1], [1, 1, 1], c='k', lw=2)

            # line between [001] and [101]
            self.addLine([0, 0, 1], [1, 0, 1], c='k', lw=2)

            # line between [101] and [111]
            self.addLine([1, 0, 1], [1, 1, 1], c='k', lw=2)

            # label poles
            self.labelPoint([0, 0, 1], '001',
                            padY=-0.005, va='top', ha='center', fontsize=12)
            self.labelPoint([1, 0, 1], '101',
                            padY=-0.005, va='top', ha='center', fontsize=12)
            self.labelPoint([1, 1, 1], '111',
                            padY=0.005, va='bottom', ha='center', fontsize=12)

        elif self.plot_type == "IPF" and self.crystal_sym == "hexagonal":
            # line between [0001] and [10-10] ([001] and [210])
            # converted to cubic axes
            self.addLine([0, 0, 1], [np.sqrt(3), 1, 0], c='k', lw=2)

            # line between [0001] and [2-1-10] ([001] and [100])
            self.addLine([0, 0, 1], [1, 0, 0], c='k', lw=2)

            # line between [2-1-10] and [10-10] ([100] and [210])
            self.addLine([1, 0, 0], [np.sqrt(3), 1, 0], c='k', lw=2)

            # label poles
            self.labelPoint([0, 0, 1], '0001',
                            padY=-0.012, va='top', ha='center', fontsize=12)
            self.labelPoint([1, 0, 0], r'$2\bar{1}\bar{1}0$',
                            padY=-0.012, va='top', ha='center', fontsize=12)
            self.labelPoint([np.sqrt(3), 1, 0], r'$10\bar{1}0$',
                            padY=0.009, va='bottom', ha='center', fontsize=12)

        else:
            raise NotImplementedError("Only works for cubic and hexagonal.")

        self.ax.axis('equal')
        self.ax.axis('off')

    def addLine(self, startPoint, endPoint, plotSyms=False, res=100, **kwargs):
        """Draw lines on the IPF plot.

        Parameters
        ----------
        startPoint : numpy.ndarray
            Start point in crystal coordinates (i.e. [0,0,1]).
        endPoint : numpy.ndarray
            End point in crystal coordinates, (i.e. [1,0,0]).
        plotSyms : bool, optional
            If true, plot all symmetrically equivelant points.
        res : int
            Number of points within each line to plot.
        kwargs
            All other arguments are passed to :func:`matplotlib.pyplot.plot`.

        """
        lines = [(startPoint, endPoint)]
        if plotSyms:
            for symm in quat.Quat.symEqv(self.crystal_sym)[1:]:
                startPointSymm = symm.transform_vector(startPoint).astype(int)
                endPointSymm = symm.transform_vector(endPoint).astype(int)

                if startPointSymm[2] < 0:
                    startPointSymm *= -1
                if endPointSymm[2] < 0:
                    endPointSymm *= -1

                lines.append((startPointSymm, endPointSymm))

        linePoints = np.zeros((3, res), dtype=float)
        for line in lines:
            for i in range(3):
                if line[0][i] == line[1][i]:
                    linePoints[i] = np.full(res, line[0][i])
                else:
                    linePoints[i] = np.linspace(line[0][i], line[1][i], res)

            xp, yp = self.projection(linePoints[0], linePoints[1], linePoints[2])
            self.ax.plot(xp, yp, **kwargs)

    def labelPoint(self, point, label, padX=0, padY=0, **kwargs):
        """Place a label near a coordinate in the pole plot.

        Parameters
        ----------
        point : tuple
            (x, y) coordinate to place text.
        label : str
            Text to use in label.
        padX : int, optional
            Pad added to x coordinate.
        padY : int, optional
            Pad added to y coordinate.
        kwargs
            Other arguments are passed to :func:`matplotlib.axes.Axes.text`.

        """
        xp, yp = self.projection(*point)
        self.ax.text(xp + padX, yp + padY, label, **kwargs)

    def addPoints(self, alpha_ang, beta_ang, marker_colour=None, marker_size=None, **kwargs):
        """Add a point to the pole plot.

        Parameters
        ----------
        alpha_ang
            Inclination angle to plot.
        beta_ang
            Azimuthal angle (around z axis from x in anticlockwise as per ISO) to plot.
        marker_colour : str or list(str), optional
            Colour of marker. If two specified, then the point will have two
            semicircles of different colour.
        marker_size : float
            Size of marker.
        kwargs
            Other arguments are passed to :func:`matplotlib.axes.Axes.scatter`.

        Raises
        -------
        Exception
            If more than two colours are specified

        """
        # project onto equatorial plane
        xp, yp = self.projection(alpha_ang, beta_ang)

        # plot poles
        # plot markers with 'half-and-half' colour
        if type(marker_colour) is str:
            marker_colour = [marker_colour]

        if marker_colour is None:
            points = self.ax.scatter(xp, yp, **kwargs)
            self.img_layers.append(points)
        elif len(marker_colour) == 2:
            pos = (xp, yp)
            r1 = 0.5
            r2 = r1 + 0.5
            marker_size = np.sqrt(marker_size)

            x = [0] + np.cos(np.linspace(0, 2 * np.pi * r1, 10)).tolist()
            y = [0] + np.sin(np.linspace(0, 2 * np.pi * r1, 10)).tolist()
            xy1 = list(zip(x, y))

            x = [0] + np.cos(np.linspace(2 * np.pi * r1, 2 * np.pi * r2, 10)).tolist()
            y = [0] + np.sin(np.linspace(2 * np.pi * r1, 2 * np.pi * r2, 10)).tolist()
            xy2 = list(zip(x, y))

            points = self.ax.scatter(
                pos[0], pos[1], marker=(xy1, 0),
                s=marker_size, c=marker_colour[0], **kwargs
            )
            self.img_layers.append(points)
            points = self.ax.scatter(
                pos[0], pos[1], marker=(xy2, 0),
                s=marker_size, c=marker_colour[1], **kwargs
            )
            self.img_layers.append(points)
        else:
            raise Exception("specify one colour for solid markers or list two for 'half and half'")

    def add_colour_bar(self, label, layer=0, **kwargs):
        """Add a colour bar to the pole plot.

        Parameters
        ----------
        label : str
            Label to place next to colour bar.
        layer : int
            Layer number to add the colour bar to.
        kwargs
            Other argument are passed to :func:`matplotlib.pyplot.colorbar`.

        """
        img = self.img_layers[layer]
        self.colour_bar = plt.colorbar(img, ax=self.ax, label=label, **kwargs)

    def addLegend(self, label='Grain area (μm$^2$)', number=6, layer=0, scaling=1, **kwargs):
        """Add a marker size legend to the pole plot.

        Parameters
        ----------
        label : str
            Label to place next to legend.
        number :
            Number of markers to plot in legend.
        layer : int
            Layer number to add the colour bar to.
        scaling : float
            Scaling applied to the data.
        kwargs
            Other argument are passed to :func:`matplotlib.pyplot.legend`.

        """
        img = self.img_layers[layer]
        self.legend = plt.legend(*img.legend_elements("sizes", num=number,
                                                      func=lambda s: s / scaling), title=label, **kwargs)

    @staticmethod
    def _validateProjection(projectionIn, validateDefault=False):
        if validateDefault:
            defaultProjection = None
        else:
            defaultProjection = PolePlot._validateProjection(
                defaults['pole_projection'], validateDefault=True
            )

        if projectionIn is None:
            projection = defaultProjection

        elif type(projectionIn) is str:
            projectionName = projectionIn.replace(" ", "").lower()
            if projectionName in ["lambert", "equalarea"]:
                projection = PolePlot.lambertProject
            elif projectionName in ["stereographic", "stereo", "equalangle"]:
                projection = PolePlot.stereoProject
            else:
                print("Unknown projection name, using default")
                projection = defaultProjection

        elif callable(projectionIn):
            projection = projectionIn

        else:
            print("Unknown projection, using default")
            projection = defaultProjection

        if projection is None:
            raise ValueError("Problem with default projection.")

        return projection

    @staticmethod
    def stereoProject(*args):
        """Stereographic projection of pole direction or pair of polar angles.

        Parameters
        ----------
        args : numpy.ndarray, len 2 or 3
            2 arguments for polar angles or 3 arguments for pole directions.

        Returns
        -------
        float, float
            x coordinate, y coordinate

        Raises
        -------
        Exception
            If input array has incorrect length

        """
        if len(args) == 3:
            alpha, beta = quat.Quat.polarAngles(args[0], args[1], args[2])
        elif len(args) == 2:
            alpha, beta = args
        else:
            raise Exception("3 arguments for pole directions and 2 for polar angles.")

        alphaComp = np.tan(alpha / 2)
        xp = alphaComp * np.cos(beta)
        yp = alphaComp * np.sin(beta)

        return xp, yp

    @staticmethod
    def lambertProject(*args):
        """Lambert Projection of pole direction or pair of polar angles.

        Parameters
        ----------
        args : numpy.ndarray, len 2 or 3
            2 arguments for polar angles or 3 arguments for pole directions.

        Returns
        -------
        float, float
            x coordinate, y coordinate

        Raises
        -------
        Exception
            If input array has incorrect length

        """
        if len(args) == 3:
            alpha, beta = quat.Quat.polarAngles(args[0], args[1], args[2])
        elif len(args) == 2:
            alpha, beta = args
        else:
            raise Exception("3 arguments for pole directions and 2 for polar angles.")

        alphaComp = np.sqrt(2 * (1 - np.cos(alpha)))
        xp = alphaComp * np.cos(beta)
        yp = alphaComp * np.sin(beta)

        return xp, yp


class HistPlot(Plot):
    """ Class for creating a histogram.

    """

    def __init__(self, plotType="scatter", axesType="linear", density=True, fig=None,
                 ax=None, ax_params={}, make_interactive=False, **kwargs):
        """Initialise a histogram plot

        Parameters
        ----------
        plotType: str, {'scatter', 'bar', 'step'}
            Type of plot to use
        axesType : str, {'linear', 'logx', 'logy', 'loglog', 'None'}, optional
            If 'log' is specified, logarithmic scale is used.
        density :
            If true, histogram is normalised such that the integral sums to 1.
        fig : matplotlib.figure.Figure
            Matplotlib figure to plot on.
        ax : matplotlib.axes.Axes
            Matplotlib axis to plot on.
        ax_params :
            Passed to defdap.plotting.Plot as ax_params.
        make_interactive : bool
            If true, make the plot interactive.
        kwargs
            Other arguments are passed to :class:`defdap.plotting.Plot`

        """
        super(HistPlot, self).__init__(
            ax, ax_params=ax_params, fig=fig, make_interactive=make_interactive,
            **kwargs
        )

        axesType = axesType.lower()
        if axesType in ["linear", "logy", "logx", "loglog"]:
            self.axesType = axesType
        else:
            raise ValueError("plotType must be linear or log.")

        if plotType in ['scatter', 'bar', 'step']:
            self.plotType = plotType
        else:
            raise ValueError("plotType must be scatter, bar or step.")

        self.density = bool(density)

        # set y-axis label
        yLabel = "Normalised frequency" if self.density else "Frequency"
        self.ax.set_ylabel(yLabel)

        # set axes to linear or log as appropriate and set to be numbers as opposed to scientific notation
        if self.axesType == 'logx' or self.axesType == 'loglog':
            self.ax.set_xscale("log")
            self.ax.xaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.5g}'.format(y)))
        if self.axesType == 'logy' or self.axesType == 'loglog':
            self.ax.set_yscale("log")
            self.ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.5g}'.format(y)))

    def addHist(self, histData, bins=100, range=None, line='o',
                label=None, **kwargs):
        """Add a histogram to the current plot

        Parameters
        ----------
        histData : numpy.ndarray
            Data to be used in the histogram.
        bins : int
            Number of bins to use for histogram.
        range : tuple or None, optional
            The lower and upper range of the bins
        line : str, optional
            Marker or line type to be used.
        label : str, optional
            Label to use for data (used for legend).
        kwargs
            Other arguments are passed to :func:`numpy.histogram`

        """

        # Generate the x bins with appropriate spaceing for linear or log
        if self.axesType == 'logx' or self.axesType == 'loglog':
            binList = np.logspace(np.log10(range[0]), np.log10(range[1]), bins)
        else:
            binList = np.linspace(range[0], range[1], bins)

        if self.plotType == 'scatter':
            # Generate the histogram data and plot as a scatter plot
            hist = np.histogram(histData.flatten(), bins=binList, density=self.density)
            yVals = hist[0]
            xVals = 0.5 * (hist[1][1:] + hist[1][:-1])

            self.ax.plot(xVals, yVals, line, label=label, **kwargs)

        else:
            # Plot as a matplotlib histogram
            self.ax.hist(histData.flatten(), bins=binList, histtype=self.plotType,
                         density=self.density, label=label, **kwargs)

    def addLegend(self, **kwargs):
        """Add legend to histogram.

        Parameters
        ----------
        kwargs
            All arguments passed to :func:`matplotlib.axes.Axes.legend`.

        """
        self.ax.legend(**kwargs)

    @classmethod
    def create(
            cls, histData, fig=None, fig_params={}, ax=None, ax_params={},
            plot=None, make_interactive=False,
            plotType="scatter", axesType="linear", density=True, bins=10, range=None,
            line='o', label=None, **kwargs
    ):
        """Create a histogram plot.

        Parameters
        ----------
        histData : numpy.ndarray
            Data to be used in the histogram.
        fig : matplotlib.figure.Figure
            Matplotlib figure to plot on.
        fig_params :
            Passed to defdap.plotting.Plot.
        ax : matplotlib.axes.Axes
            Matplotlib axis to plot on.
        ax_params :
            Passed to defdap.plotting.Plot as ax_params.
        plot : defdap.plotting.HistPlot
            Plot where histgram is created. If none, a new plot is created.
        make_interactive : bool, optional
            If true, make plot interactive.
        plotType: str, {'scatter', 'bar', 'barfilled', 'step'}
            Type of plot to use
        axesType : str, {'linear', 'logx', 'logy', 'loglog', 'None'}, optional
            If 'log' is specified, logarithmic scale is used.
        density :
            If true, histogram is normalised such that the integral sums to 1.
        bins : int
            Number of bins to use for histogram.
        range : tuple or None, optional
            The lower and upper range of the bins
        line : str, optional
            Marker or line type to be used.
        label : str, optional
            Label to use for data (is used for legend).
        kwargs
            Other arguments are passed to :func:`defdap.plotting.HistPlot.addHist`

        Returns
        -------
        defdap.plotting.HistPlot

        """
        if plot is None:
            plot = cls(axesType=axesType, plotType=plotType, density=density, fig=fig, ax=ax,
                       ax_params=ax_params, make_interactive=make_interactive,
                       **fig_params)
        plot.addHist(histData, bins=bins, range=range, line=line,
                     label=label, **kwargs)

        return plot


class CrystalPlot(Plot):
    """ Class for creating a 3D plot for plotting unit cells.

    """

    def __init__(self, fig=None, ax=None, ax_params={},
                 make_interactive=False, **kwargs):
        """Initialise a 3D plot.

        Parameters
        ----------
        fig : matplotlib.pyplot.Figure
            Figure to plot to.
        ax : matplotlib.pyplot.Axis
            Axis to plot to.
        ax_params
            Passed to defdap.plotting.Plot as ax_params.
        make_interactive : bool, optional
            If true, make plot interactive.
        kwargs
            Other arguments are passed to :class:`defdap.plotting.Plot`.

        """
        # Set default plot parameters then update with input
        fig_params = {
            'figsize': (6, 6)
        }
        fig_params.update(kwargs)
        ax_paramsDefault = {
            'projection': '3d',
            'proj_type': 'ortho'
        }
        ax_paramsDefault.update(ax_params)
        ax_params = ax_paramsDefault

        super(CrystalPlot, self).__init__(
            ax, ax_params=ax_params, fig=fig, make_interactive=make_interactive,
            **fig_params
        )

    def addVerts(self, verts, **kwargs):
        """Plots planes, defined by the vertices provided.

        Parameters
        ----------
        verts : list
            List of vertices.
        kwargs
            Other arguments are passed to :class:`matplotlib.collections.PolyCollection`.

        """
        # Set default plot parameters then update with any input
        plot_params = {
            'alpha': 0.6,
            'facecolor': '0.8',
            'linewidths': 3,
            'edgecolor': 'k'
        }
        plot_params.update(kwargs)

        # Add list of planes defined by given vertices to the 3D plot
        pc = Poly3DCollection(verts, **plot_params)
        self.ax.add_collection3d(pc)

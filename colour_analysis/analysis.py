# !/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

import json
import os
from collections import OrderedDict, deque, namedtuple
from itertools import cycle

import numpy as np
from vispy.scene import SceneCanvas
from colour import RGB_COLOURSPACES, read_image

from colour_analysis.utilities.common import REFERENCE_COLOURSPACES
from colour_analysis.constants import DEFAULT_IMAGE, SETTINGS_FILE
from colour_analysis.views import (
    ConsoleView,
    DiagramView,
    GamutView,
    ImageView)


Sequence = namedtuple(
    'Sequence',
    ('modifiers',
     'key'))

Action = namedtuple(
    'Action',
    ('name',
     'description',
     'sequence'))

ViewPreset = namedtuple(
    'ViewPreset',
    ('name',
     'description',
     'view',
     'row',
     'column',
     'row_span',
     'column_span'))

LayoutPreset = namedtuple(
    'LayoutPreset',
    ('name',
     'description',
     'views'))


class Analysis(SceneCanvas):
    def __init__(self,
                 image_path=DEFAULT_IMAGE,
                 input_colourspace='Rec. 709',
                 input_oecf='Rec. 709',
                 input_linear=True,
                 input_resample=1,
                 reference_colourspace='CIE xyY',
                 correlate_colourspace='ACEScg',
                 settings=None,
                 layout='layout_1'):
        SceneCanvas.__init__(
            self,
            keys='interactive',
            title="Colour Analysis - {0}".format(image_path),
            size=settings['canvas']['size'],
            bgcolor=settings['canvas']['canvas_background_colour'])

        self.__image_path = None
        self.image_path = image_path
        self.__image = None
        self.image = np.random.random((256, 256, 3))
        self.__input_colourspace = None
        self.input_colourspace = input_colourspace
        self.__input_oecf = None
        self.input_oecf = input_oecf
        self.__input_linear = None
        self.input_linear = input_linear
        self.__input_resample = None
        self.input_resample = input_resample
        self.__reference_colourspace = None
        self.reference_colourspace = reference_colourspace
        self.__correlate_colourspace = None
        self.correlate_colourspace = correlate_colourspace
        self.__settings = (json.load(open(SETTINGS_FILE))
                           if settings is None else
                           settings)
        self.__layout = None
        self.layout = layout

        self.__layout_presets = OrderedDict()
        self.__actions = {}

        self.__console_view = None
        self.__gamut_view = None
        self.__image_view = None
        self.__diagram_view = None
        self.__views = None

        self.__grid = None

        self.__RGB_colourspaces_cycle = cycle(
            [c for c in sorted(RGB_COLOURSPACES)
             if c not in ('aces', 'adobe1998', 'prophoto')])

        reference_colourspaces_deque = deque(REFERENCE_COLOURSPACES)
        reference_colourspaces_deque.rotate(-REFERENCE_COLOURSPACES.index(
            self.__reference_colourspace) - 1)
        self.__reference_colourspaces_cycle = cycle(
            reference_colourspaces_deque)

        self.__create_layout_presets()
        self.__create_actions()
        self.__create_image()
        self.__create_views()
        self.__layout_views()

        self.show()

    @property
    def image_path(self):
        """
        Property for **self.__image_path** private attribute.

        Returns
        -------
        unicode
            self.__image_path.
        """

        return self.__image_path

    @image_path.setter
    def image_path(self, value):
        """
        Setter for **self.__image_path** private attribute.

        Parameters
        ----------
        value : unicode
            Attribute value.
        """

        if value is not None:
            assert type(value) in (str, unicode), (
                ('"{0}" attribute: "{1}" type is not '
                 '"str" or "unicode"!').format('image_path', value))
            assert os.path.exists(value), (
                '"{0}" input image doesn\'t exists!'.format(value))
        self.__image_path = value

    @property
    def image(self):
        """
        Property for **self.__image** private attribute.

        Returns
        -------
        array_like
            self.__image.
        """

        return self.__image

    @image.setter
    def image(self, value):
        """
        Setter for **self.__image** private attribute.

        Parameters
        ----------
        value : array_like
            Attribute value.
        """

        if value is not None:
            assert type(value) in (tuple, list, np.ndarray, np.matrix), (
                ('"{0}" attribute: "{1}" type is not "tuple", "list", '
                 '"ndarray" or "matrix"!').format('image', value))
        self.__image = value

    @property
    def input_colourspace(self):
        """
        Property for **self.__input_colourspace** private attribute.

        Returns
        -------
        unicode
            self.__input_colourspace.
        """

        return self.__input_colourspace

    @input_colourspace.setter
    def input_colourspace(self, value):
        """
        Setter for **self.__input_colourspace** private attribute.

        Parameters
        ----------
        value : unicode
            Attribute value.
        """

        if value is not None:
            assert type(value) in (str, unicode), (
                ('"{0}" attribute: "{1}" type is not '
                 '"str" or "unicode"!').format('input_colourspace', value))
            assert value in RGB_COLOURSPACES, (
                '"{0}" colourspace not found in factory RGB colourspaces: '
                '"{1}".').format(
                value, ', '.join(sorted(RGB_COLOURSPACES.keys())))
        self.__input_colourspace = value

    @property
    def input_oecf(self):
        """
        Property for **self.__input_oecf** private attribute.

        Returns
        -------
        unicode
            self.__input_oecf.
        """

        return self.__input_oecf

    @input_oecf.setter
    def input_oecf(self, value):
        """
        Setter for **self.__input_oecf** private attribute.

        Parameters
        ----------
        value : unicode
            Attribute value.
        """

        if value is not None:
            assert type(value) in (str, unicode), (
                ('"{0}" attribute: "{1}" type is not '
                 '"str" or "unicode"!').format('input_oecf', value))
            assert value in RGB_COLOURSPACES, (
                '"{0}" OECF is not associated with any factory '
                'RGB colourspaces: "{1}".').format(value, ', '.join(
                sorted(RGB_COLOURSPACES.keys())))
        self.__input_oecf = value

    @property
    def input_linear(self):
        """
        Property for **self.__input_linear** private attribute.

        Returns
        -------
        bool
            self.__input_linear.
        """

        return self.__input_linear

    @input_linear.setter
    def input_linear(self, value):
        """
        Setter for **self.__input_linear** private attribute.

        Parameters
        ----------
        value : bool
            Attribute value.
        """

        if value is not None:
            assert type(value) is bool, (
                '"{0}" attribute: "{1}" type is not "bool"!'.format(
                    'input_linear', value))
        self.__input_linear = value

    @property
    def input_resample(self):
        """
        Property for **self.input_resample** attribute.

        Returns
        -------
        int
        """

        return self.__input_resample

    @input_resample.setter
    def input_resample(self, value):
        """
        Setter for **self.input_resample** attribute.

        Parameters
        ----------
        value : int
            Attribute value.
        """

        if value is not None:
            assert type(value) is int, (
                '"{0}" attribute: "{1}" type is not "int"!'.format(
                    'input_resample', value))
        self.__input_resample = value

    @property
    def reference_colourspace(self):
        """
        Property for **self.__reference_colourspace** private attribute.

        Returns
        -------
        unicode
            self.__reference_colourspace.
        """

        return self.__reference_colourspace

    @reference_colourspace.setter
    def reference_colourspace(self, value):
        """
        Setter for **self.__reference_colourspace** private attribute.

        Parameters
        ----------
        value : unicode
            Attribute value.
        """

        if value is not None:
            assert type(value) in (str, unicode), (
                ('"{0}" attribute: "{1}" type is not '
                 '"str" or "unicode"!').format('reference_colourspace', value))
            assert value in REFERENCE_COLOURSPACES, (
                '"{0}" reference colourspace not found in factory reference '
                'colourspaces: "{1}".').format(
                value, ', '.join(sorted(REFERENCE_COLOURSPACES.keys())))
        self.__reference_colourspace = value

    @property
    def correlate_colourspace(self):
        """
        Property for **self.__correlate_colourspace** private attribute.

        Returns
        -------
        unicode
            self.__correlate_colourspace.
        """

        return self.__correlate_colourspace

    @correlate_colourspace.setter
    def correlate_colourspace(self, value):
        """
        Setter for **self.__correlate_colourspace** private attribute.

        Parameters
        ----------
        value : unicode
            Attribute value.
        """

        if value is not None:
            assert type(value) in (str, unicode), (
                ('"{0}" attribute: "{1}" type is not '
                 '"str" or "unicode"!').format('correlate_colourspace', value))
            assert value in RGB_COLOURSPACES, (
                '"{0}" colourspace not found in factory RGB colourspaces: '
                '"{1}".').format(value, ', '.join(
                sorted(RGB_COLOURSPACES.keys())))
        self.__correlate_colourspace = value

    @property
    def settings(self):
        """
        Property for **self.__settings** private attribute.

        Returns
        -------
        dict
            self.__settings.
        """

        return self.__settings

    @settings.setter
    def settings(self, value):
        """
        Setter for **self.__settings** private attribute.

        Parameters
        ----------
        value : dict
            Attribute value.
        """

        raise AttributeError(
            '"{0}" attribute is read only!'.format('settings'))

    @property
    def layout(self):
        """
        Property for **self.__layout** private attribute.

        Returns
        -------
        unicode
            self.__layout.
        """

        return self.__layout

    @layout.setter
    def layout(self, value):
        """
        Setter for **self.__layout** private attribute.

        Parameters
        ----------
        value : unicode
            Attribute value.
        """

        if value is not None:
            assert type(value) in (str, unicode), (
                ('"{0}" attribute: "{1}" type is not '
                 '"str" or "unicode"!').format('layout', value))
        self.__layout = value

    @property
    def actions(self):
        """
        Property for **self.__actions** private attribute.

        Returns
        -------
        dict
            self.__actions.
        """

        return self.__actions

    @actions.setter
    def actions(self, value):
        """
        Setter for **self.__actions** private attribute.

        Parameters
        ----------
        value : dict
            Attribute value.
        """

        raise AttributeError(
            '"{0}" attribute is read only!'.format('actions'))

    @property
    def console_view(self):
        """
        Property for **self.console_view** attribute.

        Returns
        -------
        ViewBox
        """

        return self.__console_view

    @console_view.setter
    def console_view(self, value):
        """
        Setter for **self.console_view** attribute.

        Parameters
        ----------
        value : ViewBox
            Attribute value.
        """

        raise AttributeError(
            '"{0}" attribute is read only!'.format('console_view'))

    @property
    def gamut_view(self):
        """
        Property for **self.gamut_view** attribute.

        Returns
        -------
        ViewBox
        """

        return self.__gamut_view

    @gamut_view.setter
    def gamut_view(self, value):
        """
        Setter for **self.gamut_view** attribute.

        Parameters
        ----------
        value : ViewBox
            Attribute value.
        """

        raise AttributeError(
            '"{0}" attribute is read only!'.format('gamut_view'))

    @property
    def image_view(self):
        """
        Property for **self.image_view** attribute.

        Returns
        -------
        ViewBox
        """

        return self.__image_view

    @image_view.setter
    def image_view(self, value):
        """
        Setter for **self.image_view** attribute.

        Parameters
        ----------
        value : ViewBox
            Attribute value.
        """

        raise AttributeError(
            '"{0}" attribute is read only!'.format('image_view'))

    @property
    def diagram_view(self):
        """
        Property for **self.diagram_view** attribute.

        Returns
        -------
        ViewBox
        """

        return self.__diagram_view

    @diagram_view.setter
    def diagram_view(self, value):
        """
        Setter for **self.diagram_view** attribute.

        Parameters
        ----------
        value : ViewBox
            Attribute value.
        """

        raise AttributeError(
            '"{0}" attribute is read only!'.format('diagram_view'))

    def on_key_press(self, event):
        key = event.key.name.lower()
        modifiers = sorted([modifier.name.lower()
                            for modifier in event.modifiers])
        for action in self.__actions.values():
            if (key == action.sequence.key and
                        modifiers == sorted(action.sequence.modifiers)):
                method = '{0}_action'.format(action.name)

                hasattr(self, method) and getattr(self, method)()

                for view in self.__views:
                    hasattr(view, method) and getattr(view, method)()

    def __create_layout_presets(self):
        layouts = self.__settings['layouts']
        for layout in layouts:
            views = {}
            for name, view in layout['views'].items():
                views[name] = ViewPreset(
                    name=view['name'],
                    description=view['description'],
                    view=view['view'],
                    row=view['row'],
                    column=view['column'],
                    row_span=view['row_span'],
                    column_span=view['column_span'])

            self.__layout_presets[layout['name']] = LayoutPreset(
                name=layout['name'],
                description=layout['description'],
                views=views)

    def __create_image(self):
        image = read_image(self.__image_path)
        if not self.__input_linear:
            colourspace = RGB_COLOURSPACES[self.__input_oecf]
            image = colourspace.inverse_transfer_function(image)

        # Keeping RGB channels only.
        image = image[..., 0:3]

        self.__image = image[::self.__input_resample, ::self.__input_resample]

    def __create_actions(self):
        self.__actions = {}

        for name, action in self.__settings.get('actions', ()).items():
            if action.get('sequence') is not None:
                sequence = Sequence(
                    modifiers=action.get('sequence').get('modifiers', ()),
                    key=action.get('sequence').get('key'))
            else:
                sequence = Sequence(modifiers=(), key=None)

            self.__actions[name] = Action(
                name=action.get('name'),
                description=action.get('description'),
                sequence=sequence)

    def __create_views(self):
        background_colour = (
            self.__settings['canvas']['views_background_colour'])
        border_colour = self.__settings['canvas']['views_border_colour']

        self.__console_view = ConsoleView(
            canvas=self,
            text_color=(0.8, 0.8, 0.8),
            font_size=10.0,
            bgcolor=background_colour,
            border_color=border_colour)

        self.__gamut_view = GamutView(
            canvas=self,
            image=self.__image,
            input_colourspace=self.__input_colourspace,
            reference_colourspace=self.__reference_colourspace,
            correlate_colourspace=self.__correlate_colourspace,
            settings=self.__settings,
            bgcolor=background_colour,
            border_color=border_colour)

        self.__image_view = ImageView(
            canvas=self,
            image=self.__image,
            oecf=self.__input_oecf,
            input_colourspace=self.__input_colourspace,
            correlate_colourspace=self.__correlate_colourspace,
            bgcolor=background_colour,
            border_color=border_colour)

        self.__diagram_view = DiagramView(
            canvas=self,
            image=self.__image,
            oecf=self.__input_oecf,
            input_colourspace=self.__input_colourspace,
            correlate_colourspace=self.__correlate_colourspace,
            bgcolor=background_colour,
            border_color=border_colour)

        self.__views = (self.__console_view,
                        self.__gamut_view,
                        self.__image_view)

    def __layout_views(self):
        self.__grid = self.central_widget.add_grid()
        layout = self.__layout_presets.get(self.__layout)

        for view in layout.views.values():
            self.__grid.add_widget(
                getattr(self, '{0}'.format(view.view)),
                row=view.row,
                col=view.column,
                row_span=view.row_span,
                col_span=view.column_span)

    def cycle_correlate_colourspace_action(self):
        self.__correlate_colourspace = next(self.__RGB_colourspaces_cycle)

        self.__gamut_view.correlate_colourspace = self.__correlate_colourspace
        self.__image_view.correlate_colourspace = self.__correlate_colourspace

        return True

    def cycle_reference_colourspace_action(self):
        self.__reference_colourspace = next(
            self.__reference_colourspaces_cycle)

        self.__gamut_view.reference_colourspace = self.__reference_colourspace

        return True

from __future__ import division, absolute_import, unicode_literals
import os

from qtpy import QtCore
from qtpy import QtWidgets

from ..i18n import N_
from ..models import prefs
from ..qtutils import diff_font
from .. import cmds
from .. import qtutils
from .. import gitcfg
from . import defs
from . import standard


def preferences(model=None, parent=None):
    if model is None:
        model = prefs.PreferencesModel()
    view = PreferencesView(model, parent=parent)
    view.show()
    view.raise_()
    return view


class FormWidget(QtWidgets.QWidget):

    def __init__(self, model, parent, source='user'):
        QtWidgets.QWidget.__init__(self, parent)
        self.model = model
        self.config_to_widget = {}
        self.widget_to_config = {}
        self.source = source
        self.config = gitcfg.current()
        self.defaults = {}
        self.setLayout(QtWidgets.QFormLayout())

    def add_row(self, label, widget):
        self.layout().addRow(label, widget)

    def set_config(self, config_dict):
        self.config_to_widget.update(config_dict)
        for config, (widget, default) in config_dict.items():
            self.widget_to_config[config] = widget
            self.defaults[config] = default
            self.connect_widget_to_config(widget, config)

    def connect_widget_to_config(self, widget, config):
        if isinstance(widget, QtWidgets.QSpinBox):
            widget.valueChanged.connect(self._int_config_changed(config))

        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.toggled.connect(self._bool_config_changed(config))

        elif isinstance(widget, QtWidgets.QLineEdit):
            widget.editingFinished.connect(self._text_config_changed(config))
            widget.returnPressed.connect(self._text_config_changed(config))

    def _int_config_changed(self, config):
        def runner(value):
            cmds.do(prefs.SetConfig, self.model, self.source, config, value)
        return runner

    def _bool_config_changed(self, config):
        def runner(value):
            cmds.do(prefs.SetConfig, self.model, self.source, config, value)
        return runner

    def _text_config_changed(self, config):
        def runner():
            value = self.sender().text()
            cmds.do(prefs.SetConfig, self.model, self.source, config, value)
        return runner

    def update_from_config(self):
        if self.source == 'user':
            getter = self.config.get_user_or_system
        else:
            getter = self.config.get

        for config, widget in self.widget_to_config.items():
            value = getter(config)
            if value is None:
                value = self.defaults[config]
            self.set_widget_value(widget, value)

    def set_widget_value(self, widget, value):
        widget.blockSignals(True)
        if isinstance(widget, QtWidgets.QSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(value)
        widget.blockSignals(False)


class RepoFormWidget(FormWidget):

    def __init__(self, model, parent, source):
        FormWidget.__init__(self, model, parent, source=source)

        self.name = QtWidgets.QLineEdit()
        self.email = QtWidgets.QLineEdit()
        self.merge_verbosity = QtWidgets.QSpinBox()
        self.merge_verbosity.setMinimum(0)
        self.merge_verbosity.setMaximum(5)
        self.merge_verbosity.setProperty('value', 5)

        self.diff_context = QtWidgets.QSpinBox()
        self.diff_context.setMinimum(2)
        self.diff_context.setMaximum(99)
        self.diff_context.setProperty('value', 5)

        self.merge_summary = qtutils.checkbox(checked=True)
        self.merge_diffstat = qtutils.checkbox(checked=True)
        self.display_untracked = qtutils.checkbox(checked=True)

        tooltip = N_('Detect conflict markers in unmerged files')
        self.check_conflicts = qtutils.checkbox(checked=True, tooltip=tooltip)

        self.add_row(N_('User Name'), self.name)
        self.add_row(N_('Email Address'), self.email)
        self.add_row(N_('Merge Verbosity'), self.merge_verbosity)
        self.add_row(N_('Number of Diff Context Lines'), self.diff_context)
        self.add_row(N_('Summarize Merge Commits'), self.merge_summary)
        self.add_row(N_('Show Diffstat After Merge'), self.merge_diffstat)
        self.add_row(N_('Display Untracked Files'), self.display_untracked)
        self.add_row(N_('Detect Conflict Markers'), self.check_conflicts)

        self.set_config({
            prefs.CHECKCONFLICTS: (self.check_conflicts, True),
            prefs.DIFFCONTEXT: (self.diff_context, 5),
            prefs.DISPLAY_UNTRACKED: (self.display_untracked, True),
            prefs.USER_NAME: (self.name, ''),
            prefs.USER_EMAIL: (self.email, ''),
            prefs.MERGE_DIFFSTAT: (self.merge_diffstat, True),
            prefs.MERGE_SUMMARY: (self.merge_summary, True),
            prefs.MERGE_VERBOSITY: (self.merge_verbosity, 5),
        })


class SettingsFormWidget(FormWidget):

    def __init__(self, model, parent):
        FormWidget.__init__(self, model, parent)

        self.fixed_font = QtWidgets.QFontComboBox()

        self.font_size = QtWidgets.QSpinBox()
        self.font_size.setMinimum(8)
        self.font_size.setProperty('value', 12)
        self._font_str = None

        self.tabwidth = QtWidgets.QSpinBox()
        self.tabwidth.setWrapping(True)
        self.tabwidth.setMaximum(42)

        self.textwidth = QtWidgets.QSpinBox()
        self.textwidth.setWrapping(True)
        self.textwidth.setMaximum(150)

        self.linebreak = qtutils.checkbox()
        self.editor = QtWidgets.QLineEdit()
        self.historybrowser = QtWidgets.QLineEdit()
        self.blameviewer = QtWidgets.QLineEdit()
        self.difftool = QtWidgets.QLineEdit()
        self.mergetool = QtWidgets.QLineEdit()
        self.keep_merge_backups = qtutils.checkbox()
        self.sort_bookmarks = qtutils.checkbox()
        self.bold_headers = qtutils.checkbox()
        self.save_gui_settings = qtutils.checkbox()
        self.check_spelling = qtutils.checkbox()

        self.add_row(N_('Fixed-Width Font'), self.fixed_font)
        self.add_row(N_('Font Size'), self.font_size)
        self.add_row(N_('Tab Width'), self.tabwidth)
        self.add_row(N_('Text Width'), self.textwidth)
        self.add_row(N_('Auto-Wrap Lines'), self.linebreak)
        self.add_row(N_('Editor'), self.editor)
        self.add_row(N_('History Browser'), self.historybrowser)
        self.add_row(N_('Blame Viewer'), self.blameviewer)
        self.add_row(N_('Diff Tool'), self.difftool)
        self.add_row(N_('Merge Tool'), self.mergetool)
        self.add_row(N_('Keep *.orig Merge Backups'), self.keep_merge_backups)
        self.add_row(N_('Sort bookmarks alphabetically'), self.sort_bookmarks)
        self.add_row(N_('Bold with dark background font instead of italic '
                        'headers (restart required)'), self.bold_headers)
        self.add_row(N_('Save GUI Settings'), self.save_gui_settings)
        self.add_row(N_('Check spelling'), self.check_spelling)

        self.set_config({
            prefs.SAVEWINDOWSETTINGS: (self.save_gui_settings, True),
            prefs.TABWIDTH: (self.tabwidth, 8),
            prefs.TEXTWIDTH: (self.textwidth, 72),
            prefs.LINEBREAK: (self.linebreak, True),
            prefs.SORT_BOOKMARKS: (self.sort_bookmarks, True),
            prefs.BOLD_HEADERS: (self.bold_headers, False),
            prefs.DIFFTOOL: (self.difftool, 'xxdiff'),
            prefs.EDITOR: (self.editor, os.getenv('VISUAL', 'gvim')),
            prefs.HISTORY_BROWSER: (self.historybrowser,
                                    prefs.default_history_browser()),
            prefs.BLAME_VIEWER: (self.blameviewer,
                                 prefs.default_blame_viewer()),
            prefs.MERGE_KEEPBACKUP: (self.keep_merge_backups, True),
            prefs.MERGETOOL: (self.mergetool, 'xxdiff'),
            prefs.SPELL_CHECK: (self.check_spelling, False),
        })

        self.fixed_font.currentFontChanged.connect(self.current_font_changed)
        self.font_size.valueChanged.connect(self.font_size_changed)

    def update_from_config(self):
        FormWidget.update_from_config(self)

        block = self.fixed_font.blockSignals(True)
        font = diff_font()
        self.fixed_font.setCurrentFont(font)
        self.fixed_font.blockSignals(block)

        block = self.font_size.blockSignals(True)
        font_size = font.pointSize()
        self.font_size.setValue(font_size)
        self.font_size.blockSignals(block)

    def font_size_changed(self, size):
        font = self.fixed_font.currentFont()
        font.setPointSize(size)
        cmds.do(prefs.SetConfig, self.model,
                'user', prefs.FONTDIFF, font.toString())

    def current_font_changed(self, font):
        cmds.do(prefs.SetConfig, self.model,
                'user', prefs.FONTDIFF, font.toString())


class PreferencesView(standard.Dialog):

    def __init__(self, model, parent=None):
        standard.Dialog.__init__(self, parent=parent)
        self.setWindowTitle(N_('Preferences'))
        if parent is not None:
            self.setWindowModality(QtCore.Qt.WindowModal)

        self.resize(600, 360)

        self.tab_bar = QtWidgets.QTabBar()
        self.tab_bar.setDrawBase(False)
        self.tab_bar.addTab(N_('All Repositories'))
        self.tab_bar.addTab(N_('Current Repository'))
        self.tab_bar.addTab(N_('Settings'))

        self.user_form = RepoFormWidget(model, self, source='user')
        self.repo_form = RepoFormWidget(model, self, source='repo')
        self.options_form = SettingsFormWidget(model, self)

        self.stack_widget = QtWidgets.QStackedWidget()
        self.stack_widget.addWidget(self.user_form)
        self.stack_widget.addWidget(self.repo_form)
        self.stack_widget.addWidget(self.options_form)

        self.close_button = qtutils.close_button()

        self.button_layout = qtutils.hbox(defs.no_margin, defs.spacing,
                                          self.close_button, qtutils.STRETCH)

        self.main_layout = qtutils.vbox(defs.margin, defs.spacing,
                                        self.tab_bar, self.stack_widget,
                                        self.button_layout)
        self.setLayout(self.main_layout)

        self.tab_bar.currentChanged.connect(self.stack_widget.setCurrentIndex)
        self.stack_widget.currentChanged.connect(self.update_widget)

        qtutils.connect_button(self.close_button, self.accept)
        qtutils.add_close_action(self)

        self.update_widget(0)

    def update_widget(self, idx):
        widget = self.stack_widget.widget(idx)
        widget.update_from_config()

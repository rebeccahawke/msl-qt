"""
A :class:`QtWidgets.QDialog` to prompt the user to enter notes.
"""
import os
import json
from datetime import datetime

from . import application, QtWidgets, QtCore, QtGui
from . import prompt, Button
from .constants import HOME_DIR


class NotesHistory(QtWidgets.QDialog):

    def __init__(self, parent, json_path, title, even_row_color, odd_row_color):
        """Do not instantiate directly. Use :func:`msl.qt.prompt.notes` instead."""
        QtWidgets.QDialog.__init__(self, parent=parent)

        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowTitle(title)

        self.path = json_path if json_path else os.path.join(HOME_DIR, 'qt-notes-history.json')

        self.notes = []
        self.even_row_color = QtGui.QColor(even_row_color)
        self.odd_row_color = QtGui.QColor(odd_row_color)

        self.load_json()
        self.create_widgets()

        geo = application().desktop().availableGeometry()
        self.resize(int(geo.width()*0.4), int(geo.height()*0.6))

    def append_to_history_table(self, timestamp, note):
        index = self.table.rowCount()
        self.table.insertRow(index)
        self.table.setItem(index, 0, QtWidgets.QTableWidgetItem(timestamp))
        self.table.setItem(index, 1, QtWidgets.QTableWidgetItem(note))

    def apply_filter(self):
        filter_text = self.filter_edit.text().lower()
        if not filter_text and self.table.rowCount() == len(self.notes):
            # all rows are already visible
            return

        self.table.setRowCount(0)
        for item in self.notes:
            if not filter_text or filter_text in item['timestamp'] or filter_text in item['notes'].lower():
                self.append_to_history_table(item['timestamp'], item['notes'])
        self.update_table_row_colors_and_resize()

    def clear_filter(self):
        # clear the filter text, only if there is text written in the filter
        if self.filter_edit.text():
            self.filter_edit.setText('')
            self.apply_filter()

    def clear_history(self):
        if not self.notes or not prompt.question('Clear the entire history?', default=False):
            return
        self.table.setRowCount(0)
        self.notes = []
        self.save_json()

    def create_widgets(self):
        self.note_edit = QtWidgets.QPlainTextEdit(self)
        height = self.note_edit.fontMetrics().lineSpacing()
        self.note_edit.setFixedHeight(5 * height)  # display 5 lines

        self.ok_button = Button(
            text='OK',
            left_click=self.prepend_and_close,
            tooltip='Select the note and exit',
            parent=self,
        )
        self.ok_button.add_menu_item(
            text='Clear history',
            icon=QtWidgets.QStyle.SP_DialogResetButton,
            triggered=self.clear_history,
            tooltip='Delete all notes that are in the history'
        )

        #
        # the filter field
        #
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setToolTip('Search filter for the history')
        self.filter_edit.returnPressed.connect(self.apply_filter)

        filter_button = Button(
            icon=QtWidgets.QStyle.SP_FileDialogContentsView,
            tooltip='Apply filter',
            left_click=self.apply_filter
        )
        clear_button = Button(
            icon=QtWidgets.QStyle.SP_LineEditClearButton,
            tooltip='Clear filter',
            left_click=self.clear_filter
        )

        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(filter_button)
        filter_layout.addWidget(self.filter_edit)
        filter_layout.addWidget(clear_button)
        filter_layout.setSpacing(1)

        #
        # history table
        #
        self.table = QtWidgets.QTableWidget()
        table_header = ['Timestamp', 'Notes']
        self.table.setColumnCount(len(table_header))
        self.table.setHorizontalHeaderLabels(table_header)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # disable editing the table
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # highlight entire row when selected
        self.table.horizontalHeader().setStretchLastSection(True)  # make the last column stretch to fill the table
        self.table.horizontalHeader().sectionClicked.connect(self.update_table_row_colors_and_resize)
        self.table.cellDoubleClicked.connect(self.table_double_click)
        self.table.keyPressEvent = self.table_key_press
        for item in self.notes:
            self.append_to_history_table(item['timestamp'], item['notes'])
        self.update_table_row_colors_and_resize()

        #
        # main layout
        #
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Enter a new note or select one from the history below'))
        layout.addWidget(self.note_edit)
        layout.addWidget(self.ok_button)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_json(self):
        if not os.path.isfile(self.path):
            # assume that this is a new file that will be created
            return

        with open(self.path, 'rb') as fp:
            try:
                self.notes = json.load(fp, encoding='utf-8')
            except Exception as e:
                prompt.warning('Error loading JSON file:\n{}\n\n{}'.format(self.path, e))

    def prepend_and_close(self):
        self.close()

        if not self.text():
            # no new notes were entered so there is nothing to save to the history file
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.notes.insert(0, {'timestamp': timestamp, 'notes': self.text()})
        self.save_json()

    def save_json(self):
        # ensure that the intermediate directories exist
        root = os.path.dirname(self.path)
        if root and not os.path.isdir(root):
            os.makedirs(root)

        with open(self.path, 'w') as fp:
            json.dump(self.notes, fp, indent=2, ensure_ascii=False)

    def table_double_click(self, row, col):
        self.note_edit.setPlainText(self.table.item(row, 1).text())

    def table_key_press(self, event):
        # CTRL+A pressed
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_A:
            self.table.selectAll()
            return

        if event.key() != QtCore.Qt.Key_Delete:
            return

        # sort the selected rows in reverse order for the self.table.removeRow method below
        selected = sorted([s.row() for s in self.table.selectionModel().selectedRows()], reverse=True)

        if len(selected) == self.table.rowCount():
            self.clear_history()
            return

        msg = 'this item' if len(selected) == 1 else 'these {} items'.format(len(selected))
        if not prompt.question('Remove ' + msg + ' from the history?', default=False):
            return

        for index in selected:
            self.table.removeRow(index)
            del self.notes[index]

        self.save_json()

    def text(self):
        """str: The text in the note editor"""
        return self.note_edit.toPlainText().strip()

    def update_table_row_colors_and_resize(self):
        for row in range(self.table.rowCount()):
            color = self.even_row_color if row % 2 else self.odd_row_color
            try:
                self.table.item(row, 0).setBackground(color)
                self.table.item(row, 1).setBackground(color)
            except AttributeError:
                # non-reproducible bug
                # sometimes the item in the row has a NoneTye
                # possibly do to signaling issues?
                pass
        self.table.verticalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

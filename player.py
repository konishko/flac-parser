# PyQt5 Video player
# !/usr/bin/env python

from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QMessageBox,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget, QLayout, QTextEdit)
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap
import sys
import operations_with_os as owo
from flac_parser import Parser


class AudioWindow(QMainWindow):

    def __init__(self, parent=None):
        super(AudioWindow, self).__init__(parent)
        self.setWindowTitle("Audioplayer")

        self.mediaPlayer = QMediaPlayer()

        wid = QWidget(self)
        self.setCentralWidget(wid)

        self.tables = {}
        self.name = ''
        self.file_opened = False

        self._init_control_layout()

        self._init_menu_bar()

        self._init_tool_bar()

        self.make_pic_widget()

        layout = QVBoxLayout()

        layout.addLayout(self.pic_wid)
        layout.addLayout(self.control_layout)
        layout.addLayout(self.volume_and_name_layout)

        wid.setLayout(layout)

        self.mediaPlayer.stateChanged.connect(self.media_state_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.volumeChanged.connect(self.volume_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
        self.mediaPlayer.error.connect(self.handle_error)

    def _init_menu_bar(self):
        open_action = QAction(QIcon('open.png'), '&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open song')
        open_action.triggered.connect(self.open_file)

        exit_action = QAction(QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.exit_call)

        save_action = QAction(QIcon('open.png'), '&Save picture', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save picture')
        save_action.triggered.connect(self.save_picture)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(open_action)
        file_menu.addAction(exit_action)
        file_menu.addAction(save_action)

    def _init_tool_bar(self):
        decomposition_dict = {'1': 'Stream info',
                              '2': 'Vorbis comments',
                              '3': 'Cuesheet info',
                              '4': 'Application info',
                              '5': 'Picture info'}

        self.toolbar = self.addToolBar('')

        for key in decomposition_dict.keys():
            value = decomposition_dict[key]

            action = QAction(value, self)
            action.setShortcut(key)
            action.triggered.connect(lambda checked, val=value: self.show_info(val))

            self.toolbar.addAction(action)

    def _init_control_layout(self):
        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.setShortcut('Space')
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.mediaPlayer.setPosition)

        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.sliderMoved.connect(self.mediaPlayer.setVolume)
        self.mediaPlayer.setVolume(50)
        self.volumeSlider.setValue(50)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Maximum)

        self.control_layout = QHBoxLayout()
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.addWidget(self.playButton)
        self.control_layout.addWidget(self.positionSlider)

        self.volume_and_name_layout = QHBoxLayout()
        self.volume_and_name_layout.addStretch(2)
        self.volume_and_name_layout.addWidget(self.volumeSlider)

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open song",
                                                   QDir.homePath())

        if file_name != '':
            self.file_opened = True
            self.name = file_name
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(file_name)))
            self.playButton.setEnabled(True)
            self.try_parse(file_name)

    def save_picture(self):
        if self.file_opened:
            file_name = QFileDialog.getSaveFileName(self, 'Save picture',
                                                    QDir.homePath(), '(*.{})'
                                                    .format(self.extension))[0]
            if file_name != '':
                owo.write_bytes_to_file(self.pic_bytes, file_name)

        else:
            QMessageBox.question(self, 'Error',
                                 'No file opened',
                                 QMessageBox.Ok)

    def exit_call(self):
        sys.exit(app.exec_())

    def show_pic(self):
        self.cent_lbl = self.pic_layout

    def show_info(self, info_part):
        if info_part in self.tables.keys():
            self.make_info_wid(self.tables[info_part])
            self.info_wid.setWindowTitle(info_part)
            self.info_wid.show()

        else:
            QMessageBox.question(self, 'Error',
                                 '{} not provided in this file'
                                 .format(info_part), QMessageBox.Ok)

    def try_parse(self, file_name):
        bytes = owo.read_bytes_from_file(file_name)
        if bytes[:4] == b'fLaC':
            parser = Parser(bytes[4:], False)
            parser.parse_flac()
            self.fill_tables(parser.result_dict)

            if parser.picture_exist:
                self.extension = parser.extension
                self.pic_bytes = parser.pic_bytes
                self.set_pic(self.pic_bytes)
            else:
                self.set_default_pic()

    def fill_tables(self, dict):
        for key in dict.keys():
            table = QTableWidget()
            table.setColumnCount(2)
            table.setRowCount(len(dict[key].keys()))

            table.setHorizontalHeaderLabels([key, 'Value'])

            pointer = 0
            for value_key in dict[key].keys():
                table.setItem(pointer, 0, QTableWidgetItem(value_key))
                table.setItem(pointer, 1, QTableWidgetItem(str(dict[key][value_key])))

                pointer += 1

            table.resizeColumnsToContents()
            self.tables[key] = table

    def make_info_wid(self, table):
        self.info_wid = QWidget(parent=None, flags=Qt.Window)
        self.info_wid = table
        self.info_wid.resize(table.width(), table.height())

    def make_pic_widget(self):
        self.pic_wid = QVBoxLayout()
        horizontal_layout = QHBoxLayout()

        self.pic_label = QLabel()
        self.set_default_pic()

        horizontal_layout.addStretch(1)
        horizontal_layout.addWidget(self.pic_label)
        horizontal_layout.addStretch(1)

        self.pic_wid.addStretch(1)
        self.pic_wid.addLayout(horizontal_layout)
        self.pic_wid.addStretch(1)

    def set_default_pic(self):
        pic = QPixmap('il.png')
        self.pic_label.setPixmap(pic)
        self.pic_label.resize(pic.width(), pic.height())

    def set_pic(self, bytes):
        pic = QPixmap()
        pic.loadFromData(bytes)
        self.pic_label.setPixmap(pic)
        self.pic_label.resize(pic.width(), pic.height())

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def media_state_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def position_changed(self, position):
        self.positionSlider.setValue(position)

    def duration_changed(self, duration):
        self.positionSlider.setRange(0, duration)

    def volume_changed(self, position):
        self.volumeSlider.setValue(position)

    def handle_error(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = AudioWindow()
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())

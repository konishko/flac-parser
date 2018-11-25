# PyQt5 Video player
#!/usr/bin/env python

from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QMessageBox,
        QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget, QLayout)
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap
import sys
import operations_with_os as owo
from flac_parser import Parser

class VideoWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setWindowTitle("Audioplayer")

        self.mediaPlayer = QMediaPlayer()

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

        # Create new action
        openAction = QAction(QIcon('open.png'), '&Open', self)        
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)

        # Create exit action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        saveAction = QAction(QIcon('open.png'), '&Save', self)        
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save picture')
        saveAction.triggered.connect(self.save_picture)


        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)
        fileMenu.addAction(saveAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.volumeSlider)

        self.make_pic_widget()

        stream_info_action = QAction('Stream info', self)
        stream_info_action.setShortcut('1')
        stream_info_action.triggered.connect(lambda: self.show_info('Stream info'))

        add_info_action = QAction('Vorbis comments', self)
        add_info_action.setShortcut('2')
        add_info_action.triggered.connect(lambda: self.show_info('Vorbis comments'))

        cuesheet_action = QAction('Cuesheet info', self)
        cuesheet_action.setShortcut('3')
        cuesheet_action.triggered.connect(lambda: self.show_info('Cuesheet info'))

        app_action = QAction('Application info', self)
        app_action.setShortcut('4')
        app_action.triggered.connect(lambda: self.show_info('Application info'))

        pic_info = QAction('Picture info', self)
        pic_info.setShortcut('5')
        pic_info.triggered.connect(lambda: self.show_info('Picture info'))

        self.toolbar = self.addToolBar('Biba')
        self.toolbar.addAction(stream_info_action)
        self.toolbar.addAction(add_info_action)
        self.toolbar.addAction(cuesheet_action)
        self.toolbar.addAction(app_action)
        self.toolbar.addAction(pic_info)

        layout = QVBoxLayout()

        layout.addLayout(self.pic_wid)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.volumeChanged.connect(self.volumeChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        self.tables = {}
        self.file_opened = False

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open song",
                QDir.homePath())

        if fileName != '':
            self.file_opened = True
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)
            self.try_parse(fileName)

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


    def exitCall(self):
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

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def volumeChanged(self, position):
        self.volumeSlider.setValue(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())
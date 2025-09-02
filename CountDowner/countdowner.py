from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QGridLayout, QStackedLayout, QWidget
import time
import datetime
import sys

class CreatorWindow(QWidget): #This will be the window where users can create their timers
     def __init__(self):
        super().__init__()

        self.setWindowTitle("CountDowner Creator")
        self.layout = QStackedLayout()
        self.label = QLabel("Another Window")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        #Creator Window Limits
        self.setMinimumSize(QSize(700,600))
        self.setMaximumSize(QSize(1920,1080))

class MainWindow(QMainWindow):  #QMainWindow is the parent class
    def __init__(self):
        super().__init__() #must always call this or else writing code for the main window will not work

        self.w = None #Creator Window not open by default
        self.setWindowTitle("CountDowner")

        # Window Limits
        self.setMinimumSize(QSize(400,300))
        self.setMaximumSize(QSize(1920,1080))

        # Main Window Will follow a Vertical -> Grid layout
        layout = QVBoxLayout()
        layoutGrid = QGridLayout()

        self.addButton = QPushButton("Add Timer")

        # App Title. Will be switched with a proper logo
        label = QLabel("COUNTDOWNER")
        font = label.font()
        font.setPointSize(30)
        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        layout.addWidget(label)

        layout.addLayout(layoutGrid)

        #Align the Grid Layout so that it's near the logo
        layoutGrid.setAlignment(Qt.AlignmentFlag.AlignTop)
        layoutGrid.addWidget(self.addButton)

        # Finalize layout and add it to the main window
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Add Timer Button Functionality
        self.addButton.clicked.connect(self.open_creator_window)

    def open_creator_window(self, checked):
        if self.w is None:
            self.w = CreatorWindow()
            self.w.show()
        else:
            self.w.close()
            self.w = None


        


app = QApplication([]) # window variable goes after this

window = MainWindow()
window.show() #crucial

app.exec()  # window variable goes before this

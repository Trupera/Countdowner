from PyQt6.QtCore import QTimer, QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QGridLayout, QSpinBox, QWidget, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
import time
import datetime
import sys

class ActiveTimerWindow(QWidget):
    """The replica window that runs in the background."""
    def __init__(self, h, m, s, positions):
        super().__init__()
        self.setWindowTitle("MyTimer")
        self.setFixedSize(300, 200)

        # 1. Setup UI based on Creator's values
        self.hour_label = QLabel(f"{h:02}", self)
        self.min_label = QLabel(f"{m:02}", self)
        self.sec_label = QLabel(f"{s:02}", self)
        
        # Position them where the user had them (using 'positions' dict)
        self.hour_label.move(positions['h'][0], positions['h'][1])
        self.min_label.move(positions['m'][0], positions['m'][1])
        self.sec_label.move(positions['s'][0], positions['s'][1])

        # 2. Setup the Countdown Logic
        self.remaining_seconds = h * 3600 + m * 60 + s
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        # 3. Setup System Tray Icon
        self.tray_icon = QSystemTrayIcon(self)
        # Note: You'll need a real .png or .ico file for this to show up clearly
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        
        # Create a menu for the tray icon
        tray_menu = QMenu()
        show_action = QAction("Show Timer", self)
        quit_action = QAction("Stop Timer", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.close)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            h = self.remaining_seconds // 3600
            m = (self.remaining_seconds % 3600) // 60
            s = self.remaining_seconds % 60
            self.hour_label.setText(f"{h:02}")
            self.min_label.setText(f"{m:02}")
            self.sec_label.setText(f"{s:02}")
            self.tray_icon.setToolTip(f"Timer: {h:02}:{m:02}:{s:02}")
        else:
            self.timer.stop()
            self.tray_icon.showMessage("Timer Done", "Your countdown has finished!", QSystemTrayIcon.MessageIcon.Information)

class CreatorWindow(QWidget): # This will be the window where users can create their timers
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CountDowner Creator")

        # set labels
        self.hour_label = QSpinBox(self)
        self.minute_label = QSpinBox(self)
        self.second_label = QSpinBox(self)

        self.hour_label.setRange(0, 999)
        self.minute_label.setRange(0, 59)
        self.second_label.setRange(0, 59)

        # set font
        font = self.hour_label.font()
        font.setPointSize(30)
        for label in [self.hour_label, self.minute_label, self.second_label]:
            label.setFont(font)

            label.setPrefix("") 
            label.setSuffix("")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # set alignment   
        self.hour_label.move(50, 50)
        self.minute_label.move(150, 50)
        self.second_label.move(250, 50)

        self.save_button = QPushButton("Save & Start Timer", self)
        self.save_button.move(50, 150)
        self.save_button.clicked.connect(self.save_and_launch)

        
        #Creator Window Limits
        self.setMinimumSize(QSize(700,600))
        self.setMaximumSize(QSize(1920,1080))

    def save_and_launch(self):
        # 1. Capture current state
        h = self.hour_label.value()
        m = self.minute_label.value()
        s = self.second_label.value()
        
        # Store coordinates (to replicate the "move around" feature)
        positions = {
            'h': (self.hour_label.x(), self.hour_label.y()),
            'm': (self.minute_label.x(), self.minute_label.y()),
            's': (self.second_label.x(), self.second_label.y())
        }

        # 2. Launch the background replica
        self.active_timer = ActiveTimerWindow(h, m, s, positions)
        self.active_timer.show()

        # 3. Add to Main Window list (Next Step logic)
       #self.main_window.add_saved_timer(f"Timer {h}:{m}:{s}")
        
        self.close()

        #timer
        #self.duration_seconds = 10

    #     self.timer = QTimer(self)
    #     self.timer.timeout.connect(self.update_countdown)
    #     self.timer.start(1000)
    # def update_countdown(self):
    #     if self.duration_seconds > 0:
    #         self.duration_seconds -= 1

    #         hours = self.duration_seconds // 3600
    #         minutes = (self.duration_seconds % 3600) // 60
    #         seconds = self.duration_seconds % 60
            
    #         self.hour_label.setText(f"{hours:02}")
    #         self.minute_label.setText(f"{minutes:02}")
    #         self.second_label.setText(f"{seconds:02}")
    #     else:
    #          5. Stop the timer when it reaches zero
    #         self.timer.stop()

        

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

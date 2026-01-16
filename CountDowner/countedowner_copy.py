from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                             QVBoxLayout, QWidget, QSpinBox, QSystemTrayIcon, 
                             QMenu, QListWidget, QListWidgetItem)
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QAction
import sys

# (Keep ActiveTimerWindow class from the previous step)

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
        # The timer counts down with this function
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

class CreatorWindow(QWidget):
    def __init__(self, parent_main_window, preset_data=None):
        super().__init__()
        self.main_window = parent_main_window
        self.setWindowTitle("CountDowner Creator")
        self.setMinimumSize(QSize(700, 600))

        # Inputs
        self.hour_input = QSpinBox(self)
        self.min_input = QSpinBox(self)
        self.sec_input = QSpinBox(self)
        
        # If we opened this from a preset, fill the values
        if preset_data:
            self.hour_input.setValue(preset_data['h'])
            self.min_input.setValue(preset_data['m'])
            self.sec_input.setValue(preset_data['s'])
            self.hour_input.move(*preset_data['pos_h'])
            self.min_input.move(*preset_data['pos_m'])
            self.sec_input.move(*preset_data['pos_s'])
        else:
            self.hour_input.move(50, 50)
            self.min_input.move(150, 50)
            self.sec_input.move(250, 50)

        self.save_button = QPushButton("Save & Start Timer", self)
        self.save_button.move(50, 200)
        self.save_button.clicked.connect(self.save_and_launch)

    def save_and_launch(self):
        data = {
            'h': self.hour_input.value(),
            'm': self.min_input.value(),
            's': self.sec_input.value(),
            'pos_h': (self.hour_input.x(), self.hour_input.y()),
            'pos_m': (self.min_input.x(), self.min_input.y()),
            'pos_s': (self.sec_input.x(), self.sec_input.y())
        }
        
        # Launch the background window
        self.active_timer = ActiveTimerWindow(data['h'], data['m'], data['s'], 
                                             {'h': data['pos_h'], 'm': data['pos_m'], 's': data['pos_s']})
        self.active_timer.show()

        # Save to Main Window
        self.main_window.add_saved_timer(data)
        self.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CountDowner")
        self.setMinimumSize(QSize(400, 500))

        # Layout
        layout = QVBoxLayout()
        
        self.label = QLabel("MY TIMERS")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # 1. The List Widget to show saved timers
        self.timer_list = QListWidget()
        self.timer_list.itemDoubleClicked.connect(self.load_timer)
        layout.addWidget(self.timer_list)

        self.addButton = QPushButton("Create New Timer")
        self.addButton.clicked.connect(self.open_creator)
        layout.addWidget(self.addButton)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.w = None
        # 2. Storage for the actual data
        self.saved_presets = []

    def add_saved_timer(self, data):
        """Adds a timer preset to the list and memory."""
        self.saved_presets.append(data)
        
        # Create a display string for the list
        display_text = f"Timer: {data['h']:02}:{data['m']:02}:{data['s']:02}"
        item = QListWidgetItem(display_text)
        
        # Store the index so we know which data to grab later
        item.setData(Qt.ItemDataRole.UserRole, len(self.saved_presets) - 1)
        self.timer_list.addItem(item)

    def open_creator(self):
        self.w = CreatorWindow(self)
        self.w.show()

    def load_timer(self, item):
        """Re-opens the creator with saved data when an item is double-clicked."""
        index = item.data(Qt.ItemDataRole.UserRole)
        preset_data = self.saved_presets[index]
        self.w = CreatorWindow(self, preset_data)
        self.w.show()

# Boilerplate execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
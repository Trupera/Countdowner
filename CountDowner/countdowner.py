from PyQt6.QtCore import QTimer, QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QListWidget, QListWidgetItem, QSpinBox, QWidget, QSystemTrayIcon, QMenu, QToolBar, QFontComboBox
from PyQt6.QtGui import QIcon, QAction

# First class defines the drag and drop functionality
class MovableSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mouse_press_pos = None

    def mousePressEvent(self, event):
        # Record the position where the mouse was clicked relative to the widget
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_press_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Calculate how far the mouse has moved and update widget position
        if event.buttons() == Qt.MouseButton.LeftButton and self.mouse_press_pos:
            diff = event.position().toPoint() - self.mouse_press_pos
            new_pos = self.pos() + diff
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.mouse_press_pos = None
        super().mouseReleaseEvent(event)


class ActiveTimerWindow(QWidget):
    """The replica window that runs in the background."""
    def __init__(self, h, m, s, positions, h_font, m_font, s_font):
        super().__init__()
        self.setWindowTitle("MyTimer")
        self.setMinimumSize(QSize(700, 600))

        # 1. Setup UI based on Creator's values
        self.hour_label = QLabel(f"{h:02}", self)
        self.min_label = QLabel(f"{m:02}", self)
        self.sec_label = QLabel(f"{s:02}", self)

        # Set Font
        self.hour_label.setFont(h_font)
        self.min_label.setFont(m_font)
        self.sec_label.setFont(s_font)
        
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

class CreatorWindow(QMainWindow): # This will be the window where users can create their timers
    def __init__(self, parent_main_window, preset_data=None):
        super().__init__()
        self.main_window = parent_main_window
        self.setWindowTitle("CountDowner Creator")
        self.setMinimumSize(QSize(700, 600))

        # Create Toolbar
        toolbar = QToolBar("ToolBar")
        self.addToolBar(toolbar)
        save_button = QAction("Save and Start Timer", self)
        toolbar.addAction(save_button)
        save_button.triggered.connect(self.save_and_launch)

        self.canvas = QWidget()
        self.setCentralWidget(self.canvas)

        # Inputs
        self.hour_input = MovableSpinBox(self)
        self.min_input = MovableSpinBox(self)
        self.sec_input = MovableSpinBox(self)

        # Setting Fonts
        self.hour_font = QFontComboBox(self)
        self.hour_font.move(50, 180)
        self.minute_font = QFontComboBox(self)
        self.minute_font.move(200, 180)
        self.second_font = QFontComboBox(self)
        self.second_font.move(350, 180)

        self.hour_font.currentFontChanged.connect(self.change_font)
        self.minute_font.currentFontChanged.connect(self.change_font)
        self.second_font.currentFontChanged.connect(self.change_font)

        # If we opened this from a preset, fill the values
        if preset_data:
            self.hour_input.setValue(preset_data['h'])
            self.min_input.setValue(preset_data['m'])
            self.sec_input.setValue(preset_data['s'])
            self.hour_input.move(*preset_data['pos_h'])
            self.min_input.move(*preset_data['pos_m'])
            self.sec_input.move(*preset_data['pos_s'])
            self.hour_input.setFont(preset_data['h_font'])
            self.min_input.setFont(preset_data['m_font'])
            self.sec_input.setFont(preset_data['s_font'])
        else:
            self.hour_input.move(50, 100)
            self.min_input.move(200, 100)
            self.sec_input.move(350, 100)
    
    def change_font(self):
        hour = self.hour_input.font()
        hour.setPointSize(30)
        minute = self.min_input.font()
        minute.setPointSize(30)
        second = self.sec_input.font()
        second.setPointSize(30)

        self.hour_input.setFont(self.hour_font.currentFont())
        self.min_input.setFont(self.minute_font.currentFont())
        self.sec_input.setFont(self.second_font.currentFont())
        
    def save_and_launch(self):
        data = {
            'h': self.hour_input.value(),
            'm': self.min_input.value(),
            's': self.sec_input.value(),
            'pos_h': (self.hour_input.x(), self.hour_input.y()),
            'pos_m': (self.min_input.x(), self.min_input.y()),
            'pos_s': (self.sec_input.x(), self.sec_input.y()),
            'h_font': self.hour_input.font(),
            'm_font': self.min_input.font(),
            's_font': self.sec_input.font()
        }
        
        # Launch the background window
        self.active_timer = ActiveTimerWindow(data['h'], data['m'], data['s'], 
                                             {'h': data['pos_h'], 'm': data['pos_m'], 's': data['pos_s']}, data['h_font'], data['m_font'], data['s_font'])
        self.active_timer.show()

        # Save to Main Window
        self.main_window.add_saved_timer(data)
        self.close()
    

class MainWindow(QMainWindow):  #QMainWindow is the parent class
    def __init__(self):
        super().__init__() #must always call this or else writing code for the main window will not work

        self.w = None #Creator Window not open by default
        self.setWindowTitle("CountDowner")

        # Window Limits
        self.setMinimumSize(QSize(400,300))
        
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


        


app = QApplication([]) # window variable goes after this

window = MainWindow()
window.show() #crucial

app.exec()  # window variable goes before this

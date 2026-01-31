from PyQt6.QtCore import QTimer, QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QListWidget, QSpinBox, QWidget, QSystemTrayIcon, QMenu, QToolBar, QFontComboBox, QInputDialog, QFileDialog
from PyQt6.QtGui import QAction, QPixmap, QMovie
from playsound import playsound


# First class defines the drag and drop functionality
class MovableSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True) # Required to detect hover without clicking
        self.margin = 10            # How close to the edge to trigger resize
        self.is_resizing = False
        self.is_moving = False
        self.drag_start_pos = None
        self.initial_geometry = None

    def _get_edge(self, pos):
        """Returns which edge the mouse is over."""
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        
        if x > w - self.margin and y > h - self.margin: return "bottom-right"
        if x > w - self.margin: return "right"
        if y > h - self.margin: return "bottom"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_edge(event.position().toPoint())
            if edge:
                self.is_resizing = True
            else:
                self.is_moving = True
            
            self.drag_start_pos = event.globalPosition().toPoint()
            self.initial_geometry = self.geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        edge = self._get_edge(pos)

        # 1. Update Cursor Icon
        if not self.is_resizing and not self.is_moving:
            if edge == "bottom-right": self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge == "right": self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge == "bottom": self.setCursor(Qt.CursorShape.SizeVerCursor)
            else: self.setCursor(Qt.CursorShape.ArrowCursor)

        # 2. Handle Resizing
        if self.is_resizing:
            diff = event.globalPosition().toPoint() - self.drag_start_pos
            new_width = max(50, self.initial_geometry.width() + diff.x())
            new_height = max(40, self.initial_geometry.height() + diff.y())
            self.resize(new_width, new_height)
            self.update_font_size() # Sync font with new size

        # 3. Handle Moving
        elif self.is_moving:
            diff = event.globalPosition().toPoint() - self.drag_start_pos
            self.move(self.initial_geometry.topLeft() + diff)
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        self.is_moving = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def update_font_size(self):
        """Scales the font size based on the current height of the widget."""
        new_font = self.font()
        # Roughly 60% of the widget height works well for digits
        new_font.setPointSize(int(self.height() * 0.6))
        self.setFont(new_font)


class ActiveTimerWindow(QWidget):
    """The replica window that runs in the background."""
    def __init__(self, h, m, s, positions, h_font, m_font, s_font, alarm, bg_path):
        super().__init__()
        self.setWindowTitle("MyTimer")
        self.setMinimumSize(QSize(700, 600))
        self.alarm = alarm
        self.bg_path = bg_path
        print(self.bg_path)

        # 1. Setup UI based on Creator's values
        self.hour_label = QLabel(f"{h:02}", self)
        self.min_label = QLabel(f"{m:02}", self)
        self.sec_label = QLabel(f"{s:02}", self)

        # Set Font
        self.hour_label.setFont(h_font)
        self.min_label.setFont(m_font)
        self.sec_label.setFont(s_font)

        # Set Background
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 700, 600)
        self.bg_label.setScaledContents(True) 
        self.bg_label.lower() 

        if not self.bg_path == None:
            if self.bg_path.lower().endswith(".gif"):
                # Handle Animated GIF
                movie = QMovie(self.bg_path)
                self.bg_label.setMovie(movie)
                movie.start()
            else:
                # Handle Static Image
                pixmap = QPixmap(self.bg_path)
                self.bg_label.setPixmap(pixmap)
        
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
            if not self.alarm == None:
                playsound(self.alarm)


class CreatorEditWindow(QMainWindow): # This will be the window where users can create their timers
    def __init__(self, parent_main_window, name, preset_data=None):
        super().__init__()
        self.main_window = parent_main_window
        self.name = name
        self.alarm = None
        self.setWindowTitle("CountDowner Creator")
        self.setMinimumSize(QSize(700, 600))


        # Set Background Elements
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 700, 600)
        self.bg_label.setScaledContents(True) # Make image fill the label
        self.bg_label.lower() # Send to back so it doesn't cover numbers
        self.bg_path = None

        # Create Toolbar
        toolbar = QToolBar("ToolBar")
        self.addToolBar(toolbar)
        savecurrent_button = QAction("Save", self)
        toolbar.addAction(savecurrent_button)
        run_button = QAction("Run Timer", self)
        toolbar.addAction(run_button)
        alarm_button = QAction("Alarm Sound", self)
        toolbar.addAction(alarm_button)
        background_button = QAction("Set Background", self)
        toolbar.addAction(background_button)
        savecurrent_button.triggered.connect(self.savecurrent)
        run_button.triggered.connect(self.run_timer)
        alarm_button.triggered.connect(self.open_alarm_sound)
        background_button.triggered.connect(self.change_background)
    
        self.canvas = QWidget()
        self.setCentralWidget(self.canvas)
        self.canvas.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Inputs
        self.hour_input = MovableSpinBox(self)
        self.min_input = MovableSpinBox(self)
        self.sec_input = MovableSpinBox(self)

        for widget in [self.hour_input, self.min_input, self.sec_input]:
            widget.setMinimumSize(60, 40)
            widget.update_font_size() # Set initial font scale



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

            if not preset_data['background'] == None:
                self.bg_path = preset_data['background']
                if preset_data['background'].lower().endswith(".gif"):
                    movie = QMovie(preset_data['background'])
                    self.bg_label.setMovie(movie)
                    movie.start()
                else:
                    pixmap = QPixmap(preset_data['background'])
                    self.bg_label.setPixmap(pixmap)
        else:
            self.hour_input.move(50, 100)
            self.min_input.move(200, 100)
            self.sec_input.move(350, 100)

    def open_alarm_sound(self):
        # The function returns a tuple (file_path, filter). We need the path.
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            caption="Select an Alarm Sound",
            directory="", # Start directory (empty string defaults to current working directory)
            filter="All Files (*.*);;MP3 Files (*.mp3);;WAV Files (*.wav)" # File filters
        )

        if file_path:
            self.alarm = file_path
    
    def change_background(self):
        file_filter = "Images (*.png *.jpg *.jpeg *.gif)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Background", "", file_filter)
        
        if path:
            self.bg_path = path
            if path.lower().endswith(".gif"):
                # Handle Animated GIF
                movie = QMovie(path)
                self.bg_label.setMovie(movie)
                movie.start()
            else:
                # Handle Static Image
                pixmap = QPixmap(path)
                self.bg_label.setPixmap(pixmap)

    # Make sure background resizes if the window resizes
    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
    
    def change_font(self):
        hour = self.hour_input.font()
        hour.setPointSize(50)
        minute = self.min_input.font()
        minute.setPointSize(50)
        second = self.sec_input.font()
        second.setPointSize(50)

        self.hour_input.setFont(self.hour_font.currentFont())
        self.min_input.setFont(self.minute_font.currentFont())
        self.sec_input.setFont(self.second_font.currentFont())
    
    def savecurrent(self):
        data = {
            'name': self.name,
            'h': self.hour_input.value(),
            'm': self.min_input.value(),
            's': self.sec_input.value(),
            'pos_h': (self.hour_input.x(), self.hour_input.y()),
            'pos_m': (self.min_input.x(), self.min_input.y()),
            'pos_s': (self.sec_input.x(), self.sec_input.y()),
            'h_font': self.hour_input.font(),
            'm_font': self.min_input.font(),
            's_font': self.sec_input.font(),
            'size_h': (self.hour_input.width(), self.hour_input.height()), # Save the size!
            'size_m': (self.min_input.width(), self.min_input.height()),
            'size_s': (self.sec_input.width(), self.sec_input.height()),
            'background': self.bg_path
        }

        # Save to Main Window
        self.main_window.save_timer(data)
        self.close()

    def run_timer(self):
        self.active_timer = ActiveTimerWindow(self.hour_input.value(), self.min_input.value(), self.sec_input.value(), 
                                            {'h': (self.hour_input.x(), self.hour_input.y()), 'm': (self.min_input.x(), self.min_input.y()), 's': (self.sec_input.x(), self.sec_input.y())},  self.hour_input.font(), self.min_input.font(), self.sec_input.font(), self.alarm, self.bg_path)
        self.active_timer.show()


class CreatorWindow(QMainWindow): # This will be the window where users can create their timers
    def __init__(self, parent_main_window, preset_data=None):
        super().__init__()
        self.main_window = parent_main_window
        self.alarm = None
        self.setWindowTitle("CountDowner Creator")
        self.setMinimumSize(QSize(700, 600))

        # Set Background Elements
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 700, 600)
        self.bg_label.setScaledContents(True) # Make image fill the label
        self.bg_label.lower() # Send to back so it doesn't cover numbers
        self.bg_path = None

        # Create Toolbar
        toolbar = QToolBar("ToolBar")
        self.addToolBar(toolbar)
        save_button = QAction("Save as New", self)
        toolbar.addAction(save_button)
        run_button = QAction("Run Timer", self)
        toolbar.addAction(run_button)
        alarm_button = QAction("Alarm Sound", self)
        toolbar.addAction(alarm_button)
        background_button = QAction("Set Background", self)
        toolbar.addAction(background_button)
        save_button.triggered.connect(self.save_as_new)
        run_button.triggered.connect(self.run_timer)
        alarm_button.triggered.connect(self.open_alarm_sound)
        background_button.triggered.connect(self.change_background)

        self.canvas = QWidget()
        self.setCentralWidget(self.canvas)
        self.canvas.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

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

        # Set Number Size

    def open_alarm_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select an Alarm Sound",
            directory="", # Start directory (empty string defaults to current working directory)
            filter="MP3 Files (*.mp3);;WAV Files (*.wav)" # File filters
        )

        if file_path:
            self.alarm = file_path

    def change_background(self):
        file_filter = "Images (*.png *.jpg *.jpeg *.gif)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Background", "", file_filter)
        
        if path:
            self.bg_path = path
            if path.lower().endswith(".gif"):
                # Handle Animated GIF
                movie = QMovie(path)
                self.bg_label.setMovie(movie)
                movie.start()
            else:
                # Handle Static Image
                pixmap = QPixmap(path)
                self.bg_label.setPixmap(pixmap)

    # Make sure background resizes if the window resizes
    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
    
    def change_font(self):
        hour = self.hour_input.font()
        hour.setPointSize(50)
        minute = self.min_input.font()
        minute.setPointSize(50)
        second = self.sec_input.font()
        second.setPointSize(50)

        self.hour_input.setFont(self.hour_font.currentFont())
        self.min_input.setFont(self.minute_font.currentFont())
        self.sec_input.setFont(self.second_font.currentFont())
    
    def save_as_new(self):
        name, ok = QInputDialog.getText(self, "Save Timer", "Enter a name for your timer:")
        
        # If the user clicks 'Cancel', we stop the save process
        if not ok:
            return 
            
        # If they left it blank, give it a default
        if not name.strip():
            name = f"{self.hour_input.value()}:{self.min_input.value()}:{self.sec_input.value()}"


        data = {
            'name': name,
            'h': self.hour_input.value(),
            'm': self.min_input.value(),
            's': self.sec_input.value(),
            'pos_h': (self.hour_input.x(), self.hour_input.y()),
            'pos_m': (self.min_input.x(), self.min_input.y()),
            'pos_s': (self.sec_input.x(), self.sec_input.y()),
            'h_font': self.hour_input.font(),
            'm_font': self.min_input.font(),
            's_font': self.sec_input.font(),
            'size_h': (self.hour_input.width(), self.hour_input.height()), # Save the size!
            'size_m': (self.min_input.width(), self.min_input.height()),
            'size_s': (self.sec_input.width(), self.sec_input.height()),
            'background': self.bg_path
        }

        # Save to Main Window
        self.main_window.add_saved_timer(data)
        self.close()

    def run_timer(self):
        self.active_timer = ActiveTimerWindow(self.hour_input.value(), self.min_input.value(), self.sec_input.value(), 
                                            {'h': (self.hour_input.x(), self.hour_input.y()), 'm': (self.min_input.x(), self.min_input.y()), 's': (self.sec_input.x(), self.sec_input.y())},  self.hour_input.font(), self.min_input.font(), self.sec_input.font(), self.alarm,  self.bg_path)
        self.active_timer.show()
    

class MainWindow(QMainWindow):  #QMainWindow is the parent class
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CountDowner")
        self.setMinimumSize(QSize(400, 500))

        layout = QVBoxLayout()
        
        self.label = QLabel("MY TIMERS")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # 1. Setup the List Widget with Context Menu Policy
        self.timer_list = QListWidget()
        self.timer_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.timer_list.customContextMenuRequested.connect(self.show_context_menu)
        
        self.timer_list.itemDoubleClicked.connect(self.load_timer)
        layout.addWidget(self.timer_list)

        self.addButton = QPushButton("Create New Timer")
        self.addButton.clicked.connect(self.open_creator)
        layout.addWidget(self.addButton)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.w = None
        self.saved_presets = []

    def show_context_menu(self, position):
        """Triggered when the user right-clicks the list."""
        item = self.timer_list.itemAt(position)
        
        if item:
            menu = QMenu()
            delete_action = QAction("Delete Timer", self)
            
            # Using a lambda to pass the specific item to the delete function
            delete_action.triggered.connect(lambda: self.delete_timer(item))
            
            menu.addAction(delete_action)
            # Display the menu at the cursor's position
            menu.exec(self.timer_list.mapToGlobal(position))

    def delete_timer(self, item):
        """Removes the timer from the UI and the data list."""
        # Find which row was clicked
        row = self.timer_list.row(item)
        
        # Remove from the QListWidget UI
        self.timer_list.takeItem(row)
        
        # Remove from our saved_presets data list
        if 0 <= row < len(self.saved_presets):
            self.saved_presets.pop(row)
            
        print(f"Deleted timer at row {row}")

    def add_saved_timer(self, data):
        self.saved_presets.append(data)
        display_text = f"Timer: {data['name']}"
        self.timer_list.addItem(display_text)

    def save_timer(self, data):
        display_text = f"{data['name']}"
        for i in range(self.timer_list.count()):
            item = self.timer_list.item(i)
            if(item.text() == display_text):
                row = self.timer_list.row(item)
                self.timer_list.takeItem(row)
                if 0 <= row < len(self.saved_presets):
                    self.saved_presets.pop(row)
        self.saved_presets.append(data)
        self.timer_list.addItem(display_text)


    def open_creator(self):
        self.w = CreatorWindow(self)
        self.w.show()

    def load_timer(self, item):
        row = self.timer_list.row(item)
        if 0 <= row < len(self.saved_presets):
            preset_data = self.saved_presets[row]
            self.w = CreatorEditWindow(self, item.text(), preset_data)
            self.w.show()

        


app = QApplication([]) # window variable goes after this

window = MainWindow()
window.show() #crucial

app.exec()  # window variable goes before this

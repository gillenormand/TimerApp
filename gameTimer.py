# -*- coding: utf-8 -*-
#version 0.8.5a
import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QInputDialog, QMessageBox, QDesktopWidget, QListWidgetItem, QWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon

class TimerApp(QDialog):
    def __init__(self):
        super().__init__()
        self.appName = "appTimer"
        self.version = "0.8.5a"
        self.setWindowTitle(self.appName + " " + self.version)
        self.resize(500, 500)  # screen size
        self.center_window()   # window centring
        self.setWindowIcon(QIcon('img.ico'))
        
        # --- Attributes ---
        self.entries = {}
        self.currentEntry = None
        self.currentTime = 0
        self.sessionTimes = {}  # current session timer array
        self.timerRunning = False
        self.lastEntry = None
        
        # --- Layouts ---
        mainLayout = QVBoxLayout()
        buttonLayout = QHBoxLayout()
        appControlLayout = QHBoxLayout()
        
        # --- Widgets ---
        self.labelName = QLabel("!!!pick an entry!!!")
        self.font = QFont("Arial", 18)
        self.font.setBold(True)
        self.labelName.setAlignment(Qt.AlignCenter)
        self.labelName.setFont(self.font)
        
        self.timerDisplay = QLabel("0:00:00")
        self.timerDisplay.setAlignment(Qt.AlignCenter)
        self.timerDisplay.setStyleSheet("""
            font-size: 96px;  /* font size main timer */
            border: 5px solid #00000000;  /* timer border */
            padding: 10px;  /* timer padding */
            color: #ffffff;  /* timer color */
        """)
        
        self.sessionTimerDisplay = QLabel("Current Session: 0:00:00")
        self.sessionTimerDisplay.setAlignment(Qt.AlignCenter)
        self.sessionTimerDisplay.setStyleSheet("font-size: 24px;")  #font size
        
        self.listWidget = QListWidget()
        self.listWidget.itemClicked.connect(self.selectEntry)
        self.timeLabels = {}
        
        self.startButton = QPushButton("Start")
        self.startButton.setEnabled(False)
        self.startButton.clicked.connect(self.startTimer)
        
        self.pauseButton = QPushButton("Pause")
        self.pauseButton.setEnabled(False)
        self.pauseButton.clicked.connect(self.pauseTimer)
        
        self.addButton = QPushButton("Add New Entry")
        self.addButton.clicked.connect(self.addEntry)
        
        self.removeButton = QPushButton("Remove Entry")
        self.removeButton.setEnabled(False)
        self.removeButton.clicked.connect(self.removeEntry)

        self.addMinutesButton = QPushButton("+/- minutes")
        self.addMinutesButton.setEnabled(False)
        self.addMinutesButton.clicked.connect(self.addMinutes)        

        self.editButton = QPushButton("Edit Time")
        self.editButton.setEnabled(False)
        self.editButton.clicked.connect(self.editTime)
        
        # --- Set Styles ---
        self.setStyleSheet("""
            QDialog {
                background-color: #161616;
            }
            QLabel {
                color: #ffffff;
            }
            QListWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            QListWidget:disabled {
                background-color: #555555;  /* Background color when disabled */
                color: #aaaaaa;            
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
            QPushButton {
                font-size:12px;
                font-weight: bold;
                background-color: #1e1e1e;
                color: #ffffff;
                padding: 5px;
            }
            QPushButton:hover {
                border: 1px solid #ff8728;
            }
            QLabel#timerDisplay {
                border: 5px solid #ff8728;
                padding: 10px;
            }
        """)
        
        # --- Add Widgets to Layout ---
        mainLayout.addWidget(self.labelName)
        mainLayout.addWidget(self.timerDisplay)
        mainLayout.addWidget(self.sessionTimerDisplay)  # add timer of curr. sess.
        buttonLayout.addWidget(self.startButton)
        buttonLayout.addWidget(self.pauseButton)
        mainLayout.addLayout(buttonLayout)
        appControlLayout.addWidget(self.addButton)
        appControlLayout.addWidget(self.removeButton)
        appControlLayout.addWidget(self.addMinutesButton)
        appControlLayout.addWidget(self.editButton)
        mainLayout.addLayout(appControlLayout)
        mainLayout.addWidget(self.listWidget)
        self.setLayout(mainLayout)
        
        # --- Timer ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        
        # load settings
        self.loadSettings()
        self.loadEntriesFromJson()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def saveLastEntry(self):
        """Save window settings to JSON file."""
        settings = {
            'lastEntry': self.lastEntry  # save last entry
        }
        with open("settings.json", "w") as file:
            json.dump(settings, file)

    def loadEntriesFromJson(self):
        """Load entries from JSON file"""
        if os.path.exists("apps.json"):
            try:
                with open("apps.json", "r") as file:
                    self.entries = json.load(file)
                    if not isinstance(self.entries, dict) or not all(isinstance(v, int) for v in self.entries.values()):
                        raise ValueError("Invalid entries.json format")
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.warning(self, "Error", f"Failed to load entries: {str(e)}")
                self.entries = {}
        else:
            self.entries = {}
        self.populateListWidget()
        
        # Try to select the last entry
        if self.lastEntry and self.lastEntry in self.entries:
             found_item = None
             for i in range(self.listWidget.count()):
                 item = self.listWidget.item(i)
                 widget = self.listWidget.itemWidget(item)
                 if widget:
                    # Get text from first element of layout
                     label = widget.layout().itemAt(0).widget()
                     if isinstance(label, QLabel) and label.text() == self.lastEntry:
                         found_item = item
                         break
            
             if found_item:
                 self.selectEntry(found_item)
                 # Force visual selection highlight
                 self.listWidget.setCurrentItem(found_item)
                 self.listWidget.setFocus()

    def loadSettings(self):
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as file:
                    settings = json.load(file)
                    self.lastEntry = settings.get('lastEntry')
            except (json.JSONDecodeError, IOError):
                self.lastEntry = None

    def saveEntriesToJson(self):
        try:
            with open("apps.json", "w") as file:
                json.dump(self.entries, file, indent=4)
        except IOError as e:
            QMessageBox.warning(self, "Error", f"Failed to save apps: {str(e)}")

    def populateListWidget(self):
        self.listWidget.clear()
        self.timeLabels.clear()
        items = [app for app in sorted(self.entries, key=lambda k: self.entries[k], reverse=True)]
        for app in items:
            item = QListWidgetItem()  # empty element of the list

            widget = QWidget()  # container for a string
            layout = QHBoxLayout()  # create horizontal layout
            
            # create QLabel for entry name
            entryLabel = QLabel(app)
            entryLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
            
            # create QLabel for time
            timeLabel = QLabel(self.format_time(self.entries[app]))
            timeLabel.setStyleSheet("min-width: 100px; text-align: right;")
            timeLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # add widgets to layout
            layout.addWidget(entryLabel)
            layout.addWidget(timeLabel)
            layout.setContentsMargins(5, 0, 5, 0)  # margins
            
            # layout into container
            widget.setLayout(layout)
            
            # adjust element of the list
            item.setSizeHint(widget.sizeHint())
            
            # add elements
            self.listWidget.addItem(item)
            self.listWidget.setItemWidget(item, widget)
            self.timeLabels[app] = timeLabel

    def selectEntry(self, item):
        """Handle entry selection."""
        widget = self.listWidget.itemWidget(item)
        if widget:
            app_label = widget.layout().itemAt(0).widget()
            self.currentEntry = app_label.text()
            self.currentTime = self.entries.get(self.currentEntry, 0)
            
            # inicialization of time seesion if not inicialisiated
            if self.currentEntry not in self.sessionTimes:
                self.sessionTimes[self.currentEntry] = 0
                
            self.labelName.setText(f"{self.currentEntry}")
            self.updateTimerDisplay()
            self.update_sessionTimerDisplay()  # update timer session
            self.startButton.setEnabled(True)
            self.removeButton.setEnabled(True)
            self.editButton.setEnabled(True)
            self.addMinutesButton.setEnabled(True)

    def addEntry(self):
        """Add a new entry."""
        app_name, ok = QInputDialog.getText(self, "Add Entry", "Enter entry name:")
        if ok and app_name.strip():
            app_name = app_name.strip()
            if app_name in self.entries:
                QMessageBox.warning(self, "Warning", "Entry already exists.")
            else:
                self.entries[app_name] = 0
                
                # create new element of the list
                item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout()
                
                # create QLabel for entry name
                app_label = QLabel(app_name)
                app_label.setStyleSheet("font-size: 14px; font-weight: bold;")
                
                # create QLabel for time
                time_label = QLabel("0:00:00")
                time_label.setStyleSheet("min-width: 100px; text-align: right;")
                time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # layout
                layout.addWidget(app_label)
                layout.addWidget(time_label)
                layout.setContentsMargins(5, 0, 5, 0)
                widget.setLayout(layout)
                
                item.setSizeHint(widget.sizeHint())
                
                # add elements
                self.listWidget.addItem(item)
                self.listWidget.setItemWidget(item, widget)
                self.timeLabels[app_name] = time_label
                
                self.saveEntriesToJson()
                self.selectEntry(item)
        else:
            QMessageBox.warning(self, "Warning", "Entry name cannot be empty.")

    def removeEntry(self):
        """Remove the selected entry."""
        if self.currentEntry:
            confirm = QMessageBox.question(
                self, "Confirm Remove",
                f"Are you sure you want to remove {self.currentEntry}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                if self.currentEntry == self.lastEntry:
                    self.lastEntry = None  # set None, if deleted entry was the last
                self.entries.pop(self.currentEntry, None)  # remove entry from list
                self.sessionTimes.pop(self.currentEntry, None)  # remove time of this entry
                self.populateListWidget()
                self.saveEntriesToJson()
                self.reset_ui()  # reset ui
            if self.currentEntry in self.timeLabels:
                del self.timeLabels[self.currentEntry]

    def editTime(self):
        """Edit the time for the selected entry."""
        if self.currentEntry:
            new_time, ok = QInputDialog.getInt(self, "Edit Time", "Enter new time (seconds):", self.currentTime, 0)
            if ok:
                self.entries[self.currentEntry] = new_time
                self.currentTime = new_time
                self.updateTimerDisplay()
                self.saveEntriesToJson()
                if self.currentEntry in self.timeLabels:
                    self.timeLabels[self.currentEntry].setText(self.format_time(new_time))

    def addMinutes(self):
        """Add minutes accepting both dot and comma, starting with empty field."""
        if self.currentEntry:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QDoubleSpinBox
            from PyQt5.QtCore import Qt, QTimer
            from PyQt5.QtGui import QKeyEvent

            class FlexibleDoubleSpinBox(QDoubleSpinBox):
                def __init__(self):
                    super().__init__()
                    self.setRange(-9999.0, 9999.0)
                    self.setDecimals(2)
                    self.setSingleStep(0.1)
                    # remove arrows (optional)
                    # self.setButtonSymbols(QDoubleSpinBox.NoButtons) 

                def keyPressEvent(self, event):
                    # swap . to ,
                    if event.key() == Qt.Key_Period:
                        event = QKeyEvent(event.type(), Qt.Key_Comma, event.modifiers(), ",")
                    super().keyPressEvent(event)

                def textFromValue(self, value):
                    return super().textFromValue(value)

            dialog = QDialog(self)
            dialog.setWindowTitle("+/- minutes")
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            label = QLabel("Enter minutes (e.g. -5.5 or -5,5):")
            layout.addWidget(label)
            
            spin_box = FlexibleDoubleSpinBox()
            spin_box.setValue(0.0)
            spin_box.setStyleSheet("font-size: 14px; padding: 5px;")
            layout.addWidget(spin_box)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            # hack: make empty field after popup
            # use singleShot(0), for update dialogue window
            QTimer.singleShot(0, lambda: spin_box.lineEdit().setText(""))
            
            # and empty selection to stand cursor at left position
            QTimer.singleShot(0, lambda: spin_box.lineEdit().deselect())

            if dialog.exec_() == QDialog.Accepted:
                text = spin_box.lineEdit().text()
                
                if not text.strip():
                    val = 0.0
                else:
                    clean_text = text.replace(',', '.')
                    try:
                        val = float(clean_text)
                    except ValueError:
                        val = 0.0
                
                seconds_to_add = int(val * 60)
                
                self.currentTime += seconds_to_add
                
                if self.currentTime < 0:
                    self.currentTime = 0
                    
                self.entries[self.currentEntry] = self.currentTime
                self.updateTimerDisplay()
                self.saveEntriesToJson()
                
                if self.currentEntry in self.timeLabels:
                    self.timeLabels[self.currentEntry].setText(self.format_time(self.currentTime))


    def startTimer(self):
        """Start the timer."""
        if self.currentEntry:
            self.lastEntry = self.currentEntry  # save curr entry like a last
            self.saveLastEntry()  # save last entry to a file
            self.timer.start(1000)
            self.timerRunning = True
            self.startButton.setEnabled(False)
            self.pauseButton.setEnabled(True)
            self.addButton.setEnabled(False)
            self.removeButton.setEnabled(False)
            self.editButton.setEnabled(False)
            self.addMinutesButton.setEnabled(False)
            self.listWidget.setEnabled(False)
            self.timerDisplay.setStyleSheet("font-size: 96px; border: 5px solid #ff8728; padding: 10px;")

    def pauseTimer(self):
        """Pause the timer."""
        self.timer.stop()
        self.timerRunning = False
        self.entries[self.currentEntry] = self.currentTime
        self.saveEntriesToJson()
        self.startButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.addButton.setEnabled(True)
        self.removeButton.setEnabled(True)
        self.editButton.setEnabled(True)
        self.addMinutesButton.setEnabled(True)
        self.listWidget.setEnabled(True)
        self.timerDisplay.setStyleSheet("font-size: 96px; border: 5px solid #00000000; padding: 10px;")

    def updateTime(self):
        self.currentTime += 1
        self.sessionTimes[self.currentEntry] += 1
        if not hasattr(self, 'save_counter'):
            self.save_counter = 0
        self.save_counter += 1
        if self.save_counter >= 10:
            self.save_counter = 0
            self.entries[self.currentEntry] = self.currentTime
            self.saveEntriesToJson()
        self.updateTimerDisplay()
        self.update_sessionTimerDisplay()
        if self.currentEntry in self.timeLabels:
            self.timeLabels[self.currentEntry].setText(self.format_time(self.currentTime))

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02}:{secs:02}"

    def updateTimerDisplay(self):
        self.timerDisplay.setText(self.format_time(self.currentTime))

    def update_sessionTimerDisplay(self):
        session_time = self.sessionTimes.get(self.currentEntry, 0)
        self.sessionTimerDisplay.setText(f"Session: {self.format_time(session_time)}")

    def reset_ui(self):
        """Reset UI to the default state."""
        self.currentEntry = None
        self.currentTime = 0
        self.timer.stop()
        self.timerRunning = False
        self.labelName.setText("!!!pick an entry!!!")
        self.timerDisplay.setText("0:00:00")
        self.sessionTimerDisplay.setText("Session: 0:00:00")  # reset timer session
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        self.removeButton.setEnabled(False)
        self.editButton.setEnabled(False)
        self.addMinutesButton.setEnabled(False)
        self.listWidget.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerApp()
    window.show()
    sys.exit(app.exec_())

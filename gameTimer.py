# -*- coding: utf-8 -*-
#version 0.8
import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QInputDialog, QMessageBox, QDesktopWidget, QListWidgetItem, QWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon

class GameTimerApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Timer")
        self.resize(500, 500)  # screen size
        self.center_window()   # window centring
        self.setWindowIcon(QIcon('img.ico'))
        
        # --- Attributes ---
        self.games = {}
        self.current_game = None
        self.current_time = 0
        self.session_times = {}  # current session timer array
        self.timer_running = False
        self.last_game = None
        
        # --- Layouts ---
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        game_control_layout = QHBoxLayout()
        
        # --- Widgets ---
        self.label_name = QLabel("!!!pick a game!!!")
        self.font = QFont("Arial", 18)
        self.font.setBold(True)
        self.label_name.setAlignment(Qt.AlignCenter)
        self.label_name.setFont(self.font)
        
        self.timer_display = QLabel("0:00:00")
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setStyleSheet("""
            font-size: 96px;  /* Размер шрифта для основного таймера */
            border: 5px solid #00000000;  /* Бордер вокруг таймера */
            padding: 10px;  /* Внутренний отступ для таймера */
            color: #ffffff;  /* Цвет текста таймера */
        """)
        
        self.session_timer_display = QLabel("Current Session: 0:00:00")
        self.session_timer_display.setAlignment(Qt.AlignCenter)
        self.session_timer_display.setStyleSheet("font-size: 24px;")  #font size
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.select_game)
        self.time_labels = {}
        
        self.start_button = QPushButton("Start")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_timer)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_timer)
        
        self.add_button = QPushButton("Add New Game")
        self.add_button.clicked.connect(self.add_game)
        
        self.remove_button = QPushButton("Remove Game")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self.remove_game)
        
        self.edit_button = QPushButton("Edit Time")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self.edit_time)
        
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
            QLabel#timer_display {
                border: 5px solid #ff8728;
                padding: 10px;
            }
        """)
        
        # --- Add Widgets to Layout ---
        main_layout.addWidget(self.label_name)
        main_layout.addWidget(self.timer_display)
        main_layout.addWidget(self.session_timer_display)  # add timer of curr. sess.
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        main_layout.addLayout(button_layout)
        game_control_layout.addWidget(self.add_button)
        game_control_layout.addWidget(self.remove_button)
        game_control_layout.addWidget(self.edit_button)
        main_layout.addLayout(game_control_layout)
        main_layout.addWidget(self.list_widget)
        self.setLayout(main_layout)
        
        # --- Timer ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        
        # load settings
        self.load_settings()
        self.load_games_from_json()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def saveLastGame(self):
        """Save window settings to JSON file."""
        settings = {
            'last_game': self.last_game  # save last game
        }
        with open("settings.json", "w") as file:
            json.dump(settings, file)

    def load_games_from_json(self):
        """Load games from JSON file."""
        if os.path.exists("games.json"):
            try:
                with open("games.json", "r") as file:
                    self.games = json.load(file)
                    if not isinstance(self.games, dict) or not all(isinstance(v, int) for v in self.games.values()):
                        raise ValueError("Invalid games.json format")
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.warning(self, "Error", f"Failed to load games: {str(e)}")
                self.games = {}
        else:
            self.games = {}
        self.populate_list_widget()
        
        # Try to select the last game
        if self.last_game in self.games:
            item = self.list_widget.findItems(self.last_game, Qt.MatchExactly)
            if item:
                self.select_game(item[0])  # Select the last game if it exists

    def load_settings(self):
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as file:
                    settings = json.load(file)
                    self.last_game = settings.get('last_game')
            except (json.JSONDecodeError, IOError):
                self.last_game = None

    def save_games_to_json(self):
        try:
            with open("games.json", "w") as file:
                json.dump(self.games, file, indent=4)
        except IOError as e:
            QMessageBox.warning(self, "Error", f"Failed to save games: {str(e)}")

    def populate_list_widget(self):
        self.list_widget.clear()
        self.time_labels.clear()
        items = [game for game in sorted(self.games, key=lambda k: self.games[k], reverse=True)]
        for game in items:
            item = QListWidgetItem()  # Создаем пустой элемент списка
            widget = QWidget()  # Создаем контейнер для строки
            layout = QHBoxLayout()  # Создаем горизонтальный layout
            
            # Создаем QLabel для названия игры
            game_label = QLabel(game)
            game_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            
            # Создаем QLabel для времени
            time_label = QLabel(self.format_time(self.games[game]))
            time_label.setStyleSheet("min-width: 100px; text-align: right;")
            time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Добавляем виджеты в layout
            layout.addWidget(game_label)
            layout.addWidget(time_label)
            layout.setContentsMargins(5, 0, 5, 0)  # Устанавливаем отступы
            
            # Устанавливаем layout в контейнер
            widget.setLayout(layout)
            
            # Настройка элемента списка
            item.setSizeHint(widget.sizeHint())
            
            # Добавляем элементы в список и словарь
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            self.time_labels[game] = time_label

    def select_game(self, item):
        """Handle game selection."""
        widget = self.list_widget.itemWidget(item)
        if widget:
            game_label = widget.layout().itemAt(0).widget()
            self.current_game = game_label.text()
            self.current_time = self.games.get(self.current_game, 0)
            
            # inicialization of time seesion if not inicialisiated
            if self.current_game not in self.session_times:
                self.session_times[self.current_game] = 0
                
            self.label_name.setText(f"{self.current_game}")
            self.update_timer_display()
            self.update_session_timer_display()  # update timer session
            self.start_button.setEnabled(True)
            self.remove_button.setEnabled(True)
            self.edit_button.setEnabled(True)

    def add_game(self):
        """Add a new game."""
        game_name, ok = QInputDialog.getText(self, "Add Game", "Enter game name:")
        if ok and game_name.strip():
            game_name = game_name.strip()
            if game_name in self.games:
                QMessageBox.warning(self, "Warning", "Game already exists.")
            else:
                self.games[game_name] = 0
                
                # Создаем новый элемент списка
                item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout()
                
                # Создаем QLabel для названия игры
                game_label = QLabel(game_name)
                game_label.setStyleSheet("font-size: 14px; font-weight: bold;")
                
                # Создаем QLabel для времени
                time_label = QLabel("0:00:00")
                time_label.setStyleSheet("min-width: 100px; text-align: right;")
                time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Собираем layout
                layout.addWidget(game_label)
                layout.addWidget(time_label)
                layout.setContentsMargins(5, 0, 5, 0)
                widget.setLayout(layout)
                
                item.setSizeHint(widget.sizeHint())
                
                # Добавляем элементы
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
                self.time_labels[game_name] = time_label
                
                self.save_games_to_json()
                self.select_game(item)
        else:
            QMessageBox.warning(self, "Warning", "Game name cannot be empty.")

    def remove_game(self):
        """Remove the selected game."""
        if self.current_game:
            confirm = QMessageBox.question(
                self, "Confirm Remove",
                f"Are you sure you want to remove {self.current_game}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                if self.current_game == self.last_game:
                    self.last_game = None  # Установить в None, если удаляемая игра была последней
                self.games.pop(self.current_game, None)  # remove game from list
                self.session_times.pop(self.current_game, None)  # remove time of this game
                self.populate_list_widget()
                self.save_games_to_json()
                self.reset_ui()  # reset ui
            if self.current_game in self.time_labels:
                del self.time_labels[self.current_game]

    def edit_time(self):
        """Edit the time for the selected game."""
        if self.current_game:
            new_time, ok = QInputDialog.getInt(self, "Edit Time", "Enter new time (seconds):", self.current_time, 0)
            if ok:
                self.games[self.current_game] = new_time
                self.current_time = new_time
                self.update_timer_display()
                self.save_games_to_json()
                if self.current_game in self.time_labels:
                    self.time_labels[self.current_game].setText(self.format_time(new_time))

    def start_timer(self):
        """Start the timer."""
        if self.current_game:
            self.last_game = self.current_game  # save curr game like a last
            self.saveLastGame()  # save last game to a file
            self.timer.start(1000)
            self.timer_running = True
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.add_button.setEnabled(False)
            self.remove_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.list_widget.setEnabled(False)
            self.timer_display.setStyleSheet("font-size: 96px; border: 5px solid #ff8728; padding: 10px;")

    def pause_timer(self):
        """Pause the timer."""
        self.timer.stop()
        self.timer_running = False
        self.games[self.current_game] = self.current_time
        self.save_games_to_json()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.add_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.edit_button.setEnabled(True)
        self.list_widget.setEnabled(True)
        self.timer_display.setStyleSheet("font-size: 96px; border: 5px solid #00000000; padding: 10px;")

    def update_time(self):
        self.current_time += 1
        self.session_times[self.current_game] += 1
        if not hasattr(self, 'save_counter'):
            self.save_counter = 0
        self.save_counter += 1
        if self.save_counter >= 10:
            self.save_counter = 0
            self.games[self.current_game] = self.current_time
            self.save_games_to_json()
        self.update_timer_display()
        self.update_session_timer_display()
        if self.current_game in self.time_labels:
            self.time_labels[self.current_game].setText(self.format_time(self.current_time))

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02}:{secs:02}"

    def update_timer_display(self):
        self.timer_display.setText(self.format_time(self.current_time))

    def update_session_timer_display(self):
        session_time = self.session_times.get(self.current_game, 0)
        self.session_timer_display.setText(f"Session: {self.format_time(session_time)}")

    def reset_ui(self):
        """Reset UI to the default state."""
        self.current_game = None
        self.current_time = 0
        self.timer.stop()
        self.timer_running = False
        self.label_name.setText("!!!pick a game!!!")
        self.timer_display.setText("0:00:00")
        self.session_timer_display.setText("Session: 0:00:00")  # reset timer session
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.list_widget.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameTimerApp()
    window.show()
    sys.exit(app.exec_())

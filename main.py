from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QCursor
import calendar
import sys
import json
from datetime import datetime
from pymysql import cursors, connect
from dotenv import dotenv_values
import qtawesome as qta

JAN = 1
FEB = 2
MAR = 3
APR = 4
MAY = 5
JUN = 6
JUL = 7
AUG = 8
SEP = 9
OCT = 10
NOV = 11
DEC = 12

cal = calendar.Calendar()
config = dotenv_values(".env")


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        self.days = []
        self.months = {
            "January":   1,
            "February":  2,
            "March":     3,
            "April":     4,
            "May":       5,
            "June":      6,
            "July":      7,
            "August":    8,
            "September": 9,
            "October":   10,
            "November":  11,
            "December":  12
        }
        self.year = 2021
        self.current_month = datetime.now().strftime('%B')
        self.month = self.months[self.current_month]

        self.windowControl = QFrame(self)
        self.windowControlLayout = QHBoxLayout(self)
        self.windowControl.setLayout(self.windowControlLayout)

        self.title = "Scheduler"
        self.menuBar = self.menuBar()
        self.statusBar = self.statusBar()
        self.statusBar.showMessage('Message in statusbar.')
        self.statusBar.setStyleSheet("color: #333333; font-size: 14px;")
        self.setStatusBar(self.statusBar)

        self.fileMenu = self.menuBar.addMenu('&File')
        self.newProjectAction = QAction('New Project...')
        self.newAction = QAction('&New...')
        self.openAction = QAction('&Open...')
        self.saveAction = QAction('&Save')
        self.saveAsAction = QAction('Save as...')
        self.printAction = QAction('&Print...')
        self.exitAction = QAction('Exit', self)

        self.editMenu = self.menuBar.addMenu('&Edit')

        self.formatMenu = self.menuBar.addMenu('Format')
        self.fontAction = QAction('Font...')

        self.close_btn = QPushButton(self.menuBar)
        self.max_btn = QPushButton(self.menuBar)
        self.min_btn = QPushButton(self.menuBar)

        self.oldPos = self.pos()
        self.screen = app.desktop()
        self.winX = int((self.screen.width() / 2) - (self.width() / 2))
        self.winY = int((self.screen.height() / 2) - (self.height() / 2))
        self.pressed = False

        self.mainLayout = QVBoxLayout(self)
        self.mainFrame = QFrame(self)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.mainFrame)
        self.setCentralWidget(self.mainFrame)
        self.calendarLayout = QVBoxLayout(self)
        self.mainFrame.setLayout(self.calendarLayout)
        self.calendar = QTableWidget(self)

        self.calendarLabel = QLabel("")

        self.fullScreen = False
        self.popup = None
        self.initUI()

    def initUI(self):
        self.setObjectName('MainWindow')
        self.setWindowTitle(self.title)
        self.resize(640, 480)
        self.setMouseTracking(True)

        self.setStyleSheet('background-color: #cccccc')

        self.menuBar.setStyleSheet('color: #333333; font-size: 20px;')

        self.newProjectAction.setShortcut('Ctrl+Shift+N')
        self.fileMenu.addAction(self.newProjectAction)

        self.newAction.setShortcut('Ctrl+N')
        self.fileMenu.addAction(self.newAction)

        self.openAction.setShortcut('Ctrl+O')
        self.fileMenu.addAction(self.openAction)

        self.fileMenu.addSeparator()

        self.saveAction.setShortcut('Ctrl+S')
        self.fileMenu.addAction(self.saveAction)

        self.saveAsAction.setShortcut('Ctrl+Shift+S')
        self.fileMenu.addAction(self.saveAsAction)

        self.printAction.setShortcut('Ctrl+P')
        self.fileMenu.addAction(self.printAction)

        self.fileMenu.addSeparator()

        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(qApp.quit)
        self.fileMenu.addAction(self.exitAction)

        self.menuBar.setCornerWidget(self.windowControl, Qt.TopRightCorner)
        self.windowControlLayout.addWidget(self.min_btn)
        self.windowControlLayout.addWidget(self.max_btn)
        self.windowControlLayout.addWidget(self.close_btn)

        self.min_btn.setStyleSheet("width: 30px; height:20px; border: none;")
        self.min_btn.setIcon(qta.icon('fa5s.window-minimize', color="#333333"))
        self.min_btn.setIconSize(QSize(20, 20))
        self.min_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.min_btn.clicked.connect(self.minButton)

        self.max_btn.setStyleSheet("width: 30px; height:20px; border: none;")
        self.max_btn.setIcon(qta.icon('fa5s.window-maximize', color="#333333"))
        self.max_btn.setIconSize(QSize(20, 20))
        self.max_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.max_btn.clicked.connect(self.maxButton)

        self.close_btn.setStyleSheet("width: 30px; height:20px; border: none;")
        self.close_btn.setIcon(qta.icon('fa5s.times', color="#333333"))
        self.close_btn.setIconSize(QSize(20, 20))
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.closeButton)

        monthSelect = QComboBox(self)
        for month in self.months.keys():
            monthSelect.addItem(month)

        monthSelect.activated[str].connect(self.onMonthChange)
        monthSelect.setStyleSheet('background-color: #ffffff; color: #333333; padding: 5px;')
        self.calendarLayout.addWidget(monthSelect)
        self.createCalendar()
        self.calendarLayout.addWidget(self.calendarLabel)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.move(self.winX, self.winY)

        self.show()

    @staticmethod
    def connectDB():
        return connect(host=config["MYSQL_HOST"],
                       user=config["MYSQL_USER"],
                       password=config["MYSQL_PASS"],
                       db=config["MYSQL_DB"],
                       charset='utf8mb4',
                       cursorclass=cursors.DictCursor)

    def get_num_events(self, day):
        connection = self.connectDB()
        events = []
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'''SELECT * FROM `events` WHERE month={self.month} AND day={day} AND year={self.year}''')
            events = cursor.fetchall()
        finally:
            connection.close()
            return len(events)

    def createCalendar(self):
        self.calendar.setRowCount(len(cal.monthdayscalendar(self.year, self.month)))
        self.calendar.horizontalHeader().setStretchLastSection(True)
        self.calendar.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar.setColumnCount(7)
        self.calendar.verticalHeader().setVisible(False)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.calendar.setHorizontalHeaderLabels(days)
        self.calendar.clicked.connect(self.showDay)

        for i, week in enumerate(cal.monthdayscalendar(self.year, self.month)):
            self.days.append([])
            for j, day in enumerate(week):
                self.days[i].append(Day(self.month, self.year, day, days[j]))

        for i, week in enumerate(self.days):
            monday_events = self.get_num_events(week[0])
            day_num = QLabel(f"{week[0]}")
            if monday_events > 0:
                if monday_events > 1:
                    monday = QLabel(f"{monday_events} events")
                else:
                    monday = QLabel(f"{monday_events} event")
            else:
                monday = QLabel("")
            monday.setStatusTip(week[0].toString())

            cell_layout = QVBoxLayout()
            cell_layout.addWidget(day_num)
            cell_layout.addWidget(monday)

            cellWidget = QWidget()
            cellWidget.setLayout(cell_layout)

            tuesday_events = self.get_num_events(week[1])
            day_num1 = QLabel(f"{week[1]}")
            if tuesday_events > 0:
                if tuesday_events > 1:
                    tuesday = QLabel(f"{tuesday_events} events")
                else:
                    tuesday = QLabel(f"{tuesday_events} event")
            else:
                tuesday = QLabel("")
            tuesday.setStatusTip(week[1].toString())

            cell_layout1 = QVBoxLayout()
            cell_layout1.addWidget(day_num1)
            cell_layout1.addWidget(tuesday)

            cellWidget1 = QWidget()
            cellWidget1.setLayout(cell_layout1)

            wednesday_events = self.get_num_events(week[2])
            day_num2 = QLabel(f"{week[2]}")
            if wednesday_events > 0:
                if wednesday_events > 1:
                    wednesday = QLabel(f"{wednesday_events} events")
                else:
                    wednesday = QLabel(f"{wednesday_events} event")
            else:
                wednesday = QLabel("")
            wednesday.setStatusTip(week[2].toString())

            cell_layout2 = QVBoxLayout()
            cell_layout2.addWidget(day_num2)
            cell_layout2.addWidget(wednesday)

            cellWidget2 = QWidget()
            cellWidget2.setLayout(cell_layout2)

            thursday_events = self.get_num_events(week[3])
            day_num3 = QLabel(f"{week[3]}")
            if thursday_events > 0:
                if thursday_events > 1:
                    thursday = QLabel(f"{thursday_events} events")
                else:
                    thursday = QLabel(f"{thursday_events} event")
            else:
                thursday = QLabel("")
            thursday.setStatusTip(week[3].toString())

            cell_layout3 = QVBoxLayout()
            cell_layout3.addWidget(day_num3)
            cell_layout3.addWidget(thursday)

            cellWidget3 = QWidget()
            cellWidget3.setLayout(cell_layout3)

            friday_events = self.get_num_events(week[4])
            day_num4 = QLabel(f"{week[4]}")
            if friday_events > 0:
                if friday_events > 1:
                    friday = QLabel(f"{friday_events} events")
                else:
                    friday = QLabel(f"{friday_events} event")
            else:
                friday = QLabel("")
            friday.setStatusTip(week[4].toString())

            cell_layout4 = QVBoxLayout()
            cell_layout4.addWidget(day_num4)
            cell_layout4.addWidget(friday)

            cellWidget4 = QWidget()
            cellWidget4.setLayout(cell_layout4)

            saturday_events = self.get_num_events(week[5])
            day_num5 = QLabel(f"{week[5]}")
            if saturday_events > 0:
                if saturday_events > 1:
                    saturday = QLabel(f"{saturday_events} events")
                else:
                    saturday = QLabel(f"{saturday_events} event")
            else:
                saturday = QLabel("")
            saturday.setStatusTip(week[5].toString())

            cell_layout5 = QVBoxLayout()
            cell_layout5.addWidget(day_num5)
            cell_layout5.addWidget(saturday)

            cellWidget5 = QWidget()
            cellWidget5.setLayout(cell_layout5)

            sunday_events = self.get_num_events(week[6])
            day_num6 = QLabel(f"{week[6]}")
            if sunday_events > 0:
                if sunday_events > 1:
                    sunday = QLabel(f"{sunday_events} events")
                else:
                    sunday = QLabel(f"{sunday_events} event")
            else:
                sunday = QLabel("")
            sunday.setStatusTip(week[6].toString())

            cell_layout6 = QVBoxLayout()
            cell_layout6.addWidget(day_num6)
            cell_layout6.addWidget(sunday)

            cellWidget6 = QWidget()
            cellWidget6.setLayout(cell_layout6)

            self.calendar.setCellWidget(i, 0, cellWidget)
            self.calendar.setCellWidget(i, 1, cellWidget1)
            self.calendar.setCellWidget(i, 2, cellWidget2)
            self.calendar.setCellWidget(i, 3, cellWidget3)
            self.calendar.setCellWidget(i, 4, cellWidget4)
            self.calendar.setCellWidget(i, 5, cellWidget5)
            self.calendar.setCellWidget(i, 6, cellWidget6)

        self.calendarLayout.addWidget(self.calendar)

    def showDay(self, cell):
        self.popup = DayView(self.days[cell.row()][cell.column()])

    def onMonthChange(self, text):
        self.month = self.months[text]
        self.days = []
        self.createCalendar()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()
        self.pressed = True

    def mouseReleaseEvent(self, event):
        self.oldPos = event.globalPos()
        self.pressed = False

    def mouseMoveEvent(self, event):
        if self.pressed:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    @pyqtSlot()
    def minButton(self):
        self.showMinimized()

    @pyqtSlot()
    def maxButton(self):
        if self.fullScreen:
            self.winX = int((self.screen.size().width() / 2) - (640 / 2))
            self.winY = int((self.screen.size().height() / 2) - (480 / 2))
            self.setGeometry(self.winX, self.winY, 640, 480)
            self.fullScreen = False

        else:
            self.setGeometry(0, 0, self.screen.size().width(), self.screen.size().height())
            self.fullScreen = True

    @pyqtSlot()
    def closeButton(self):
        sys.exit()


class DayView(QWidget):
    def __init__(self, day):
        QWidget.__init__(self)
        self.day = day
        self.eventName = ""
        self.startHourValue = ""
        self.startMinValue = ""
        self.startAmPmValue = ""
        self.endHourValue = ""
        self.endMinValue = ""
        self.endAmPmValue = ""
        self.setGeometry(QRect(100, 100, 600, 600))
        layout = QFormLayout(self)

        self.dayLabel = QLabel(self.day.toString())
        self.dayLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: #333333;")
        layout.addRow(self.dayLabel)

        self.eventNameInput = QLineEdit(self)
        self.eventNameInput.textChanged.connect(self.onEventNameChange)
        self.eventNameInput.setPlaceholderText('Event Name')
        self.eventNameInput.setStyleSheet('background-color: #ffffff; color: #333333; padding: 5px;')
        layout.addRow(self.eventNameInput)

        eventTimeLayout = QHBoxLayout(self)

        startLabel = QLabel("Start Time:")
        startLabel.setStyleSheet("width: 100px; padding-left: 50px;")
        self.startHour = QComboBox(self)
        for hr in range(1, 13):
            if len(str(hr)) > 1:
                self.startHour.addItem(str(hr))
            else:
                self.startHour.addItem(f"0{hr}")
        self.startHour.activated[str].connect(self.onStartHourChange)

        self.startMin = QComboBox(self)
        for minute in range(0, 60, 5):
            if len(str(minute)) > 1:
                self.startMin.addItem(str(minute))
            else:
                self.startMin.addItem(f"0{minute}")
        self.startMin.activated[str].connect(self.onStartMinChange)

        self.startAmPm = QComboBox(self)
        self.startAmPm.addItem("AM")
        self.startAmPm.addItem("PM")
        self.startAmPm.activated[str].connect(self.onStartAmPmChange)

        startLayout = QHBoxLayout(self)
        startLayout.addWidget(self.startHour)
        startLayout.addWidget(self.startMin)
        startLayout.addWidget(self.startAmPm)
        eventTimeLayout.addWidget(startLabel)
        eventTimeLayout.addItem(startLayout)

        endLabel = QLabel("End Time:")
        endLabel.setStyleSheet("width: 100px; padding-left: 50px;")
        self.endHour = QComboBox(self)

        for hr in range(1, 13):
            if len(str(hr)) > 1:
                self.endHour.addItem(str(hr))
            else:
                self.endHour.addItem(f"0{hr}")
        self.endHour.activated[str].connect(self.onEndHourChange)

        self.endMin = QComboBox(self)
        for minute in range(0, 60, 5):
            if len(str(minute)) > 1:
                self.endMin.addItem(str(minute))
            else:
                self.endMin.addItem(f"0{minute}")
        self.endMin.activated[str].connect(self.onEndMinChange)

        self.endAmPm = QComboBox(self)
        self.endAmPm.addItem("AM")
        self.endAmPm.addItem("PM")
        self.endAmPm.activated[str].connect(self.onEndAmPmChange)

        endLayout = QHBoxLayout(self)
        endLayout.addWidget(self.endHour)
        endLayout.addWidget(self.endMin)
        endLayout.addWidget(self.endAmPm)
        eventTimeLayout.addWidget(endLabel)
        eventTimeLayout.addItem(endLayout)

        layout.addRow(eventTimeLayout)

        self.addEventBtn = QPushButton("Add")
        self.addEventBtn.clicked.connect(self.onAddEvent)
        self.addEventBtn.setStyleSheet('padding: 5px; background-color: #666666; color: #cccccc;')
        layout.addRow(self.addEventBtn)

        self.calendar = QTableWidget(self)
        self.calendar.setRowCount(24)

        self.calendar.setColumnCount(2)
        self.calendar.verticalHeader().setVisible(False)
        self.calendar.setHorizontalHeaderLabels(["Time", "Event"])
        header = self.calendar.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.calendar.clicked.connect(self.showSlot)
        times = ["12:00 AM",
                 "1:00 AM",
                 "2:00 AM",
                 "3:00 AM",
                 "4:00 AM",
                 "5:00 AM",
                 "6:00 AM",
                 "7:00 AM",
                 "8:00 AM",
                 "9:00 AM",
                 "10:00 AM",
                 "11:00 AM",
                 "12:00 PM",
                 "1:00 PM",
                 "2:00 PM",
                 "3:00 PM",
                 "4:00 PM",
                 "5:00 PM",
                 "6:00 PM",
                 "7:00 PM",
                 "8:00 PM",
                 "9:00 PM",
                 "10:00 PM",
                 "11:00 PM"]
        for i, time_slot in enumerate(times):
            self.calendar.setItem(i, 0, QTableWidgetItem(time_slot))

        connection = self.connectDB()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'''SELECT * FROM `events` WHERE month={self.day.month} AND day={self.day.dom} AND year={self.day.year} ORDER BY id DESC''')
            events = cursor.fetchall()
            for event in events:

                if event["start_ampm"] == "AM":
                    row = int(event["start_hour"])+1
                    cell_data = QLabel(f"{event['start_hour']}:{event['start_min']} {event['start_ampm']} {event['event_name']}")

                else:
                    row = int(event["start_hour"])+12
                    cell_data = QLabel(f"{event['start_hour']}:{event['start_min']} {event['start_ampm']} {event['event_name']}")

                cell_layout = QVBoxLayout()
                cell_layout.addWidget(cell_data)

                cellWidget = QWidget()
                cellWidget.setLayout(cell_layout)
                self.calendar.setCellWidget(row, 1, cellWidget)

        finally:
            connection.close()

        layout.addRow(self.calendar)
        self.setLayout(layout)

        self.init()

    def init(self):
        self.show()

    @staticmethod
    def connectDB():
        return connect(host=config["MYSQL_HOST"],
                       user=config["MYSQL_USER"],
                       password=config["MYSQL_PASS"],
                       db=config["MYSQL_DB"],
                       charset='utf8mb4',
                       cursorclass=cursors.DictCursor)

    def onStartHourChange(self, text):
        self.startHourValue = text

    def onStartMinChange(self, text):
        self.startMinValue = text

    def onStartAmPmChange(self, text):
        self.startAmPmValue = text

    def onEndHourChange(self, text):
        self.endHourValue = text

    def onEndMinChange(self, text):
        self.endMinValue = text

    def onEndAmPmChange(self, text):
        self.endAmPmValue = text

    def showSlot(self, cell):
        print(cell.row())

    def onAddEvent(self):
        connection = self.connectDB()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''INSERT INTO `events` 
                               (event_name, start_hour, start_min, start_ampm, end_hour, end_min, end_ampm, month, day, year, date_passed, date_set) 
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                               (self.eventName, self.startHourValue, self.startMinValue, self.startAmPmValue, self.endHourValue, self.endMinValue, self.endAmPmValue, self.day.month, self.day.dom, self.day.year, False, datetime.utcnow()))
        except Exception as e:
            print(e)
        finally:
            connection.close()

    def onEventNameChange(self, text):
        self.eventName = text


class Day:
    def __init__(self, month, year, dom, dow):
        self.month  = month
        self.year   = year
        self.dom    = dom
        self.dow    = dow
        self.events = []
        self.months = {
            "January":   1,
            "February":  2,
            "March":     3,
            "April":     4,
            "May":       5,
            "June":      6,
            "July":      7,
            "August":    8,
            "September": 9,
            "October":   10,
            "November":  11,
            "December":  12
        }

    def __str__(self):
        if self.dom == 0:
            return " "
        return str(self.dom)

    def __call__(self):
        return self.events

    def toString(self):
        return f"{self.dow}. {list(self.months.keys())[self.month-1]} {self.dom}, {self.year}"

    def addEvent(self, event, time_slot):
        self.events.append(Event(event, time_slot))


class Event:
    def __init__(self, event, time_slot):
        self.event     = event
        self.time_slot = time_slot


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = App()
    sys.exit(app.exec_())

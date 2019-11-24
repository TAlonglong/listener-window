import sys

from queue import Empty
from multiprocessing import Process, Queue
import threading

from posttroll.listener import ListenerContainer, Listener
import posttroll

from PySide2.QtWidgets import QApplication, QSizePolicy
from PySide2.QtWidgets import (QAction, QAbstractItemView, qApp, QDataWidgetMapper, QHeaderView, QMainWindow, QMessageBox, QWidget, QGroupBox, QTableView, QVBoxLayout, QMenu, QAction)
from PySide2.QtGui import QKeySequence, QStandardItemModel, QStandardItem, QColor, QCursor
from PySide2.QtCore import QStringListModel, QObject, QThread, Signal, Slot

class mainWindow(QMainWindow):
    """A main window"""

    def __init__(self):
        QMainWindow.__init__(self)

        self._queue = Queue()
        config = {'subscribe-topic': '/'}
        self.listener = FileListener(self._queue, config, "command")
        self.listener.start()

        #self.thread = QThread(self)
        config_item = 'section on old config stash'
        self.message_handler = MessageHandler(config, config_item, self._queue)
        self.message_handler.over.connect(self.on_over)
        self.message_handler.start()

        self.setWindowTitle("Hello")
        self.centralWidget = QWidget(self)
        self.centralWidget.setObjectName("centralWidget")

        self.liste = QTableView(self.centralWidget)
        self.liste.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.liste.setObjectName("liste")
        self.liste.resize(self.centralWidget.size())
        self.liste.setAlternatingRowColors(True)

        self.model = QStandardItemModel(0,7)
        self.model.setHorizontalHeaderLabels(['Subject', 'Type', 'Sender', 'Time', 'Binary', 'Version', 'data'])
        
        # Set the model
        self.liste.setModel(self.model)

        self.liste.setSortingEnabled(True)

        self.setCentralWidget(self.centralWidget)

    def create_menubar(self):
        file_menu = self.menuBar().addMenu(self.tr("&File"))
        quit_action = file_menu.addAction(self.tr("&Quit"))
        quit_action.triggered.connect(self.message_handler.receive_quit)
        quit_action.triggered.connect(self.listener.receive_quit)
        quit_action.triggered.connect(qApp.quit)
        
        help_menu = self.menuBar().addMenu(self.tr("&Help"))
        about_action = help_menu.addAction(self.tr("&About"))
        about_action.setShortcut(QKeySequence.HelpContents)
        about_action.triggered.connect(self.about)
        aboutQt_action = help_menu.addAction("&About Qt")
        aboutQt_action.triggered.connect(qApp.aboutQt)

        
        #print(QColor.colorNames())

    def about(self):
        QMessageBox.about(self, self.tr("About Books"),
            self.tr("<p>main window with more"))

    @Slot(object)
    def on_over(self, value):
        #print('In slot', value)
        self.model.appendRow([QStandardItem(str(value.subject)),
                              QStandardItem(str(value.type)),
                              QStandardItem(str(value.sender)),
                              QStandardItem(str(value.time)),
                              QStandardItem(str(value.binary)),
                              QStandardItem(str(value.version)),
                              QStandardItem(str(value.data))])
        self.liste.resizeColumnsToContents()
        #self.liste.selectRow(self.model.rowCount() - 1)
        self.liste.scrollToBottom()

    def resizeEvent(self, re):
        self.liste.resize(self.centralWidget.size())
        self.centralWidget.resizeEvent(re)

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.renameAction = QAction('Rename', self)
        self.renameAction.triggered.connect(self.renameSlot(event))
        self.menu.addAction(self.renameAction)
        # add other required actions
        self.menu.popup(QCursor.pos())
        print("HER")

    def renameSlot(self, event):
        print("renaming slot called", event)
        # get the selected row and column
        row = self.liste.rowAt(event.pos().y())
        col = self.liste.columnAt(event.pos().x())
        print(col,row)
        # get the selected cell
        #cell = self.liste.item(row, col)
        # get the text inside selected cell (if any)
        #cellText = cell.text()
        # get the widget inside selected cell (if any)
        #widget = self.liste.cellWidget(row, col)


class MessageHandler(QThread):
    over = Signal(object)

    """Listen for all messages and process them.
    """

    def __init__(self, config, section, _queue):
        super().__init__()
        self._config = config
        self._queue = _queue

        try:
            self.providing_server = config.get(section,'providing-server')
        except:
            self.providing_server = None

        print("Message handler init complete")

    def run(self):
        """Run MessageHandler"""
        print("Start in run")
        self._loop = True
        while self._loop:
            # Check queue for new messages
            msg = None
            try:
                #print("Message Handler")
                msg = self._queue.get(True, 1)
                #print("HER:",msg)
            except KeyboardInterrupt:
                self.stop()
                continue
            except Empty:
                continue

            try:
                _msg = msg['msg']
            except TypeError:
                break

            #print(str(_msg))
            self.over.emit(_msg)

    def stop(self):
        """Stop MessageHandler."""
        print("Stopping MessageHandler.")
        self._loop = False

    def process(self, msg):
        """Process message"""
        return

    @Slot(object)
    def receive_quit(self):
        self.stop()

        
class FileListener(threading.Thread):

    def __init__(self, queue, config, command_name):
        threading.Thread.__init__(self)

        
        self.loop = True
        self.queue = queue
        self.config = config
        self.subscr = None
        self.command_name = command_name

    def stop(self):
        """Stops the file listener"""
        print("Entering stop in FileListener ...")
        self.loop = False
        self.queue.put(None)

    @Slot(object)
    def receive_quit(self):
        self.stop()

    def run(self):
        print("Entering run in FileListener ...")
        if type(self.config["subscribe-topic"]) not in (tuple, list, set):
            self.config["subscribe-topic"] = [self.config["subscribe-topic"]]
        try:
            if 'services' not in self.config:
                self.config['services'] = ''
            with posttroll.subscriber.Subscribe(self.config['services'], self.config['subscribe-topic'],
                                                True) as subscr:

                print("Entering for loop subscr.recv")
                for msg in subscr.recv(timeout=1):
                    if not self.loop:
                        # LOGGER.debug("Self.loop false in FileListener {}".format(self.loop))
                        break
                    #print("Message = " + str(msg))
                    if msg is None:
                        continue 
                    if msg.type in ['beat', 'info']:
                        continue
                    print("Put the message on the queue...")                    
                    msg_data = {}
                    msg_data['config'] = self.config
                    msg_data['msg'] = msg
                    msg_data['command_name'] = self.command_name
                    self.queue.put(msg_data)
                    #print("After queue put.")

        except KeyError as ke:
            print("Some key error. probably in config:", ke)
            raise
        except KeyboardInterrupt:
            print("Received keyboard interrupt. Shutting down.")
            raise

        
if __name__ == "__main__":
    app = QApplication([])
    
    window = mainWindow()
    window.create_menubar()
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec_())

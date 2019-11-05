import sys

from queue import Empty
from multiprocessing import Process, Queue
import threading

from posttroll.listener import ListenerContainer, Listener
import posttroll

from PySide2.QtWidgets import QApplication, QSizePolicy
from PySide2.QtWidgets import (QAction, QAbstractItemView, qApp, QDataWidgetMapper, QHeaderView, QMainWindow, QMessageBox, QWidget, QGroupBox, QTableView, QVBoxLayout)
from PySide2.QtGui import QKeySequence, QStandardItemModel, QStandardItem
from PySide2.QtCore import QStringListModel, QObject, QThread, Signal, Slot

class mainWindow(QMainWindow):
    """A main window"""

    def __init__(self):
        QMainWindow.__init__(self)

        self._queue = Queue()
        config = {'subscribe-topic': '/'}
        listener = FileListener(self._queue, config, "command")
        listener.start()

        #self.thread = QThread(self)
        config_item = 'section on old config stash'
        self.message_handler = MessageHandler(config, config_item, self._queue)
        #self.message_handler.moveToThread(self.thread)
        self.message_handler.over.connect(self.on_over)
        self.message_handler.start()

        
        #self.message_handler.start()

        self.setWindowTitle("Hello")
        self.centralWidget = QWidget(self)
        self.centralWidget.setObjectName("centralWidget")
        ###self.centralWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.centralWidget.resize(600, 600)
        #self.centralWidget.setBaseSize(600, 600)
         #self.groupBox = QGroupBox(self.centralWidget)
        #self.groupBox.setTitle("GroupBox")
        #self.groupBox.setObjectName("groupBox")

        #self.vboxlayout1 = QVBoxLayout(self.groupBox)
        #self.vboxlayout1.setSpacing(6)
        #self.vboxlayout1.setContentsMargins(9, 9, 9, 9)
        #self.vboxlayout1.setObjectName("vboxlayout1")

        #self.liste = QTableView(self.groupBox)
        self.liste = QTableView(self.centralWidget)
        self.liste.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.liste.setObjectName("liste")
        self.liste.resize(800,600)
        self.liste.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)        #self.vboxlayout1.addWidget(self.liste)

        #self.model = QStringListModel(self.liste)
        self.model = QStandardItemModel(0,4)
        self.model.setHorizontalHeaderLabels(['Subject', 'data'])
        #self.model.setHorizontalHeader("test")
        
        #self.model.setStringList(self.content)
        self.model.appendRow([QStandardItem("første"),QStandardItem("første1"),QStandardItem("første2")])

        # Set the model
        self.liste.setModel(self.model)

        self.setCentralWidget(self.centralWidget)

        #Need to connect the append_content when new message arrives
        #new_message.triggered.connect(append_content())

    def create_menubar(self):
        file_menu = self.menuBar().addMenu(self.tr("&File"))
        quit_action = file_menu.addAction(self.tr("&Quit"))
        quit_action.triggered.connect(qApp.quit)

        help_menu = self.menuBar().addMenu(self.tr("&Help"))
        about_action = help_menu.addAction(self.tr("&About"))
        about_action.setShortcut(QKeySequence.HelpContents)
        about_action.triggered.connect(self.about)
        aboutQt_action = help_menu.addAction("&About Qt")
        aboutQt_action.triggered.connect(qApp.aboutQt)

    def about(self):
        QMessageBox.about(self, self.tr("About Books"),
            self.tr("<p>main window with more"))

    @Slot(object)
    def on_over(self, value):
        print('In slot', value)
        #self.content.append(value.subject)        
        #self.model.setStringList(self.content)
        self.model.appendRow([QStandardItem(str(value.subject)), QStandardItem(str(value.data))])

def read_from_queue(queue):
    #read from queue
    while True:
        print("Start waiting for new message in queue qith queue size: {}".format(queue.qsize()))
        msg = queue.get()
        print("Got new message. Queue size is now: {}".format(queue.qsize()))
        _msg = msg['msg']
        print("Data   : {}".format(_msg.data))
        print("Subject: {}".format(_msg.subject))
        print("Type   : {}".format(_msg.type))
        print("Sender : {}".format(_msg.sender))
        print("Time   : {}".format(_msg.time))
        print("Binary : {}".format(_msg.binary))
        print("Version: {}".format(_msg.version))

class MessageHandler(QThread):
    over = Signal(object)

    """Listen for all messages and process them.
    """

    def __init__(self, config, section, _queue):
        super().__init__()
        #Process.__init__(self)
        self._config = config
        #self._section = section
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
                print("Message Handler")
                msg = self._queue.get(True, 1)
                print("HER:",msg)
            except KeyboardInterrupt:
                self.stop()
                continue
            except Empty:
                continue

            _msg = msg['msg']
            #if self.providing_server and self.providing_server not in _msg.host:
            #    continue

            print(str(_msg))
            self.over.emit(_msg)

    def stop(self):
        """Stop MessageHandler."""
        #self.logger.info("Stopping MessageHandler.")
        print("Stopping MessageHandler.")
        self._loop = False

    def process(self, msg):
        """Process message"""
        return

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
                    print("Message = " + str(msg))
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
                    print("After queue put.")

        except KeyError as ke:
            print("Some key error. probably in config:", ke)
            raise
        except KeyboardInterrupt:
            print("Received keyboard interrupt. Shutting down.")
            raise
                   
def write_to_queue(msg, meta, _queue):
    #Write to queue
    #print "WRITE TO QUEUE"
    print("Before write", _queue.qsize())
    #msg.data['db_database'] = meta['db_database']
    #msg.data['db_passwd'] = meta['db_passwd']
    #msg.data['db_user'] = meta['db_user']
    #msg.data['db_host'] = meta['db_host']
    _queue.put(msg)
    print("After write", _queue.qsize())

        
if __name__ == "__main__":
    app = QApplication([])

    #_queue = Queue()

    #queue_handler = Process(target=read_from_queue, args=(_queue,))
    #queue_handler.daemon = True
    #queue_handler.start()

    #config = {'subscribe-topic': '/'}
    #listener = FileListener(_queue, config, "command")
    #listener.start()
    
    #config_item = 'section on old config stash'
    #message_handler = MessageHandler(config, config_item, _queue)
    #message_handler.daemon = True
    #message_handler.set_logger(logger)
    #message_handler.run()
    #message_handler.start()

    
    window = mainWindow()
    window.create_menubar()
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec_())

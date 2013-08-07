#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python

"""

    \mainpage Snapshoter
    
    Snapshoter allow to take full screen snapshot each give number of sec and
    storing it to an image file.
    
    
    \section Infos
    
    Written by fbianco aka François Bianco, University of Geneva -
    francois.bianco@unige.ch
    
    
    \section Copyright

    Copyright © 2009 fbianco aka François Bianco, University of Geneva -
                     francois.bianco@unige.ch
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


    \section Updates
    
    2013-08-07:
        v.1.1 : fbianco : added continue on errors
    2009-04-30
        v.1.0 : fbianco : First version
    
"""

import sys, os
from PyQt4 import Qt

DEBUG = False

def _tr(s):
    """ Allow to implement a translation mechanism """
    return s
    
    
class SnapshoterWindow(Qt.QMainWindow) :
    """ Snapshoter construct a widget with all configuration options and define
        the main function of this application. """
    
    def __init__(self, application = None, *args) :
        """ Constructor : Application argument is used for connecting the
            quitAction to the quit slot of the application."""
    
        Qt.QMainWindow.__init__( self, *args )
    
        self.setWindowTitle( _tr('Snapshoter') )
        self.setWindowIcon( Qt.QIcon('img/icon.svg') )
    
        # store the application for the quit action
        self.application = application
    
        # store the timer reference for stopping it
        self.timer = None
    
        widget = Qt.QWidget( self )
        layout = Qt.QFormLayout()
        widget.setLayout( layout )
        self.setCentralWidget( widget )
    
        self.startButton = Qt.QPushButton( Qt.QIcon( 'img/start.svg' ),
                                          _tr('Start') )
        self.startButton.setCheckable( True )
        Qt.QObject.connect( self.startButton, Qt.SIGNAL("clicked()"),
                            self.toggleSnapshoter )
    
        self.intervalSpinBox = Qt.QDoubleSpinBox()
        self.intervalSpinBox.setSuffix( _tr(' s') )
        self.intervalSpinBox.setMinimum( 1 )
        self.intervalSpinBox.setDecimals( 0 )
    
        self.snapshotName = Qt.QLineEdit()
        self.changeSnapshotNameButton = Qt.QPushButton(
                    Qt.QIcon('img/saveAs.svg'), _tr('Select file') )
        Qt.QObject.connect( self.changeSnapshotNameButton,
                            Qt.SIGNAL("clicked()"), self.selectFile )
    
        self.autoStart = Qt.QCheckBox()
        self.continueOnError = Qt.QCheckBox()
    
        layout.addRow(_tr("Start/Stop"), self.startButton)
        separator = Qt.QFrame()
        separator.setFrameStyle(Qt.QFrame.HLine)
        layout.addRow(separator)
        layout.addRow(_tr('Snapshots interval'), self.intervalSpinBox)
        layout.addRow(_tr('Save path'), self.snapshotName)
        layout.addRow(_tr('Change path'), self.changeSnapshotNameButton)
        layout.addRow(_tr('Autostart'), self.autoStart )
        layout.addRow(_tr('Continue on error'), self.continueOnError)
    
        self.createActions()
        self.createTrayIcon()
        self.getScreenGeometry()
        self.readSettings()
    
    
    def selectFile( self ):
        """ Open a file dialog to let the user choose its snapshot file. """
    
        fileName = Qt.QFileDialog.getSaveFileName(self,
                    _tr("Snapshot file"),self.snapshotName.text(),
                    _tr("Images (*.png *.xpm *.jpg)"))
        if fileName :
            self.snapshotName.setText(fileName)
            if DEBUG : print "Snapshot file changed to %s. " % fileName
    
    
    def createActions( self ):
        """ Create the widget's actions """
    
        self.quitAction = Qt.QAction(_tr("&Quit"), self)
        self.quitAction.setIcon(Qt.QIcon('img/quit.svg'))
        Qt.QObject.connect(self.quitAction,
            Qt.SIGNAL("triggered()"), self.writeSettings )
        Qt.QObject.connect(self.quitAction,
            Qt.SIGNAL("triggered()"), self.application, Qt.SLOT("quit()") )
    
        self.toggleVisibilityAction = Qt.QAction(_tr("Reduce"),self)
        self.toggleVisibilityAction.setIcon(Qt.QIcon('img/reduce.svg'))
        Qt.QObject.connect(self.toggleVisibilityAction,
                           Qt.SIGNAL("triggered()"), self.toggleVisibility)
    
    
    def getScreenGeometry( self ):
        """ Construct a rectangle containing all the screens active on the
            desktop. """
    
        desktop = Qt.QApplication.desktop()
    
        # rectangle top left corner coordinates (x,y), width (w) and height (h).
        x,y,w,h = 0,0,0,0
        for i in range(desktop.numScreens()):
            geometry = desktop.screenGeometry(i)
            x=min(geometry.x(),x)
            y=min(geometry.y(),y)
            w=max(geometry.x()+geometry.width(),w)
            h=max(geometry.y()+geometry.height(),h)
    
        if DEBUG : print "Screen geometry : (%i,%i,%i,%i)" % (x,y,w,h)
    
        self.screenGeometry = (x,y,w,h)
    
    
    def readSettings(self):
        """ Read the stored settings. """
    
        settings = Qt.QSettings( "snapshotTaker", "pref" )
        self.intervalSpinBox.setValue( settings.value(
            "interval", Qt.QVariant("1")).toInt()[0] )
        self.snapshotName.setText( settings.value(
            "snapshotName", Qt.QVariant(Qt.QDir.home().path()) ).toString() )
    
        self.restoreGeometry( settings.value( "geometry" ).toByteArray() )
        self.continueOnError.setChecked( settings.value( "continueOnError",
                                    Qt.QVariant('False')).toBool())
        
        autoStart = settings.value(
            "autoStart", Qt.QVariant('False')).toBool()
        self.autoStart.setChecked( autoStart )
        if autoStart :
            self.startButton.setChecked( True )
            self.toggleSnapshoter()
    
    
    def writeSettings(self):
        """ Store the settings. """
    
        settings = Qt.QSettings( "snapshotTaker", "pref" )
        settings.setValue("interval", Qt.QVariant(self.intervalSpinBox.value()))
        settings.setValue("snapshotName", Qt.QVariant(self.snapshotName.text()))
        settings.setValue("autoStart", Qt.QVariant(self.autoStart.isChecked()))
        settings.setValue("continueOnError", Qt.QVariant(
                                            self.continueOnError.isChecked()))
        settings.setValue("geometry", Qt.QVariant(self.saveGeometry()) )
    
    
    def createTrayIcon(self):
        """ Create a system tray icon and a related context menu."""
    
        self.trayIconMenu = Qt.QMenu(self)
        self.trayIconMenu.addAction(self.toggleVisibilityAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
    
        self.trayIcon = Qt.QSystemTrayIcon(Qt.QIcon('img/icon.svg'),self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.show()
    
        Qt.QObject.connect(self.trayIcon,
            Qt.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"),
                       self.toggleVisibility )
    
    
    def toggleVisibility(self, reason = None):
        """ Show or hide the window, except if the activation reason (form the
            tray icon) required the context menu. """
    
        # If the activation is a right click on the icon ignore it
        if reason == Qt.QSystemTrayIcon.Context:
            return
    
        if self.isVisible():
            self.toggleVisibilityAction.setText( _tr("Restore") )
            self.toggleVisibilityAction.setIcon( Qt.QIcon('img/restore.svg') )
        else:
            self.toggleVisibilityAction.setText( _tr("Reduce") )
            self.toggleVisibilityAction.setIcon( Qt.QIcon('img/reduce.svg') )
    
        self.setVisible( not self.isVisible() )
    
        if DEBUG : print "Windows visibility to %s." % self.isVisible()
    
    
    def closeEvent(self, event):
        """ Reimplement the close event (like click on the 'x' on the window
            decoration)."""
    
        self.toggleVisibility()
        event.ignore()
    
    
    def toggleSnapshoter(self):
        """ Start/Stop the snapshoter timer. """
        if self.startButton.isChecked() :
            self.startButton.setIcon( Qt.QIcon('img/stop.svg') )
            self.startButton.setText( _tr('Stop') )
            self.timer = self.startTimer(
                self.intervalSpinBox.value() * 1000 ) # convert seconds to ms
            self.timerEvent() # take the first picture
            if DEBUG: print "Started each %i seconds." \
                                % self.intervalSpinBox.value()
        else :
            self.startButton.setIcon( Qt.QIcon('img/start.svg') )
            self.startButton.setText( _tr('Start') )
            self.killTimer(self.timer)
            if DEBUG: print "Stopped"
    
    
    def timerEvent(self, event = None):
        """ Take a snapshot at each timer tick, and handle possible errors."""
    
        ok = Qt.QPixmap.grabWindow(
            Qt.QApplication.desktop().winId(), # window system identifier
            self.screenGeometry[0],self.screenGeometry[1],
            self.screenGeometry[2],self.screenGeometry[3]
                ).save(self.snapshotName.text()) # return true if save was ok.
    
        if DEBUG: print "Try to save snapshot to %s. Result %s" \
                            % (self.snapshotName.text(),ok)
    
        if not ok and not self.continueOnError.isChecked() :
            self.trayIcon.showMessage ( _tr('Error'),
                    _tr('The snapshot cannot be saved under %s.\n' \
                        'Snapshoter will be stopped.') \
                        % self.snapshotName.text(), Qt.QSystemTrayIcon.Critical)
            self.startButton.setChecked( False )
            self.toggleSnapshoter()

        elif not ok:
           self.trayIcon.showMessage ( _tr('Error'),
                 _tr('The snapshot cannot be saved under %s.') \
                      % self.snapshotName.text(),
                 Qt.QSystemTrayIcon.Warning)


# Only start an application if we are __main__
if __name__ == '__main__':
    
    app = Qt.QApplication(sys.argv)
    Qt.QObject.connect( app, Qt.SIGNAL("lastWindowClosed()"), app,
Qt.SLOT("quit()") )
    mainWindow = SnapshoterWindow( app )
    mainWindow.show()
    sys.exit( app.exec_() )

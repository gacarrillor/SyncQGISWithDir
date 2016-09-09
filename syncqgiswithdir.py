# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SyncQGISWithDir
                                 A QGIS plugin
 Lets you know when new layers are available in a directory, so that you can load them to QGIS 
                              -------------------
        begin                : 2012-10-06
        copyright            : (C) 2012 by German Carrillo
        email                : geotux_tuxfamily@linuxmail.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.gui import QgsMessageBar
from qgis.core import *

import glob
import os

# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from syncqgiswithdirdialog import SyncQGISWithDirDialog

DEBUG = False


class SyncQGISWithDir:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # Create the dialog and keep reference
        self.dlg = SyncQGISWithDirDialog(self.iface.mainWindow())
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/syncqgiswithdir"
        # initialize locale
        localePath = ""
        locale = str(QSettings().value("locale/userLocale"))[0:2]
       
        if QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/syncqgiswithdir_" + locale + ".qm"

        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
   
        self.loadFormats()
        self.dictExt = {}            # {".shp":"v",...}
        self.filesFoundLastTime = {} # {'/data/a.shp':'v', '/data/b.tif':'r'}
        self.newFiles = {}           # {'/data/a.shp':'v', '/data/b.tif':'r'}
        self.dataDir = ""
        self.timer = QTimer()
        
        QObject.connect( self.timer, SIGNAL("timeout()"), self.check )
        QObject.connect( self.dlg.ui.btnBaseDir, SIGNAL( "clicked()" ), self.selectDir )

    def initGui(self):    
        self.action = QAction(QIcon(":/plugins/syncqgiswithdir/syncdirconf.png"), \
            u"Synchronize QGIS with a directory", self.iface.mainWindow())
        self.actionNotify = QAction(QIcon(":/plugins/syncqgiswithdir/notification.png"), \
            u"There are no layers to add", self.iface.mainWindow())
        self.actionNotify.setEnabled(False)
        self.actionStop = QAction(QIcon(":/plugins/syncqgiswithdir/stopsync.png"), \
            u"Stop synchronization", self.iface.mainWindow())
        self.actionStop.setEnabled(False)
            
        # connect the action to the run method
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)
        QObject.connect(self.actionNotify, SIGNAL("triggered()"), self.runNotify)
        QObject.connect(self.actionStop, SIGNAL("triggered()"), self.stop)

        # create toolbar
        self.toolBar = QToolBar("Synchronization tools", self.iface.mainWindow())
        self.toolBar.setObjectName("Sync_ToolBar")
        self.iface.mainWindow().addToolBar(self.toolBar)
        self.toolBar.addAction(self.action)
        self.toolBar.addAction(self.actionNotify)
        self.toolBar.addAction(self.actionStop)
        
        self.iface.addPluginToMenu(u"&Synchronize QGIS with a directory", self.action)
        self.iface.addPluginToMenu(u"&Synchronize QGIS with a directory", self.actionNotify)
        self.iface.addPluginToMenu(u"&Synchronize QGIS with a directory", self.actionStop)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Synchronize QGIS with a directory",self.action)
        self.iface.removePluginMenu(u"&Synchronize QGIS with a directory",self.actionNotify)
        self.iface.removePluginMenu(u"&Synchronize QGIS with a directory",self.actionStop)
        self.iface.mainWindow().removeToolBar(self.toolBar)

        if self.timer.isActive():
            self.timer.stop()

    # run method that performs all the real work
    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()

        if result == 1:    
            self.dataDir = str(self.dlg.ui.txtBaseDir.text())
            extensions = self.dlg.ui.cboFormats.itemData( self.dlg.ui.cboFormats.currentIndex() )
            self.dictExt = dict([ext.split("#") for ext in extensions]) 
            if DEBUG: print "Debug: Extensions",self.dictExt
            
            self.filesFoundLastTime = self.doCheck(self.dataDir, self.dictExt)
            
            if self.dlg.ui.chkLoadExisting.isChecked():
                if self.filesFoundLastTime:
                    if DEBUG: print "Debug: New files", self.filesFoundLastTime
                    self.loadLayers(self.filesFoundLastTime)            
            
            self.timer.setInterval(int(self.dlg.ui.txtPeriod.text()) * 1000)
            self.timer.start()
            self.newFiles = {}
            self.actionNotify.setEnabled(False)
            self.actionNotify.setToolTip("There are no layers to add")
            self.actionStop.setEnabled(True)
            
    def runNotify(self):
        # Load new layers if available 
        self.timer.stop()
        
        if self.newFiles:
            self.loadLayers(self.newFiles)
            self.actionNotify.setToolTip("There are no layers to add")
            self.actionNotify.setEnabled(False)
            
        self.newFiles = {}
        self.timer.start()
        
    def check(self):
        """ Slot for the timer """
        result = self.doCheck(self.dataDir, self.dictExt)
        
        # Filter the new layers 
        newFiles = list(set(result.keys()) - set(self.filesFoundLastTime.keys()))
        self.filesFoundLastTime = result
        if newFiles:
            for key in newFiles:
                self.newFiles[key] = result[key]
            if DEBUG: print "Debug: New files", self.newFiles
            self.actionNotify.setIcon(QIcon(":/plugins/syncqgiswithdir/notification.png"))
            self.actionNotify.setToolTip("There are " + str(len(self.newFiles))
                + " layers to load")
            self.iface.messageBar().pushMessage("Riiing!", "There are " + str(len(self.newFiles))
                + " layers to load. (You can load it/them by clicking the bell button)", level=QgsMessageBar.INFO, duration=10)
            self.actionNotify.setEnabled(True)
        else:
            if DEBUG: print "Debug: Nothing new..."
            
    def doCheck(self, dataDir, dictExt):        
        """ Get all layers in the directory """
        dictFiles = {}
        for ext in dictExt.keys():
            path = os.path.join(dataDir, ''.join(['*',str(ext)]))
            files = glob.glob(path)
            dictFiles.update( dict(zip(files,[dictExt[ext]]*len(files))) )
            
        return dictFiles
        
    def stop(self): 
        if self.timer.isActive():
            self.timer.stop()
        self.actionStop.setEnabled(False)
        
    def loadLayers(self, newLayers):
        for l,f in newLayers.iteritems():
            if f == "v":
                self.iface.addVectorLayer(l, os.path.basename(l), "ogr")
            else:
                self.iface.addRasterLayer(l, os.path.basename(l))
            
    def selectDir(self):
        """ Open a dialog for the user to choose a starting directory """
        settings = QSettings()
        if not settings.value( "/SyncQGISWithDir/path" ) is None:
            tmpPath = settings.value( "/SyncQGISWithDir/path", type=str )
        else:
            tmpPath = '.'
        path = QFileDialog.getExistingDirectory( self.iface.mainWindow(), "Select a directory", 
            tmpPath, QFileDialog.ShowDirsOnly )
        if path: self.dlg.ui.txtBaseDir.setText( path )
    
    def loadFormats(self):    
        self.dlg.ui.cboFormats.addItem( "All listed formats (*.*)",  [".shp#v", ".mif#v", ".tab#v", ".dgn#v", ".vrt#v", ".csv#v", ".gml#v", ".gpx#v", ".kml#v", ".geojson#v", ".gmt#v", ".sqlite#v", ".e00#v", ".dxf#v", ".xml#v", ".vrt#r", ".tif#r", ".tiff#r", ".img#r", ".asc#r", ".png#r", ".jpg#r", ".jpeg#r", ".gif#r", ".xpm#r", ".bmp#r", ".pix#r", ".map#r", ".mpr#r", ".mpl#r", ".hgt#r", ".nc#r", ".grb#r", ".rst#r", ".grd#r", ".rda#r", ".hdr#r", ".dem#r", ".blx#r", ".sqlite#r", ".sdat#r"] ) 
        
        self.dlg.ui.cboFormats.addItem( "All listed vector formats (*.*)",  [".shp#v", ".mif#v", ".tab#v", ".dgn#v", ".vrt#v", ".csv#v", ".gml#v", ".gpx#v", ".kml#v", ".geojson#v", ".gmt#v", ".sqlite#v", ".e00#v", ".dxf#v", ".xml#v"] ) 
        self.dlg.ui.cboFormats.addItem( "All listed raster formats (*.*)",  [".vrt#r", ".tif#r", ".tiff#r", ".img#r", ".asc#r", ".png#r", ".jpg#r", ".jpeg#r", ".gif#r", ".xpm#r", ".bmp#r", ".pix#r", ".map#r", ".mpr#r", ".mpl#r", ".hgt#r", ".nc#r", ".grb#r", ".rst#r", ".grd#r", ".rda#r", ".hdr#r", ".dem#r", ".blx#r", ".sqlite#r", ".sdat#r"] ) 
        
        # Vector formats
        self.dlg.ui.cboFormats.addItem( "ESRI Shapefile (*.shp)",  [".shp#v"] ) 
        self.dlg.ui.cboFormats.addItem( "Mapinfo File (*.mif, *.tab)",  [".mif#v", ".tab#v"] ) 
        self.dlg.ui.cboFormats.addItem( "Microstation DGN (*.dgn)",  [".dgn#v"] ) 
        self.dlg.ui.cboFormats.addItem( "VRT - Virtual Datasource (*.vrt)",  [".vrt#v"] ) 
        self.dlg.ui.cboFormats.addItem( "Comma Separated Value (*.csv)",  [".csv#v"] ) 
        self.dlg.ui.cboFormats.addItem( "Geography Markup Language (*.gml)",  [".gml#v"] ) 
        self.dlg.ui.cboFormats.addItem( "GPX (*.gpx)",  [".gpx#v"] ) 
        self.dlg.ui.cboFormats.addItem( "KML - Keyhole Markup Language (*.kml)",  [".kml#v"] ) 
        self.dlg.ui.cboFormats.addItem( "GeoJSON (*.geojson)",  [".geojson#v"] ) 
        self.dlg.ui.cboFormats.addItem( "GMT (*.gmt)", [".gmt#v"] ) 
        self.dlg.ui.cboFormats.addItem( "SQLite (*.sqlite)",  [".sqlite#v"] ) 
        self.dlg.ui.cboFormats.addItem( "Arc/Info ASCII Coverage (*.e00)",  [".e00#v"] ) 
        self.dlg.ui.cboFormats.addItem( "AutoCAD DXF (*.dxf)",  [".dxf#v"] ) 
        self.dlg.ui.cboFormats.addItem( "GeoRSS (*.xml)", [".xml#v"] ) 
        
        # Raster formats
        self.dlg.ui.cboFormats.addItem( "Virtual Raster (*.vrt)",  [".vrt#r"] ) 
        self.dlg.ui.cboFormats.addItem( "GeoTIFF (*.tif, *.tiff)",  [".tif#r", ".tiff#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Erdas Imagine Images (*.img)",  [".img#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Arc/Info ASCII Grid (*.asc)",  [".asc#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Portable Network Graphics (*.png)",  [".png#r"] ) 
        self.dlg.ui.cboFormats.addItem( "JPEG JFIF (*.jpg, *.jpeg)", [".jpg#r", ".jpeg#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Graphics Interchange Format (*.gif)",  [".gif#r"] ) 
        self.dlg.ui.cboFormats.addItem( "X11 PixMap Format (*.xpm)",  [".xpm#r"] ) 
        self.dlg.ui.cboFormats.addItem( "MS Windows Device Independent Bitmap (*.bmp)",  [".bmp#r"] ) 
        self.dlg.ui.cboFormats.addItem( "PCIDSK Database File (*.pix)",  [".pix#r"] ) 
        self.dlg.ui.cboFormats.addItem( "PCRaster Raster File (*.map)",  [".map#r"] ) 
        self.dlg.ui.cboFormats.addItem( "ILWIS Raster Map (*.mpr, *.mpl)",  [".mpr#r", ".mpl#r"] ) 
        self.dlg.ui.cboFormats.addItem( "SRTMHGT File Format (*.hgt)",  [".hgt#r"] ) 
        self.dlg.ui.cboFormats.addItem( "GMT NetCDF Grid Format (*.nc)",  [".nc#r"] ) 
        self.dlg.ui.cboFormats.addItem( "GRIdded Binary (*.grb)",  [".grb#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Idrisi Raster A.1 (*.rst)", [".rst#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Golden Software ASCII Grid (*.grd)",  [".grd#r"] ) 
        self.dlg.ui.cboFormats.addItem( "R Object Data Store (*.rda)", [".rda#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Vexcel MFF Raster (*.hdr)",  [".hdr#r"] ) 
        self.dlg.ui.cboFormats.addItem( "USGS Optional ASCII DEM (*.dem)", [".dem#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Magellan topo (*.blx)", [".blx#r"] ) 
        self.dlg.ui.cboFormats.addItem( "Rasterlite (*.sqlite)", [".sqlite#r"] ) 
        self.dlg.ui.cboFormats.addItem( "SAGA GIS Binary Grid (*.sdat)", [".sdat#r"] ) 


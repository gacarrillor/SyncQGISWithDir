# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SyncQGISWithDirDialog
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

from PyQt4 import QtCore, QtGui
from ui_syncqgiswithdir import Ui_SyncQGISWithDir
# create the dialog for zoom to point
class SyncQGISWithDirDialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        # Set up the user interface from Designer.
        self.ui = Ui_SyncQGISWithDir()
        self.ui.setupUi(self)

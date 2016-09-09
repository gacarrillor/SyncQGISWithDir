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
 This script initializes the plugin, making it known to QGIS.
"""
def name():
    return "Synchronize QGIS with a directory"
def description():
    return "Lets you know when new layers are available in a directory, so that you can load them to QGIS "
def version():
    return "Version 2.2"
def icon():
    return "icon.png"
def qgisMinimumVersion():
    return "2.0"
def classFactory(iface):
    # load SyncQGISWithDir class from file SyncQGISWithDir
    from syncqgiswithdir import SyncQGISWithDir
    return SyncQGISWithDir(iface)
def author():    
    return "Germán Carrillo (GeoTux)"
def email():    
    return "geotux_tuxman@linuxmail.org"

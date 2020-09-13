#!/usr/bin/python3
# coding=utf-8

# Copyright (C) 2019 Hans P. Möller <hmollercl@lubuntu.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

''' Open Notification Dialog to enable upgrade'''

import sys
import subprocess
from pathlib import Path
import apt_pkg
from argparse import ArgumentParser
import gettext

from PyQt5.QtWidgets import (QWidget, QApplication, QLabel, QPushButton,
                             QHBoxLayout, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


class Dialog(QWidget):
    ''' UI '''

    def __init__(self, upgrades, security_upgrades, reboot_required, upg_path):
        QWidget.__init__(self)
        self.upgrades = upgrades
        self.security_upgrades = security_upgrades
        self.upg_path = upg_path
        self.reboot_required = reboot_required

        apt_pkg.init()
        try:
            self.cache = apt_pkg.Cache()
        except SystemError as e:
            sys.stderr.write(_("Error: Opening the cache (%s)") % e)
            sys.exit(-1)
        self.depcache = apt_pkg.DepCache(self.cache)

        self.initUI()
        self.upgradeBtn.clicked.connect(self.call_upgrade)
        self.closeBtn.clicked.connect(self.call_reject)

    def initUI(self):
        ''' UI initialization '''
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignHCenter)

        self.tw = QTreeWidget()
        self.tw.setColumnCount(1)
        self.tw.setHeaderLabels([_('Affected Packages')])
        self.tw.setHeaderHidden(True)

        self.upgradeBtn = QPushButton("Upgrade")
        self.closeBtn = QPushButton("Close")
        text = ""

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.upgradeBtn)
        hbox.addWidget(self.closeBtn)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.label)
        vbox.addWidget(self.tw)
        vbox.addLayout(hbox)

        if self.upg_path is None:
            self.upgradeBtn.setVisible(False)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 500, 150)
        self.setWindowTitle("Update Notifier")
        self.center()

        if self.upgrades > 0:
            self.depcache.upgrade(True)  # True for non safe.
            pkg_install = list()
            pkg_upgrade = list()
            pkg_delete = list()
            for p in self.cache.packages:
                if self.depcache.marked_delete(p):
                    pkg_delete.append(p.name)
                elif self.depcache.marked_install(p):
                    pkg_install.append(p.name)
                elif self.depcache.marked_upgrade(p):
                    pkg_upgrade.append(p.name)
            text = _("There are upgrades available. Do you want to do a system "
                     "upgrade?")
            text += "\n"
            text += _("This will mean packages could be upgraded, installed, or "
                    "removed.")

            if len(pkg_delete) > 0:
                toDelete = QTreeWidgetItem([_('Remove')])
                for p in pkg_delete:
                    td_child = QTreeWidgetItem([p])
                    toDelete.addChild(td_child)
                toDelete.setIcon(0, QIcon.fromTheme("edit-delete"))
                self.tw.addTopLevelItem(toDelete)
            if len(pkg_install) > 0:
                toInstall = QTreeWidgetItem([_('Install')])
                for p in pkg_install:
                    td_child = QTreeWidgetItem([p])
                    toInstall.addChild(td_child)
                toInstall.setIcon(0, QIcon.fromTheme("system-software-install"))
                self.tw.addTopLevelItem(toInstall)
            if len(pkg_upgrade) > 0:
                toUpgrade = QTreeWidgetItem([_('Upgrade')])
                for p in pkg_upgrade:
                    td_child = QTreeWidgetItem([p])
                    toUpgrade.addChild(td_child)
                toUpgrade.setIcon(0, QIcon.fromTheme("system-software-update"))
                self.tw.addTopLevelItem(toUpgrade)

        if self.reboot_required:
            if text == "":
                text = _("Reboot required")
                self.upgradeBtn.setVisible(False)
            else:
                text += "\n"
                text += _("Reboot required")

        self.label.setText(text)

    def center(self):
        ''' puts UI in center of screen '''
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def call_reject(self):
        ''' when close button is pressed, quit '''
        app.quit()

    def call_upgrade(self):
        ''' starts upgrade process '''
        self.label.setText(_("Upgrading..."))
        # TODO maybe open another thread so notifier won't freeze
        if self.upg_path == "terminal":
            # cmd = ['qterminal', '-e', 'sudo', 'apt', 'dist-upgrade']
            cmd = ['qterminal', '-e', './upg.sh']
        else:
            cmd = ['lxqt-sudo', self.upg_path, '--full-upgrade']
        # process = subprocess.Popen(self.upg_path)
        # process = subprocess.Popen(cmd, shell=True)
        self.upgradeBtn.setVisible(False)
        self.upgradeBtn.setEnabled(False)
        process = subprocess.Popen(cmd)
        process.wait()

        if self.upg_path == "terminal":
            text = _("Upgrade finished")

            reboot_required_path = Path("/var/run/reboot-required")
            if reboot_required_path.exists():
                text += "\n" + _("Reboot required")
            self.label.setText(text)
            self.closeBtn.setVisible(True)
            self.closeBtn.setEnabled(True)

        else:
            app.quit()


class App(QApplication):
    '''application'''
    def __init__(self, upgrades, security_upgrades, reboot_required, upg_path,
                 *args):
        QApplication.__init__(self, *args)
        self.dialog = Dialog(upgrades, security_upgrades, reboot_required,
                             upg_path)
        self.dialog.show()


def main(args, upgrades, security_upgrades, reboot_required, upg_path):
    '''main'''
    global app
    app = App(upgrades, security_upgrades, reboot_required, upg_path, args)
    app.setWindowIcon(QIcon.fromTheme("system-software-update"))
    app.exec_()


if __name__ == "__main__":
    localesApp ="lubuntu-update-notifier"
    localesDir ="/usr/share/locale"
    gettext.bindtextdomain(localesApp, localesDir)
    gettext.textdomain(localesApp)
    _ = gettext.gettext

    parser = ArgumentParser()
    parser.add_argument("-p",
                        "--upgrader-sw",
                        dest="upg_path",
                        help=_("Define software/app to open for upgrade"),
                        metavar="APP")
    parser.add_argument("-u",
                        "--upgrades",
                        dest="upgrades",
                        help=_("How many upgrades are available"),
                        metavar="APP")
    parser.add_argument("-s",
                        "--security-upg",
                        dest="security_upgrades",
                        help=_("How many security upgrades are available"),
                        metavar="APP")

    options = parser.parse_args()

    reboot_required_path = Path("/var/run/reboot-required")
    reboot_required = reboot_required_path.exists()

    if int(options.upgrades) > 0 or reboot_required:
        main(sys.argv, int(options.upgrades), int(options.security_upgrades),
             reboot_required, options.upg_path)

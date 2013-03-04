#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2013 Frédéric Massart - FMCorz.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

http://github.com/FMCorz/mdk
"""

import os
import urllib
import re
import logging
from time import sleep
from lib.command import Command
from lib.tools import process, ProcessInThread


class BehatCommand(Command):

    _arguments = [
        (
            ['-r', '--run'],
            {
                'action': 'store_true',
                'help': 'run the tests'
            }
        ),
        (
            ['-j', '--no-javascript'],
            {
                'action': 'store_true',
                'dest': 'nojavascript',
                'help': 'skip the tests involving Javascript'
            }
        ),
        (
            ['-s', '--switch-completely'],
            {
                'action': 'store_true',
                'dest': 'switchcompletely',
                'help': 'force the switch completely setting. This will be automatically enabled for PHP < 5.4'
            }
        ),
        (
            ['--selenium'],
            {
                'default': None,
                'dest': 'selenium',
                'help': 'path to the selenium standalone server to use',
                'metavar': 'jarfile',
                'nargs': '?'
            }
        ),
        (
            ['--selenium-verbose'],
            {
                'action': 'store_true',
                'dest': 'seleniumverbose',
                'help': 'outputs the output from selenium in the same window'
            }
        ),
        (
            ['name'],
            {
                'default': None,
                'help': 'name of the instance',
                'metavar': 'name',
                'nargs': '?'
            }
        )
    ]
    _description = 'Initialise Behat'

    def run(self, args):

        # Loading instance
        M = self.resolve(args.name)
        if not M:
            raise Exception('This is not a Moodle instance')

        # Check if installed
        if not M.get('installed'):
            raise Exception('This instance needs to be installed first')

        # No Javascript
        nojavascript = args.nojavascript
        if not nojavascript and not self.C.get('java') or not os.path.isfile(os.path.abspath(self.C.get('java'))):
            nojavascript = True
            logging.info('Disabling Javascript because Java is required to run Selenium and could not be found.')

        # If not composer.phar, install Composer
        if not os.path.isfile(os.path.join(M.get('path'), 'composer.phar')):
            logging.info('Installing Composer')
            cliFile = 'behat_install_composer.php'
            cliPath = os.path.join(M.get('path'), 'behat_install_composer.php')
            urllib.urlretrieve('http://getcomposer.org/installer', cliPath)
            M.cli('/' + cliFile, stdout=None, stderr=None)
            os.remove(cliPath)
            M.cli('composer.phar', args='install --dev', stdout=None, stderr=None)

        # Download selenium
        seleniumPath = os.path.expanduser(os.path.join(self.C.get('dirs.mdk'), 'selenium.jar'))
        if args.selenium:
            seleniumPath = args.selenium
        elif not nojavascript and not os.path.isfile(seleniumPath):
            logging.info('Attempting to find a download for Selenium')
            url = urllib.urlopen('http://docs.seleniumhq.org/download/')
            content = url.read()
            selenium = re.search(r'http:[a-z0-9/._-]+selenium-server-standalone-[0-9.]+\.jar', content, re.I)
            if selenium:
                logging.info('Downloading Selenium from %s' % (selenium.group(0)))
                urllib.urlretrieve(selenium.group(0), seleniumPath)
            else:
                logging.warning('Could not locate Selenium server to download')

        if not os.path.isfile(seleniumPath):
            raise Exception('Selenium file %s does not exist')

        # Run cli
        try:
            M.initBehat(switchcompletely=args.switchcompletely)
            logging.info('Behat ready!')

            # Preparing Behat command
            cmd = ['vendor/bin/behat']
            if nojavascript:
                cmd.append('--tags ~@javascript')
            cmd.append('--config=%s/behat/behat.yml' % (M.get('behat_dataroot')))
            cmd = ' '.join(cmd)

            phpCommand = '%s -S localhost:8000' % (self.C.get('php'))
            seleniumCommand = None
            if seleniumPath:
                seleniumCommand = '%s -jar %s' % (self.C.get('java'), seleniumPath)

            if args.run:
                logging.info('Preparing Behat testing')

                # Preparing PHP Server
                phpServer = None
                if not M.get('behat_switchcompletely'):
                    logging.info('Starting standalone PHP server')
                    kwargs = {}
                    kwargs['cwd'] = M.get('path')
                    phpServer = ProcessInThread(phpCommand, **kwargs)
                    phpServer.start()

                # Launching Selenium
                seleniumServer = None
                if seleniumPath and not nojavascript:
                    logging.info('Starting Selenium server')
                    kwargs = {}
                    if args.seleniumverbose:
                        kwargs['stdout'] = None
                        kwargs['stderr'] = None
                    seleniumServer = ProcessInThread(seleniumCommand, **kwargs)
                    seleniumServer.start()

                logging.info('Running Behat tests')

                # Sleep for a few seconds before starting Behat
                if phpServer or seleniumServer:
                    sleep(3)

                # Running the tests
                process(cmd, M.path, None, None)

                # Kill the remaining processes
                if phpServer:
                    phpServer.kill()
                if seleniumServer:
                    seleniumServer.kill()

                # Remove the switch completely tag
                if M.get('behat_switchcompletely'):
                    M.removeConfig('behat_switchcompletely')

            else:
                logging.info('Launch PHP Server (or set $CFG->behat_switchcompletely to True):\n %s' % (phpCommand))
                if seleniumCommand:
                    logging.info('Launch Selenium (optional):\n %s' % (seleniumCommand))
                logging.info('Launch Behat:\n %s' % (cmd))

        except Exception as e:
            raise e

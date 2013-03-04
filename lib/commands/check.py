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
import shutil
from lib import git
from lib.command import Command


class CheckCommand(Command):

    _arguments = [
        (
            ['--fix'],
            {
                'action': 'store_true',
                'help': 'Automatically fix the identified problems'
            }
        )
    ]
    _description = 'Perform several checks on your current installation'

    def run(self, args):

        # Check directories
        self.directories(args)

        # Check the cached remotes
        self.cachedRepositories(args)

    def cachedRepositories(self, args):
        """Ensure that the cached repositories are valid"""

        print 'Checking cached repositories'
        cache = os.path.abspath(os.path.realpath(os.path.expanduser(self.C.get('dirs.mdk'))))

        dirs = [
            {
                'dir': os.path.join(cache, 'moodle.git'),
                'url': self.C.get('remotes.stable')
            },
            {
                'dir': os.path.join(cache, 'integration.git'),
                'url': self.C.get('remotes.integration')
            },
        ]

        for d in dirs:
            directory = d['dir']
            name = os.path.split(directory)[1]

            if os.path.isdir(directory):
                if os.path.isdir(os.path.join(directory, '.git')):
                    print '  %s is not a bare repository' % name
                    if args.fix:
                        print '    Renaming %s/.git directory to %s' % (directory, directory)
                        os.rename(directory, directory + '.tmp')
                        os.rename(os.path.join(directory + '.tmp', '.git'), directory)
                        shutil.rmtree(directory + '.tmp')

                repo = git.Git(directory, self.C.get('git'))
                if repo.getConfig('core.bare') != 'true':
                    print '  %s core.bare is not set to true' % name
                    if args.fix:
                        print '    Setting core.bare to true'
                        repo.setConfig('core.bare', 'true')

                if repo.getConfig('remote.origin.url') != d['url']:
                    print '  %s uses an different origin (%s)' % (name, repo.getConfig('remote.origin.url'))
                    if args.fix:
                        print '    Setting remote.origin.url to %s' % d['url']
                        repo.setConfig('remote.origin.url', d['url'])

                if repo.getConfig('remote.origin.fetch') != '+refs/*:refs/*':
                    print '  %s fetch value is invalid (%s)' % (name, repo.getConfig('remote.origin.fetch'))
                    if args.fix:
                        print '    Setting remote.origin.fetch to %s' % '+refs/*:refs/*'
                        repo.setConfig('remote.origin.fetch', '+refs/*:refs/*')

    def directories(self, args):
        """Check that the directories are valid"""

        print 'Checking directories'
        for k, d in self.C.get('dirs').items():
            d = os.path.abspath(os.path.realpath(os.path.expanduser(d)))
            if not os.path.isdir(d):
                print '  %s does not exist' % d
                if args.fix:
                    print '    Creating %s' % d
                    os.mkdir(d, 0777)

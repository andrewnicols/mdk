#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2014 Frédéric Massart - FMCorz.net

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

import logging
import os
from lib.command import Command
from lib import js, plugins


class JsCommand(Command):

    _arguments = [
        (
            ['mode'],
            {
                'metavar': 'mode',
                'help': 'the type of action to perform',
                'sub-commands':
                    {
                        'shift': (
                            {
                                'help': 'keen to use shifter?'
                            },
                            [
                                (
                                    ['-p', '--plugin'],
                                    {
                                        'action': 'store',
                                        'dest': 'plugin',
                                        'default': None,
                                        'help': 'the name of the plugin or subsystem to target. If not passed, we do our best to guess from the current path.'
                                    }
                                ),
                                (
                                    ['-m', '--module'],
                                    {
                                        'action': 'store',
                                        'dest': 'module',
                                        'default': None,
                                        'help': 'the name of the module in the plugin or subsystem. If omitted all the modules will be shifted, except we are in a module.'
                                    }
                                ),
                                # (
                                #     ['-w', '--watch'],
                                #     {
                                #         'action': 'store_true',
                                #         'dest': 'watch',
                                #         'help': 'watch for changes to re-shift'
                                #     }
                                # ),
                                (
                                    ['names'],
                                    {
                                        'default': None,
                                        'help': 'name of the instances',
                                        'metavar': 'names',
                                        'nargs': '*'
                                    }
                                )
                            ]
                        )
                    }
            }
        )
    ]
    _description = 'Wrapper for JS functions'

    def run(self, args):
        if args.mode == 'shift':
            self.shift(args)


    def shift(self, args):
        """The shift mode"""

        Mlist = self.Wp.resolveMultiple(args.names)
        if len(Mlist) < 1:
            raise Exception('No instances to work on. Exiting...')

        cwd = os.path.realpath(os.path.abspath(os.getcwd()))
        mpath = Mlist[0].get('path')
        relpath = cwd.replace(mpath, '').strip('/')

        if not args.plugin:
            (subsystemOrPlugin, pluginName) = plugins.PluginManager.getSubsystemOrPluginFromPath(cwd, Mlist[0])
            if subsystemOrPlugin:
                args.plugin = subsystemOrPlugin + ('_' + pluginName) if pluginName else ''
                logging.info("I guessed the plugin/subsystem to work on as '%s'" % (args.plugin))
            else:
                self.argumentError('The argument --plugin is required, I could not guess it.')

        if not args.module:
            candidate = relpath
            module = None
            while '/yui/src' in candidate:
                (head, tail) = os.path.split(candidate)
                if head.endswith('/yui/src'):
                    module = tail
                    break
                candidate = head

            if module:
                args.module = module
                logging.info("I guessed the JS module to work on as '%s'" % (args.module))


        for M in Mlist:
            if len(Mlist) > 1:
                logging.info('Let\'s shift everything you wanted on \'%s\'' % (M.get('identifier')))

            processor = js.Js(M)
            processor.shift(subsystemOrPlugin=args.plugin, module=args.module)
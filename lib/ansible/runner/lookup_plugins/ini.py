# (c) 2015, Yannig Perre <yannig.perre(at)gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible import utils, errors
import StringIO
import os
import codecs
import ConfigParser
import re

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir
        self.cp      = ConfigParser.ConfigParser()

    def read_properties(self, filename, key, dflt, is_regexp):
        config = StringIO.StringIO()
        config.write('[java_properties]\n' + open(filename).read())
        config.seek(0, os.SEEK_SET)
        self.cp.readfp(config)
        return self.get_value(key, 'java_properties', dflt, is_regexp)

    def read_ini(self, filename, key, section, dflt, is_regexp):
        self.cp.readfp(open(filename))
        return self.get_value(key, section, dflt, is_regexp)

    def get_value(self, key, section, dflt, is_regexp):
        # Retrieve all values from a section using a regexp
        if is_regexp:
            return [v for k, v in self.cp.items(section) if re.match(key, k)]
        value = None
        # Retrieve a single value
        try:
            value = self.cp.get(section, key)
        except ConfigParser.NoOptionError, e:
            return dflt
        return value

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        if isinstance(terms, basestring):
            terms = [ terms ]

        ret = []
        for term in terms:
            params = term.split()
            key = params[0]

            paramvals = {
                'file'     : 'ansible.ini',
                're'       : False,
                'default'  : None,
                'section'  : "global",
                'type'     : "ini",
            }

            # parameters specified?
            try:
                for param in params[1:]:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value
            except (ValueError, AssertionError), e:
                raise errors.AnsibleError(e)

            path = utils.path_dwim(self.basedir, paramvals['file'])
            if paramvals['type'] == "properties":
                var = self.read_properties(path, key, paramvals['default'], paramvals['re'])
            else:
                var = self.read_ini(path, key, paramvals['section'], paramvals['default'], paramvals['re'])
            if var is not None:
                if type(var) is list:
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)
        return ret

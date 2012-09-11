# vi: ts=4 expandtab
#
#    Copyright (C) 2012 Yahoo! Inc.
#
#    Author: Joshua Harlow <harlowja@yahoo-inc.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3, as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os

from builder import util

import json


class TarBallDownloader(object):
    def __init__(self, config):
        self.cache_dir = config.get('cache_dir') or 'cache'
        self.where_from = config['from']
        self.root_file = config.get('root_file')

    def _check_cache(self):
        cache_name = util.hash_blob(self.where_from, 'md5', mlen=8)
        full_pth = os.path.join(self.cache_dir, "%s.tar.gz" % (cache_name))
        if os.path.isfile(full_pth):
            return (full_pth, True)
        return (full_pth, False)

    def _adjust_real_root(self, arch_path):
        if self.root_file:
            print("Oh you really meant %s, finding that file..." % (util.quote(self.root_file)))
            # Extract and then copy over the right file...
            with util.tempdir() as tdir:
                arch_dir = os.path.join(tdir, 'archive')
                os.makedirs(arch_dir)
                util.subp(['tar', '-xzf', arch_path, '-C', arch_dir])
                root_gz = util.find_file(self.root_file, arch_dir)
                if not root_gz:
                    raise RuntimeError(("Needed file %r not found in"
                                        " extracted contents of %s") 
                                        % (self.root_file, cache_pth))
                else:
                    util.copy(root_gz, arch_path)
        return arch_path

    def download(self):
        (cache_pth, exists_there) = self._check_cache()
        if exists_there:
            return cache_pth
        print("Downloading from: %s" % (util.quote(self.where_from)))
        util.ensure_dirs([os.path.dirname(cache_pth)])
        print("To: %s" % (util.quote(cache_pth)))
        util.download_url(self.where_from, cache_pth)
        try:
            meta_js = {
                'cached_on': util.time_rfc2822(),
                'from': self.where_from,
                'root_file': self.root_file,
            }
            util.write_file("%s.json" % (cache_pth),
                            "%s\n" % (json.dumps(meta_js, indent=4)))
            return self._adjust_real_root(cache_pth)
        except:
            util.del_file(cache_pth)
            raise
import sys
from os.path import abspath, basename

import menuinst


def main():
    from optparse import OptionParser

    p = OptionParser(
        usage="usage: %prog [options] MENU_FILE",
        description="install a menu item")

    p.add_option('-p', '--prefix',
                 action="store",
                 default=sys.prefix)

    p.add_option('--remove',
                 action="store_true")

    p.add_option('--version',
                 action="store_true")

    opts, args = p.parse_args()

    if opts.version:
        sys.stdout.write("menuinst: %s" % menuinst.__version__)
        return

    if abspath(opts.prefix) == abspath(sys.prefix):
        env_name = None
        env_setup_cmd = None
    else:
        env_name = basename(opts.prefix)
        env_setup_cmd = 'activate "%s"' % env_name

    for path in args:
        menuinst.install(path,
                         remove=opts.remove,
                         target_prefix=opts.prefix,
                         env_name=env_name,
                         env_setup_cmd=env_setup_cmd)


if __name__ == '__main__':
    main()

# Copyright (C) 2011 Luca Ferroni <http://www.lucaferroni.it>
#
# This file is part of OpenVPN monitor
# OpenVPN monitor is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License
#
# OpenVPN monitor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenVPN monitor. If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import random
import string

from django.utils import six
from django.conf import settings


class CalledShellCommandError(Exception):
    """Exception raised for errors in shell command execution

    Attributes:
        shell_cmd -- shell command
        output  -- command output
        returncode -- error code
    """

    DEFAULT_OUTPUT = "no output provided (using python 2.6?)"

    def __init__(self, shell_cmd, returncode, output=DEFAULT_OUTPUT):
        self.shell_cmd = shell_cmd
        self.returncode = returncode
        self.output = output


def call_shell(shell_cmd, stdin=None):
    """Call shell command and normalize exception output."""
    towrite = ''

    if isinstance(stdin, six.text_type) or isinstance(stdin, str):
        towrite = stdin
        stdin = subprocess.PIPE

    try:
        if stdin is not subprocess.PIPE:
            rv = subprocess.check_output(shell_cmd,
                                         stdin=stdin,
                                         stderr=subprocess.STDOUT,
                                         shell=True)
        else:
            process = subprocess.Popen(shell_cmd,
                                       stdin=stdin,
                                       stderr=subprocess.STDOUT,
                                       shell=True,
                                       stdout=subprocess.PIPE)
            process.stdin.write(towrite + '\n')
            output, unused_err = process.communicate()
            retcode = process.poll()
            if retcode:
                raise subprocess.CalledProcessError(
                    retcode, shell_cmd, output=output)
            return output
    except subprocess.CalledProcessError as e:
        raise CalledShellCommandError(shell_cmd, e.returncode, e.output)
    except AttributeError:  # python 2.6
        try:
            rv = subprocess.check_call(shell_cmd, stdin=stdin, shell=True)
        except subprocess.CalledProcessError as e:
            raise CalledShellCommandError(shell_cmd, e.returncode)
    except OSError as e:
        raise CalledShellCommandError(shell_cmd, e.errno, e)
    return rv


def gen_difficult_password(length=10):

    SPECIAL_CHARS = '*()!&,.<:'
    SPECIAL_CHARS = '@.+-_'  # Limitazione applicazione SPES
    total = string.ascii_letters + SPECIAL_CHARS + string.digits
    password = ''.join(random.sample(total, length))
    return password


def get_manage_shell_cmd(cmd, *args, **kw):

    ENVIRONMENT_VARIABLE = "DJANGO_SETTINGS_MODULE"
    settings_module = os.environ[ENVIRONMENT_VARIABLE]
    kw_expanded = ""
    for k, v in kw.items():
        kw_expanded += "--%s=%s" % (k, v)
    args_expanded = " ".join(args)
    cmd = "%s/manage.py %s --settings=%s %s %s" % (settings.PROJECT_ROOT, cmd,
                                                   settings_module,
                                                   kw_expanded, args_expanded)
    if os.environ.get("VIRTUAL_ENV"):
        cmd = ". %s/bin/activate && %s" % (os.environ["VIRTUAL_ENV"], cmd)
    return cmd

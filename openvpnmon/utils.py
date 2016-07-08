
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


import subprocess

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

#-----------------------------------------------------------------------------------

def call_shell(shell_cmd):
    """Call shell command and normalize exception output."""

    try:
        rv = subprocess.check_output(shell_cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        raise CalledShellCommandError(shell_cmd, e.returncode, e.output) 
    except AttributeError:  #python 2.6
        try:
            rv = subprocess.check_call(shell_cmd, shell=True)
        except subprocess.CalledProcessError as e:
            raise CalledShellCommandError(shell_cmd, e.returncode) 
    except OSError as e:
        raise CalledShellCommandError(shell_cmd, e.errno, e) 
    return rv


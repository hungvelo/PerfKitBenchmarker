# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module containing classes related to GCE VM networking.

The Firewall class provides a way of opening VM ports. The Network class allows
VMs to communicate via internal ips and isolates PerfKitBenchmarker VMs from
others in the
same project. See https://developers.google.com/compute/docs/networking for
more information about GCE VM networking.
"""
import threading

from perfkitbenchmarker import flags
from perfkitbenchmarker import network
from perfkitbenchmarker import vm_util
from perfkitbenchmarker.gcp import util


FLAGS = flags.FLAGS


class GceFirewall(network.BaseFirewall):
  """An object representing the GCE Firewall."""

  def __init__(self, project):
    """Initialize GCE firewall class.

    Args:
      project: The GCP project name under which firewall is created.
    """
    self._lock = threading.Lock()
    self.firewall_names = []
    self.project = project

  def __getstate__(self):
    """Implements getstate to allow pickling (since locks can't be pickled)."""
    d = self.__dict__.copy()
    del d['_lock']
    return d

  def __setstate__(self, state):
    """Restores the lock after the object is unpickled."""
    self.__dict__ = state
    self._lock = threading.Lock()

  def AllowPort(self, vm, port):
    """Opens a port on the firewall.

    Args:
      vm: The BaseVirtualMachine object to open the port for.
      port: The local port to open.
    """
    if vm.is_static:
      return
    with self._lock:
      firewall_name = ('perfkit-firewall-%s-%d' %
                       (FLAGS.run_uri, port))
      if firewall_name in self.firewall_names:
        return
      firewall_cmd = [FLAGS.gcloud_path,
                      'compute',
                      'firewall-rules',
                      'create',
                      firewall_name,
                      '--allow', 'tcp:%d' % port, 'udp:%d' % port]
      firewall_cmd.extend(util.GetDefaultGcloudFlags(self))

      vm_util.IssueRetryableCommand(firewall_cmd)
      self.firewall_names.append(firewall_name)

  def DisallowAllPorts(self):
    """Closes all ports on the firewall."""
    for firewall in self.firewall_names:
      firewall_cmd = [FLAGS.gcloud_path,
                      'compute',
                      'firewall-rules',
                      'delete',
                      firewall]
      firewall_cmd.extend(util.GetDefaultGcloudFlags(self))
      vm_util.IssueRetryableCommand(firewall_cmd)


class GceNetwork(network.BaseNetwork):
  """Object representing a GCE Network."""

  def Create(self):
    """Creates the actual network."""
    pass

  def Delete(self):
    """Deletes the actual network."""
    pass

#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from fuelweb_test.helpers.decorators import log_snapshot_after_test
from proboscis import test

from stacklight_tests.toolchain import api


@test(groups=["plugins"])
class TestDestructiveToolchainPlugin(api.ToolchainApi):
    """Class for testing plugin failover after network disaster."""

    @test(depends_on_groups=["deploy_ha_toolchain"],
          groups=["check_disaster_toolchain", "toolchain",
                  "destructive", "check_cluster_outage_toolchain"])
    @log_snapshot_after_test
    def check_cluster_outage_toolchain(self):
        """Verify that the backends and dashboards recover
        after a network outage of the whole cluster with plugins toolchain.

        Scenario:
            1. Revert the snapshot with 9 deployed nodes in HA configuration
            2. Simulate a network outage of the whole cluster
               with plugins toolchain
            3. Wait for at least 7 minutes before network recovery
            4. Wait for all services to be back online
            5. Run OSTF
            6. Check that the cluster's state is okay

        Duration 40m
        """
        self.env.revert_snapshot("deploy_ha_toolchain")

        self.helpers.emulate_whole_network_disaster(
            delay_before_recover=7 * 60)

        self.INFLUXDB_GRAFANA.wait_plugin_online()
        self.ELASTICSEARCH_KIBANA.wait_plugin_online()
        self.LMA_INFRASTRUCTURE_ALERTING.wait_plugin_online()

        # NOTE(rpromyshlennikov): OpenStack cluster can't recover after it,
        # but plugins toolchain is working properly
        self.helpers.run_ostf()

    @test(depends_on_groups=["deploy_toolchain"],
          groups=["check_disaster_toolchain", "toolchain",
                  "destructive", "check_node_outage_toolchain"])
    @log_snapshot_after_test
    def check_node_outage_toolchain(self):
        """Verify that the backends and dashboards recover after
        a network outage on a standalone plugins toolchain node.

        Scenario:
            1. Revert the snapshot with 3 deployed nodes
            2. Simulate network interruption on the Toolchain node
            3. Wait for at least 30 seconds before recover network availability
            4. Run OSTF
            5. Check that plugins toolchain is working

        Duration 20m
        """
        self.env.revert_snapshot("deploy_toolchain")

        with self.fuel_web.get_ssh_for_nailgun_node(
                self.helpers.get_master_node_by_role(
                    self.settings.stacklight_roles)
        ) as remote:
            self.remote_ops.simulate_network_interrupt_on_node(remote)

        self.INFLUXDB_GRAFANA.wait_plugin_online()
        self.ELASTICSEARCH_KIBANA.wait_plugin_online()
        self.LMA_INFRASTRUCTURE_ALERTING.wait_plugin_online()

        self.helpers.run_ostf()

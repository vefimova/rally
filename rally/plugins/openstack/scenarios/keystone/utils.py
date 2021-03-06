# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
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

import uuid

from rally.plugins.openstack import scenario
from rally.task.scenarios import base


def is_temporary(resource):
    return resource.name.startswith(KeystoneScenario.RESOURCE_NAME_PREFIX)


class KeystoneScenario(scenario.OpenStackScenario):
    """Base class for Keystone scenarios with basic atomic actions."""

    RESOURCE_NAME_PREFIX = "rally_keystone_"

    @base.atomic_action_timer("keystone.create_user")
    def _user_create(self, name_length=10, email=None, **kwargs):
        """Creates keystone user with random name.

        :param name_length: length of generated (random) part of name
        :param kwargs: Other optional parameters to create users like
                        "tenant_id", "enabled".
        :returns: keystone user instance
        """
        name = self._generate_random_name(length=name_length)
        # NOTE(boris-42): password and email parameters are required by
        #                 keystone client v2.0. This should be cleanuped
        #                 when we switch to v3.
        password = kwargs.pop("password", str(uuid.uuid4()))
        email = email or (name + "@rally.me")
        return self.admin_clients("keystone").users.create(
            name, password=password, email=email, **kwargs)

    @base.atomic_action_timer("keystone.update_user_enabled")
    def _update_user_enabled(self, user, enabled):
        """Enable or disable a user.

        :param user: The user to enable or disable
        :param enabled: Boolean indicating if the user should be
                        enabled (True) or disabled (False)
        """
        self.admin_clients("keystone").users.update_enabled(user, enabled)

    def _resource_delete(self, resource):
        """"Delete keystone resource."""
        r = "keystone.delete_%s" % resource.__class__.__name__.lower()
        with base.AtomicAction(self, r):
            resource.delete()

    @base.atomic_action_timer("keystone.create_tenant")
    def _tenant_create(self, name_length=10, **kwargs):
        """Creates keystone tenant with random name.

        :param name_length: length of generated (random) part of name
        :param kwargs: Other optional parameters
        :returns: keystone tenant instance
        """
        name = self._generate_random_name(length=name_length)
        return self.admin_clients("keystone").tenants.create(name, **kwargs)

    @base.atomic_action_timer("keystone.create_service")
    def _service_create(self, service_type="rally_test_type",
                        description=None):
        """Creates keystone service with random name.

        :param name: name of the service
        :param service_type: type of the service
        :param description: description of the service
        :returns: keystone service instance
        """
        description = description or self._generate_random_name(
            prefix="rally_test_service_description_")
        return self.admin_clients("keystone").services.create(
            self._generate_random_name(),
            service_type, description)

    @base.atomic_action_timer("keystone.create_users")
    def _users_create(self, tenant, users_per_tenant, name_length=10):
        """Adds users to a tenant.

        :param tenant: tenant object
        :param users_per_tenant: number of users in per tenant
        :param name_length: length of generated (random) part of name for user
        """
        for i in range(users_per_tenant):
            name = self._generate_random_name(length=name_length)
            password = name
            email = (name + "@rally.me")
            self.admin_clients("keystone").users.create(
                name, password=password, email=email, tenant_id=tenant.id)

    @base.atomic_action_timer("keystone.create_role")
    def _role_create(self, name_length=5):
        """Creates keystone user role with random name.

        :param name_length: length of generated (random) part of role name
        :returns: keystone user role instance
        """
        role = self.admin_clients("keystone").roles.create(
            self._generate_random_name(length=name_length))
        return role

    @base.atomic_action_timer("keystone.list_users")
    def _list_users(self):
        """List users."""
        return self.admin_clients("keystone").users.list()

    @base.atomic_action_timer("keystone.list_tenants")
    def _list_tenants(self):
        """List tenants."""
        return self.admin_clients("keystone").tenants.list()

    @base.atomic_action_timer("keystone.service_list")
    def _list_services(self):
        """List services."""
        return self.admin_clients("keystone").services.list()

    @base.atomic_action_timer("keystone.list_roles")
    def _list_roles_for_user(self, user, tenant):
        """List user roles.

        :param user: user for whom roles will be listed
        :param tenant: tenant on which user have roles
        """
        return self.admin_clients("keystone").roles.roles_for_user(
            user, tenant)

    @base.atomic_action_timer("keystone.add_role")
    def _role_add(self, user, role, tenant):
        """Add role to a given user on a tenant.

        :param user: user to be assigned the role to
        :param role: user role to assign with
        :param tenant: tenant on which assignation will take place
        """
        self.admin_clients("keystone").roles.add_user_role(user, role, tenant)

    @base.atomic_action_timer("keystone.remove_role")
    def _role_remove(self, user, role, tenant):
        """Dissociate user with role.

        :param user: user to be stripped with role
        :param role: role to be dissociated with user
        :param tenant: tenant on which assignation took place
        """
        self.admin_clients("keystone").roles.remove_user_role(user,
                                                              role, tenant)

    @base.atomic_action_timer("keystone.get_tenant")
    def _get_tenant(self, tenant_id):
        """Get given tenant.

        :param tenant_id: tenant object
        """
        return self.admin_clients("keystone").tenants.get(tenant_id)

    @base.atomic_action_timer("keystone.get_user")
    def _get_user(self, user_id):
        """Get given user.

        :param user_id: user object
        """
        return self.admin_clients("keystone").users.get(user_id)

    @base.atomic_action_timer("keystone.get_role")
    def _get_role(self, role_id):
        """Get given user role.

        :param role_id: user role object
        """
        return self.admin_clients("keystone").roles.get(role_id)

    @base.atomic_action_timer("keystone.get_service")
    def _get_service(self, service_id):
        """Get service with given service id.

        :param service_id: id for service object
        """
        return self.admin_clients("keystone").services.get(service_id)

    def _get_service_by_name(self, name):
        for i in self._list_services():
            if i.name == name:
                return i

    @base.atomic_action_timer("keystone.delete_service")
    def _delete_service(self, service_id):
        """Delete service.

        :param service_id: service to be deleted
        """
        self.admin_clients("keystone").services.delete(service_id)

    @base.atomic_action_timer("keystone.update_tenant")
    def _update_tenant(self, tenant, name=None, description=None):
        """Update tenant name and description.

        :param tenant: tenant to be updated
        :param name: tenant name to be set
        :param description: tenant description to be set
        """
        name = name or (tenant.name + "_updated")
        description = description or (tenant.name + "_description_updated")
        self.admin_clients("keystone").tenants.update(tenant.id,
                                                      name, description)

    @base.atomic_action_timer("keystone.update_user_password")
    def _update_user_password(self, user_id, password):
        """Update user password.

        :param user_id: id of the user
        :param password: new password
        """
        self.admin_clients("keystone").users.update_password(user_id,
                                                             password)

    @base.atomic_action_timer("keystone.create_ec2creds")
    def _create_ec2credentials(self, user_id, tenant_id):
        """Create ec2credentials.

        :param user_id: User ID for which to create credentials
        :param tenant_id: Tenant ID for which to create credentials

        :returns: Created ec2-credentials object
        """
        return self.clients("keystone").ec2.create(user_id, tenant_id)

    @base.atomic_action_timer("keystone.list_ec2creds")
    def _list_ec2credentials(self, user_id):
        """List of access/secret pairs for a user_id.

        :param user_id: List all ec2-credentials for User ID

        :returns: Return ec2-credentials list
        """
        return self.clients("keystone").ec2.list(user_id)

    @base.atomic_action_timer("keystone.delete_ec2creds")
    def _delete_ec2credential(self, user_id, access):
        """Delete ec2credential.

        :param user_id: User ID for which to delete credential
        :param access: access key for ec2credential to delete
        """
        self.clients("keystone").ec2.delete(user_id, access)

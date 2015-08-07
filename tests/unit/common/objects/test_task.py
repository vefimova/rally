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

"""Tests for db.task layer."""

import json

import mock

from rally.common import objects
from rally import consts
from tests.unit import test


class TaskTestCase(test.TestCase):
    def setUp(self):
        super(TaskTestCase, self).setUp()
        self.task = {
            "uuid": "00ef46a2-c5b8-4aea-a5ca-0f54a10cbca1",
            "status": consts.TaskStatus.INIT,
            "verification_log": "",
        }

    @mock.patch("rally.common.objects.task.db.task_create")
    def test_init_with_create(self, mock_task_create):
        mock_task_create.return_value = self.task
        task = objects.Task(status=consts.TaskStatus.FAILED)
        mock_task_create.assert_called_once_with({
            "status": consts.TaskStatus.FAILED})
        self.assertEqual(task["uuid"], self.task["uuid"])

    @mock.patch("rally.common.objects.task.db.task_create")
    def test_init_without_create(self, mock_task_create):
        task = objects.Task(task=self.task)
        self.assertFalse(mock_task_create.called)
        self.assertEqual(task["uuid"], self.task["uuid"])

    @mock.patch("rally.common.objects.task.uuid.uuid4",
                return_value="some_uuid")
    @mock.patch("rally.common.objects.task.db.task_create")
    def test_init_with_fake_true(self, mock_task_create, mock_uuid4):
        task = objects.Task(fake=True)
        self.assertFalse(mock_task_create.called)
        self.assertTrue(mock_uuid4.called)
        self.assertEqual(task["uuid"], mock_uuid4.return_value)

    @mock.patch("rally.common.objects.task.db.task_get")
    def test_get(self, mock_task_get):
        mock_task_get.return_value = self.task
        task = objects.Task.get(self.task["uuid"])
        mock_task_get.assert_called_once_with(self.task["uuid"])
        self.assertEqual(task["uuid"], self.task["uuid"])

    @mock.patch("rally.common.objects.task.db.task_delete")
    @mock.patch("rally.common.objects.task.db.task_create")
    def test_create_and_delete(self, mock_task_create, mock_task_delete):
        mock_task_create.return_value = self.task
        task = objects.Task()
        task.delete()
        mock_task_delete.assert_called_once_with(
            self.task["uuid"], status=None)

    @mock.patch("rally.common.objects.task.db.task_delete")
    @mock.patch("rally.common.objects.task.db.task_create")
    def test_create_and_delete_status(self, mock_task_create,
                                      mock_task_delete):
        mock_task_create.return_value = self.task
        task = objects.Task()
        task.delete(status=consts.TaskStatus.FINISHED)
        mock_task_delete.assert_called_once_with(
            self.task["uuid"], status=consts.TaskStatus.FINISHED)

    @mock.patch("rally.common.objects.task.db.task_delete")
    def test_delete_by_uuid(self, mock_task_delete):
        objects.Task.delete_by_uuid(self.task["uuid"])
        mock_task_delete.assert_called_once_with(
            self.task["uuid"], status=None)

    @mock.patch("rally.common.objects.task.db.task_delete")
    def test_delete_by_uuid_status(self, mock_task_delete):
        objects.Task.delete_by_uuid(self.task["uuid"],
                                    consts.TaskStatus.FINISHED)
        mock_task_delete.assert_called_once_with(
            self.task["uuid"], status=consts.TaskStatus.FINISHED)

    @mock.patch("rally.common.objects.task.db.task_list",
                return_value=[{"uuid": "a",
                               "created_at": "b",
                               "status": consts.TaskStatus.FAILED,
                               "tag": "d",
                               "deployment_name": "some_name"}])
    def list(self, mock_db_task_list):
        tasks = objects.Task.list(status="somestatus")
        mock_db_task_list.assert_called_once_with("somestatus", None)
        self.assertIs(type(tasks), list)
        self.assertIsInstance(tasks[0], objects.Task)
        self.assertEqual(mock_db_task_list.return_value["uuis"],
                         tasks[0]["uuid"])

    @mock.patch("rally.common.objects.deploy.db.task_update")
    @mock.patch("rally.common.objects.task.db.task_create")
    def test_update(self, mock_task_create, mock_task_update):
        mock_task_create.return_value = self.task
        mock_task_update.return_value = {"opt": "val2"}
        deploy = objects.Task(opt="val1")
        deploy._update({"opt": "val2"})
        mock_task_update.assert_called_once_with(
            self.task["uuid"], {"opt": "val2"})
        self.assertEqual(deploy["opt"], "val2")

    @mock.patch("rally.common.objects.task.db.task_update")
    def test_update_status(self, mock_task_update):
        mock_task_update.return_value = self.task
        task = objects.Task(task=self.task)
        task.update_status(consts.TaskStatus.FINISHED)
        mock_task_update.assert_called_once_with(
            self.task["uuid"],
            {"status": consts.TaskStatus.FINISHED},
        )

    @mock.patch("rally.common.objects.task.db.task_update")
    def test_update_verification_log(self, mock_task_update):
        mock_task_update.return_value = self.task
        task = objects.Task(task=self.task)
        task.update_verification_log({"a": "fake"})
        mock_task_update.assert_called_once_with(
            self.task["uuid"],
            {"verification_log": json.dumps({"a": "fake"})}
        )

    @mock.patch("rally.common.objects.task.db.task_result_get_all_by_uuid",
                return_value="foo_results")
    def test_get_results(self, mock_task_result_get_all_by_uuid):
        task = objects.Task(task=self.task)
        results = task.get_results()
        mock_task_result_get_all_by_uuid.assert_called_once_with(
            self.task["uuid"])
        self.assertEqual(results, "foo_results")

    @mock.patch("rally.common.objects.task.db.task_result_create")
    def test_append_results(self, mock_task_result_create):
        task = objects.Task(task=self.task)
        task.append_results("opt", "val")
        mock_task_result_create.assert_called_once_with(
            self.task["uuid"], "opt", "val")

    @mock.patch("rally.common.objects.task.db.task_update")
    def test_set_failed(self, mock_task_update):
        mock_task_update.return_value = self.task
        task = objects.Task(task=self.task)
        task.set_failed()
        mock_task_update.assert_called_once_with(
            self.task["uuid"],
            {"status": consts.TaskStatus.FAILED, "verification_log": "\"\""},
        )

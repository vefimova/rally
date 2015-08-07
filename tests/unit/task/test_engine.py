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

"""Tests for the Test engine."""

import collections
import copy

import jsonschema
import mock

from rally import consts
from rally import exceptions
from rally.task import engine
from tests.unit import fakes
from tests.unit import test


class BenchmarkEngineTestCase(test.TestCase):

    def test_init(self):
        config = mock.MagicMock()
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, task)
        self.assertEqual(eng.config, config)
        self.assertEqual(eng.task, task)

    @mock.patch("rally.task.engine.jsonschema.validate")
    def test_validate(self, mock_validate):
        config = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, mock.MagicMock())
        mock_validate = mock.MagicMock()

        eng._validate_config_scenarios_name = mock_validate.names
        eng._validate_config_syntax = mock_validate.syntax
        eng._validate_config_semantic = mock_validate.semantic

        eng.validate()

        expected_calls = [
            mock.call.names(config),
            mock.call.syntax(config),
            mock.call.semantic(config)
        ]
        mock_validate.assert_has_calls(expected_calls)

    def test_validate__wrong_schema(self):
        config = {
            "wrong": True
        }
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, task)
        self.assertRaises(exceptions.InvalidTaskException,
                          eng.validate)
        self.assertTrue(task.set_failed.called)

    @mock.patch("rally.task.engine.jsonschema.validate")
    def test_validate__wrong_scenarios_name(self, mock_validate):
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(mock.MagicMock(), task)
        eng._validate_config_scenarios_name = mock.MagicMock(
            side_effect=exceptions.NotFoundScenarios)

        self.assertRaises(exceptions.InvalidTaskException, eng.validate)
        self.assertTrue(task.set_failed.called)

    @mock.patch("rally.task.engine.jsonschema.validate")
    def test_validate__wrong_syntax(self, mock_validate):
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(mock.MagicMock(), task)
        eng._validate_config_scenarios_name = mock.MagicMock()
        eng._validate_config_syntax = mock.MagicMock(
            side_effect=exceptions.InvalidBenchmarkConfig)

        self.assertRaises(exceptions.InvalidTaskException, eng.validate)
        self.assertTrue(task.set_failed.called)

    @mock.patch("rally.task.engine.jsonschema.validate")
    def test_validate__wrong_semantic(self, mock_validate):
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(mock.MagicMock(), task)
        eng._validate_config_scenarios_name = mock.MagicMock()
        eng._validate_config_syntax = mock.MagicMock()
        eng._validate_config_semantic = mock.MagicMock(
            side_effect=exceptions.InvalidBenchmarkConfig)

        self.assertRaises(exceptions.InvalidTaskException, eng.validate)
        self.assertTrue(task.set_failed.called)

    @mock.patch("rally.task.engine.base_scenario.Scenario")
    def test__validate_config_scenarios_name(self, mock_scenario):
        config = {
            "a": [],
            "b": []
        }
        mock_scenario.list_benchmark_scenarios.return_value = ["e", "b", "a"]
        eng = engine.BenchmarkEngine(config, mock.MagicMock())
        eng._validate_config_scenarios_name(config)

    @mock.patch("rally.task.engine.base_scenario.Scenario")
    def test__validate_config_scenarios_name_non_exsisting(self,
                                                           mock_scenario):
        config = {
            "exist": [],
            "nonexist1": [],
            "nonexist2": []
        }
        mock_scenario.list_benchmark_scenarios.return_value = ["exist", "aaa"]
        eng = engine.BenchmarkEngine(config, mock.MagicMock())

        self.assertRaises(exceptions.NotFoundScenarios,
                          eng._validate_config_scenarios_name, config)

    @mock.patch("rally.task.engine.runner.ScenarioRunner.validate")
    @mock.patch("rally.task.engine.context.ContextManager.validate")
    def test__validate_config_syntax(
            self, mock_context_manager_validate,
            mock_scenario_runner_validate):
        config = {"sca": [{"context": "a"}], "scb": [{"runner": "b"}]}
        eng = engine.BenchmarkEngine(mock.MagicMock(), mock.MagicMock())
        eng._validate_config_syntax(config)
        mock_scenario_runner_validate.assert_has_calls(
            [mock.call({}), mock.call("b")], any_order=True)
        mock_context_manager_validate.assert_has_calls(
            [mock.call("a", non_hidden=True), mock.call({}, non_hidden=True)],
            any_order=True)

    @mock.patch("rally.task.engine.runner.ScenarioRunner")
    @mock.patch("rally.task.engine.context.ContextManager.validate")
    def test__validate_config_syntax__wrong_runner(
            self, mock_context_manager_validate, mock_scenario_runner):
        config = {"sca": [{"context": "a"}], "scb": [{"runner": "b"}]}
        eng = engine.BenchmarkEngine(mock.MagicMock(), mock.MagicMock())

        mock_scenario_runner.validate = mock.MagicMock(
            side_effect=jsonschema.ValidationError("a"))
        self.assertRaises(exceptions.InvalidBenchmarkConfig,
                          eng._validate_config_syntax, config)

    @mock.patch("rally.task.engine.runner.ScenarioRunner.validate")
    @mock.patch("rally.task.engine.context.ContextManager")
    def test__validate_config_syntax__wrong_context(
            self, mock_context_manager, mock_scenario_runner_validate):
        config = {"sca": [{"context": "a"}], "scb": [{"runner": "b"}]}
        eng = engine.BenchmarkEngine(mock.MagicMock(), mock.MagicMock())

        mock_context_manager.validate = mock.MagicMock(
            side_effect=jsonschema.ValidationError("a"))
        self.assertRaises(exceptions.InvalidBenchmarkConfig,
                          eng._validate_config_syntax, config)

    @mock.patch("rally.task.engine.base_scenario.Scenario.validate")
    def test__validate_config_semantic_helper(self, mock_scenario_validate):
        deployment = mock.MagicMock()
        eng = engine.BenchmarkEngine(mock.MagicMock(), mock.MagicMock())
        eng._validate_config_semantic_helper("admin", "user", "name", "pos",
                                             deployment, {"args": "args"})
        mock_scenario_validate.assert_called_once_with(
            "name", {"args": "args"}, admin="admin", users=["user"],
            deployment=deployment)

    @mock.patch("rally.task.engine.base_scenario.Scenario.validate",
                side_effect=exceptions.InvalidScenarioArgument)
    def test__validate_config_semanitc_helper_invalid_arg(
            self, mock_scenario_validate):
        eng = engine.BenchmarkEngine(mock.MagicMock(), mock.MagicMock())

        self.assertRaises(exceptions.InvalidBenchmarkConfig,
                          eng._validate_config_semantic_helper, "a", "u", "n",
                          "p", mock.MagicMock(), {})

    @mock.patch("rally.task.engine.existing_users.ExistingUsers")
    def test_get_user_ctx_for_validation_existing_users(
            self, mock_existing_users):

        context = {"a": 10}
        users = [mock.MagicMock(), mock.MagicMock()]

        eng = engine.BenchmarkEngine(mock.MagicMock(), mock.MagicMock(),
                                     users=users)

        result = eng._get_user_ctx_for_validation(context)

        self.assertEqual(context["config"]["existing_users"], users)
        mock_existing_users.assert_called_once_with(context)

        self.assertEqual(mock_existing_users.return_value, result)

    @mock.patch("rally.task.engine.osclients.Clients")
    @mock.patch("rally.task.engine.users_ctx")
    @mock.patch("rally.task.engine.BenchmarkEngine"
                "._validate_config_semantic_helper")
    @mock.patch("rally.task.engine.objects.Deployment.get",
                return_value="FakeDeployment")
    def test__validate_config_semantic(
            self, mock_deployment_get,
            mock__validate_config_semantic_helper,
            mock_users_ctx, mock_clients):
        mock_users_ctx.UserGenerator = fakes.FakeUserContext
        mock_clients.return_value = mock.MagicMock()
        config = {
            "a": [mock.MagicMock(), mock.MagicMock()],
            "b": [mock.MagicMock()]
        }

        fake_task = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, fake_task)

        eng.admin = "admin"

        eng._validate_config_semantic(config)

        expected_calls = [
            mock.call("admin"),
            mock.call(fakes.FakeUserContext.user["endpoint"])
        ]
        mock_clients.assert_has_calls(expected_calls)

        mock_deployment_get.assert_called_once_with(fake_task["uuid"])

        admin = user = mock_clients.return_value
        fake_deployment = mock_deployment_get.return_value
        expected_calls = [
            mock.call(admin, user, "a", 0, fake_deployment, config["a"][0]),
            mock.call(admin, user, "a", 1, fake_deployment, config["a"][1]),
            mock.call(admin, user, "b", 0, fake_deployment, config["b"][0])
        ]
        mock__validate_config_semantic_helper.assert_has_calls(
            expected_calls, any_order=True)

    @mock.patch("rally.task.engine.BenchmarkEngine.consume_results")
    @mock.patch("rally.task.engine.context.ContextManager.cleanup")
    @mock.patch("rally.task.engine.context.ContextManager.setup")
    @mock.patch("rally.task.engine.base_scenario.Scenario")
    @mock.patch("rally.task.engine.runner.ScenarioRunner")
    def test_run__update_status(
            self, mock_scenario_runner, mock_scenario,
            mock_context_manager_setup, mock_context_manager_cleanup,
            mock_consume_results):
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine([], task)
        eng.run()
        task.update_status.assert_has_calls([
            mock.call(consts.TaskStatus.RUNNING),
            mock.call(consts.TaskStatus.FINISHED)
        ])

    @mock.patch("rally.task.engine.BenchmarkEngine.consume_results")
    @mock.patch("rally.task.engine.base_scenario.Scenario")
    @mock.patch("rally.task.engine.runner.ScenarioRunner")
    @mock.patch("rally.task.engine.context.ContextManager.cleanup")
    @mock.patch("rally.task.engine.context.ContextManager.setup")
    def test_run__config_has_args(
            self, mock_context_manager_setup, mock_context_manager_cleanup,
            mock_scenario_runner, mock_scenario,
            mock_consume_results):
        config = {
            "a.benchmark": [{"args": {"a": "a", "b": 1}}],
            "b.benchmark": [{"args": {"a": 1}}]
        }
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, task)
        eng.run()

    @mock.patch("rally.task.engine.BenchmarkEngine.consume_results")
    @mock.patch("rally.task.engine.base_scenario.Scenario")
    @mock.patch("rally.task.engine.runner.ScenarioRunner")
    @mock.patch("rally.task.engine.context.ContextManager.cleanup")
    @mock.patch("rally.task.engine.context.ContextManager.setup")
    def test_run__config_has_runner(
            self, mock_context_manager_setup, mock_context_manager_cleanup,
            mock_scenario_runner, mock_scenario, mock_consume_results):
        config = {
            "a.benchmark": [{"runner": {"type": "a", "b": 1}}],
            "b.benchmark": [{"runner": {"type": "c", "a": 1}}]
        }
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, task)
        eng.run()

    @mock.patch("rally.task.engine.BenchmarkEngine.consume_results")
    @mock.patch("rally.task.engine.base_scenario.Scenario")
    @mock.patch("rally.task.engine.runner.ScenarioRunner")
    @mock.patch("rally.task.engine.context.ContextManager.cleanup")
    @mock.patch("rally.task.engine.context.ContextManager.setup")
    def test_run__config_has_context(
            self, mock_context_manager_setup, mock_context_manager_cleanup,
            mock_scenario_runner, mock_scenario, mock_consume_results):
        config = {
            "a.benchmark": [{"context": {"context_a": {"a": 1}}}],
            "b.benchmark": [{"context": {"context_b": {"b": 2}}}]
        }
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, task)
        eng.run()

    @mock.patch("rally.task.engine.LOG")
    @mock.patch("rally.task.engine.BenchmarkEngine.consume_results")
    @mock.patch("rally.task.engine.base_scenario.Scenario")
    @mock.patch("rally.task.engine.runner.ScenarioRunner")
    @mock.patch("rally.task.engine.context.ContextManager.cleanup")
    @mock.patch("rally.task.engine.context.ContextManager.setup")
    def test_run_exception_is_logged(
            self, mock_context_manager_setup, mock_context_manager_cleanup,
            mock_scenario_runner, mock_scenario, mock_consume_results,
            mock_log):

        mock_context_manager_setup.side_effect = Exception

        config = {
            "a.benchmark": [{"context": {"context_a": {"a": 1}}}],
            "b.benchmark": [{"context": {"context_b": {"b": 2}}}]
        }
        task = mock.MagicMock()
        eng = engine.BenchmarkEngine(config, task)
        eng.run()

        self.assertEqual(2, mock_log.exception.call_count)

    @mock.patch("rally.task.engine.base_scenario.Scenario.meta")
    def test__prepare_context(self, mock_scenario_meta):
        default_context = {"a": 1, "b": 2}
        mock_scenario_meta.return_value = default_context
        task = mock.MagicMock()
        name = "a.benchmark"
        context = {"b": 3, "c": 4}
        endpoint = mock.MagicMock()
        config = {
            "a.benchmark": [{"context": {"context_a": {"a": 1}}}],
        }
        eng = engine.BenchmarkEngine(config, task)
        result = eng._prepare_context(context, name, endpoint)
        expected_context = copy.deepcopy(default_context)
        expected_context.setdefault("users", {})
        expected_context.update(context)
        expected_result = {
            "task": task,
            "admin": {"endpoint": endpoint},
            "scenario_name": name,
            "config": expected_context
        }
        self.assertEqual(result, expected_result)
        mock_scenario_meta.assert_called_once_with(name, "context")

    @mock.patch("rally.task.engine.base_scenario.Scenario.meta")
    def test__prepare_context_with_existing_users(self, mock_scenario_meta):
        mock_scenario_meta.return_value = {}
        task = mock.MagicMock()
        name = "a.benchmark"
        context = {"b": 3, "c": 4}
        endpoint = mock.MagicMock()
        config = {
            "a.benchmark": [{"context": {"context_a": {"a": 1}}}],
        }
        existing_users = [mock.MagicMock()]
        eng = engine.BenchmarkEngine(config, task, users=existing_users)
        result = eng._prepare_context(context, name, endpoint)
        expected_context = {"existing_users": existing_users}
        expected_context.update(context)
        expected_result = {
            "task": task,
            "admin": {"endpoint": endpoint},
            "scenario_name": name,
            "config": expected_context
        }
        self.assertEqual(result, expected_result)
        mock_scenario_meta.assert_called_once_with(name, "context")

    @mock.patch("rally.task.sla.SLAChecker")
    def test_consume_results(self, mock_sla_checker):
        mock_sla_instance = mock.MagicMock()
        mock_sla_checker.return_value = mock_sla_instance
        key = {"kw": {"fake": 2}, "name": "fake", "pos": 0}
        task = mock.MagicMock()
        config = {
            "a.benchmark": [{"context": {"context_a": {"a": 1}}}],
        }
        runner = mock.MagicMock()
        runner.result_queue = collections.deque([1, 2])
        is_done = mock.MagicMock()
        is_done.isSet.side_effect = [False, False, True]
        eng = engine.BenchmarkEngine(config, task)
        eng.duration = 123
        eng.full_duration = 456
        eng.consume_results(key, task, is_done, {}, runner)
        mock_sla_checker.assert_called_once_with({"fake": 2})
        expected_iteration_calls = [mock.call(1), mock.call(2)]
        self.assertEqual(expected_iteration_calls,
                         mock_sla_instance.add_iteration.mock_calls)

    @mock.patch("rally.task.sla.SLAChecker")
    def test_consume_results_sla_failure_abort(self, mock_sla_checker):
        mock_sla_instance = mock.MagicMock()
        mock_sla_checker.return_value = mock_sla_instance
        mock_sla_instance.add_iteration.side_effect = [True, True, False,
                                                       False]
        key = {"kw": {"fake": 2}, "name": "fake", "pos": 0}
        task = mock.MagicMock()
        config = {
            "a.benchmark": [{"context": {"context_a": {"a": 1}}}],
        }
        runner = mock.MagicMock()
        runner.result_queue = collections.deque([1, 2, 3, 4])
        is_done = mock.MagicMock()
        is_done.isSet.side_effect = [False, False, False, False, True]
        eng = engine.BenchmarkEngine(config, task, abort_on_sla_failure=True)
        eng.duration = 123
        eng.full_duration = 456
        eng.consume_results(key, task, is_done, {}, runner)
        mock_sla_checker.assert_called_once_with({"fake": 2})
        self.assertTrue(runner.abort.called)

    @mock.patch("rally.task.sla.SLAChecker")
    def test_consume_results_sla_failure_continue(self, mock_sla_checker):
        mock_sla_instance = mock.MagicMock()
        mock_sla_checker.return_value = mock_sla_instance
        mock_sla_instance.add_iteration.side_effect = [True, True, False,
                                                       False]
        key = {"kw": {"fake": 2}, "name": "fake", "pos": 0}
        task = mock.MagicMock()
        config = {
            "a.benchmark": [{"context": {"context_a": {"a": 1}}}],
        }
        runner = mock.MagicMock()
        runner.result_queue = collections.deque([1, 2, 3, 4])
        is_done = mock.MagicMock()
        is_done.isSet.side_effect = [False, False, False, False, True]
        eng = engine.BenchmarkEngine(config, task, abort_on_sla_failure=False)
        eng.duration = 123
        eng.full_duration = 456
        eng.consume_results(key, task, is_done, {}, runner)
        mock_sla_checker.assert_called_once_with({"fake": 2})
        self.assertEqual(0, runner.abort.call_count)

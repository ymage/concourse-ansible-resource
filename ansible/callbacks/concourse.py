#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# (c) 2017, Jose Riguera

__metaclass__ = type

from ansible import constants as C
from ansible.plugins.callback.default import CallbackModule as CallbackModuleDefault
from ansible.utils.display import Display
from datetime import datetime


class StderrDisplay(Display):

    def display(self, msg, *args, **kwargs):
        # Everything is displayed on stderr
        return super(StderrDisplay, self).display(msg, stderr=True, *args, **kwargs)


class CallbackModule(CallbackModuleDefault):
    '''
    This is the concourse callback plugin, which reuses the default
    callback plugin but sends output to stderr.
    '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'concourse'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self._display = StderrDisplay()
        self.start_time = datetime.now()

    def _human_runtime(self, runtime):
        minutes = (runtime.seconds // 60) % 60
        r_seconds = runtime.seconds - (minutes * 60)
        return runtime.days, runtime.seconds // 3600, minutes, r_seconds

    def v2_playbook_on_stats(self, stats):
        super(CallbackModule, self).v2_playbook_on_stats(stats)
        end_time = datetime.now()
        runtime = end_time - self.start_time
        self._display.display("Runtime: %s days, %s hours, %s minutes, %s seconds" % (self._human_runtime(runtime)))

    def v2_runner_on_failed(self, result, ignore_errors=False):

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        self._handle_exception(result._result, use_stderr=True)
        self._handle_warnings(result._result)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)

        else:
            if delegated_vars:
                self._display.display(
                    "fatal: [%s -> %s]: FAILED! => %s" % (result._host.get_name(), delegated_vars['ansible_host'],
                                                          self._dump_results(result._result)), color=C.COLOR_ERROR)
            else:
                self._display.display(
                    "fatal: [%s]: FAILED! => %s" % (result._host.get_name(), self._dump_results(result._result)),
                    color=C.COLOR_ERROR)

        if ignore_errors:
            self._display.display("...ignoring", color=C.COLOR_SKIP)

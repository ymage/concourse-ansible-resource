# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# concourse-ansible-resource - playbook_cli.py
# 03/04/2018


from collections import namedtuple

from ansible.cli import CLI
from ansible.errors import AnsibleError
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory.manager import InventoryManager
from ansible.module_utils._text import to_bytes
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import VaultSecret
from ansible.utils.vars import load_extra_vars, load_options_vars
from ansible.vars.manager import VariableManager

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()


class PlaybookCLI(CLI):
    DEFAULTS = {
        'subset': None,
        'ask_pass': False,
        'ask_vault_pass': False,
        'become': False,
        'become_ask_pass': False,
        'become_user': 'root',
        'become_method': 'sudo',
        'become_pass': None,
        'check': False,
        'connection': 'smart',
        'diff': False,
        'extra_vars': [],
        'flush_cache': False,
        'force_handlers': False,
        'forks': 5,
        'inventory': None,
        'listhosts': False,
        'listtags': False,
        'listtasks': False,
        'module_path': None,
        'new_vault_password_file': None,
        'output_file': None,
        'private_key_file': None,
        'remote_user': 'root',
        'remote_pass': None,
        'scp_extra_args': '',
        'sftp_extra_args': '',
        'skip_tags': [],
        'ssh_common_args': '',
        'ssh_extra_args': '',
        'start_at_task': None,
        'step': None,
        'syntax': False,  # None
        'tags': ['all'],
        'timeout': 10,
        'vault_password': None,
        'vault_password_file': None,
        'verbosity': 0,
    }

    def __init__(self, config, logger):
        super(self.__class__, self).__init__({})
        self.logger = logger
        options = dict(self.DEFAULTS)
        options.update(config)
        # del options_all['private_key_file']
        # del options_all['module_path']
        #  Convert dictionary to namedtuple 'Options'
        self.options = namedtuple('Options', options.keys())(**options)

    def parse(self):
        pass

    def run(self):
        rcode = 0
        playbook_path = self.options.playbook
        inventory_path = self.options.inventory
        vault_password = self.options.vault_password
        become_password = self.options.become_pass
        remote_password = self.options.remote_pass
        extra_vars = self.options.extra_vars
        # host_vars = None
        # group_vars = None
        passwords = {}

        # all needs loader
        loader = DataLoader()

        basedir = getattr(self.options, 'basedir', False)
        if basedir:
            loader.set_basedir(basedir)

        # create the inventory, and filter it based on the subset specified (if any)
        inventory = InventoryManager(loader=loader, sources=inventory_path)

        # create the variable manager, which will be shared throughout
        # the code, ensuring a consistent view of global variables
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        if extra_vars:
            variable_manager.extra_vars = load_extra_vars(loader=loader, options=self.options)

        if hasattr(self.options, 'basedir'):
            if self.options.basedir:
                variable_manager.safe_basedir = True
        else:
            variable_manager.safe_basedir = True

        if vault_password:
            loader.set_vault_secrets([('default', VaultSecret(_bytes=to_bytes(vault_password)))])

        if become_password is not None:
            passwords['become_pass'] = become_password
        if remote_password is not None:
            passwords['conn_pass'] = remote_password
        self.logger.info("Running playbook '%s': %s" % (playbook_path, self.options))

        # flush fact cache if requested
        if self.options.flush_cache:
            PlaybookCLI._flush_cache(inventory, variable_manager)

        # Setup playbook executor, but don't run until run() called
        playbook = PlaybookExecutor(
            playbooks=[playbook_path],
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=self.options,
            passwords=passwords
        )
        display.verbosity = self.options.verbosity

        # Results of PlaybookExecutor
        results = ""
        try:
            results = playbook.run()
        except AnsibleError as e:
            msg = "Error running playbook '%s': %s" % (playbook_path, str(e))
            self.logger.error(msg)
            rcode = 1
        else:
            self.logger.info("Done '%s'" % playbook_path)

        stats = playbook._tqm._stats
        return rcode, results, stats

    @staticmethod
    def _flush_cache(inventory, variable_manager):
        for host in inventory.list_hosts():
            hostname = host.get_name()
            variable_manager.clear_facts(hostname)

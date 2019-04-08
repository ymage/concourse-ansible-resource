# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# concourse-ansible-resource - ansible_playbook.py
# 03/04/2018

import os
import time
from io import StringIO
from resource import Resource
from tempfile import NamedTemporaryFile

from git import Repo
from playbook_cli import PlaybookCLI

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()


class AnsiblePlaybook(Resource):
    """Concourse resource implementation for ansible-playbook"""
    SOURCE = {
        # private_key
        "private_key_file": str,
        "remote_user": str,
        "remote_pass": str,
        "vault_password": str,
        "extra_vars": dict,
        "inventory": dict,
        "become": bool,
        "become_method": str,
        "become_user": str,
        "become_pass": str,
        "ssh_common_args": str,
        "forks": int,
        "tags": list,
        "skip_tags": list,
    }
    PARAMS = {
        # playbook
        "src": str,
        "playbook": str,
        "extra_vars": dict,
        "inventory": dict,
        "become": bool,
        "become_method": str,
        "become_user": str,
        "connection": str,
        "timeout": int,
        "ssh_common_args": str,
        "verbosity": int,
        "force_handlers": bool,
        "forks": int,
        "tags": list,
        "skip_tags": list,
    }
    DEFAULT_INVENTORY_FILE = "inventory.ini"
    DEFAULT_INVENTORY_PATH = "inventory"

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def _get_config_param(self, data, params={}):
        config = {}
        for p in params.keys():
            value = data.get(p)
            if value:
                value_type = params[p]
                if value_type is bool:
                    config[p] = str(value).lower() in ["true", "1", "yes", "y"]
                elif value_type is None:
                    config[p] = value
                else:
                    try:
                        config[p] = value_type(value)
                    except ValueError as e:
                        msg = "Cannot get config param '%s': %s" % (p, str(e))
                        self.logger.error(msg)
        return config

    def _hosts_group(self, name, data_group, output):
        """It Processes a inventory group. It can be a host (string),
        a list of hosts (list of strings) or a dictionary.
        """
        print("[%s]".format(name), file=output)
        if isinstance(data_group, dict):
            if "hosts" in data_group:
                for host in data_group['hosts']:
                    if isinstance(host, list):
                        print(' '.join(host), file=output)
                    else:
                        print(host, file=output)
            print('', file=output)
            if "vars" in data_group:
                print("[%s:vars]" % name, file=output)
                variables = data_group['vars']
                try:
                    for v in variables.keys():
                        print("%s='%s'" % (v, variables[v]), file=output)
                    print('', file=output)
                except Exception as e:
                    msg = "Inventory vars exception %s: '%s'" % (name, str(e))
                    self.logger.error(msg)
                print('', file=output)
            if "children" in data_group:
                print("[%s:children]" % name, file=output)
                for children in data_group['children']:
                    print(children, file=output)
                print('', file=output)
        elif isinstance(data_group, list):
            for host in data_group:
                if isinstance(host, list):
                    print(' '.join(host), file=output)
                else:
                    print(host, file=output)
            print('', file=output)
        else:
            print(data_group, file=output)
            print('', file=output)
        print('', file=output)

    def hosts(self, data, path, hosts_file):
        output = StringIO()
        if isinstance(data, dict):
            # inventory is (json) dictionary as specified in
            # http://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html
            self.logger.debug("Processing json inventory: '%s'" % repr(data))
            groups_children = [
                g for g in data.keys()
                if isinstance(data[g], dict) and 'children' in data[g]
            ]
            groups_leaf = [
                g for g in data.keys()
                if g not in groups_children
            ]
            for group in groups_children:
                self._hosts_group(group, data[group], output)
            for group in groups_leaf:
                self._hosts_group(group, data[group], output)
        elif isinstance(data, list):
            # inventory is a list of hosts
            self.logger.debug("Processing list inventory: '%s'" % repr(data))
            for host in data:
                if isinstance(host, list):
                    print(' '.join(host), file=output)
                else:
                    print(host, file=output)
        else:
            # inventory is something like "localhost"
            msg = "Processing simple str inventory: '%s'" % repr(data)
            self.logger.debug(msg)
            print(data, file=output)
        content = output.getvalue()
        inventory_path = os.path.join(path, hosts_file)
        try:
            with open(inventory_path, 'w') as f:
                f.write(content)
        except Exception as e:
            msg = "Cannot write inventory '%s': %s" % (inventory_path, str(e))
            self.logger.error(msg)
            raise
        else:
            output.close()
        return content

    def inventory(self, workfolder, source, params):
        output = None
        inventory = source.get('inventory', {})
        # Fixme! avoid overwriting
        inventory.update(params.get("inventory", {}))
        hosts = inventory.get("hosts")
        inventory_path = inventory.get("path", self.DEFAULT_INVENTORY_PATH)
        inventory_file = inventory.get("file")
        inventory_exec = inventory.get("executable")
        # TODO
        group_vars = inventory.get("group_vars")
        host_vars = inventory.get("host_vars")
        if inventory_exec:
            # dynamic inventory executable
            output = inventory_exec
        else:
            inventory_path = os.path.join(workfolder, inventory_path)
            if not os.path.exists(inventory_path):
                try:
                    os.makedirs(inventory_path)
                except Exception as e:
                    msg = "Cannot create inventory folder '%s': %s" % (inventory_path, str(e))
                    self.logger.error(msg)
                    raise
            if inventory_file:
                # Inventory is pointing directly to the ini file
                output = os.path.join(inventory_path, inventory_file)
            else:
                # Inventory is the full path
                # Just create a inventory file
                inventory_file = self.DEFAULT_INVENTORY_FILE
                output = inventory_path
            if hosts:
                self.hosts(hosts, inventory_path, inventory_file)
        return output

    def configure(self, workfolder, source, params):
        config = self._get_config_param(source, self.SOURCE)
        private_key_path = config.get("private_key_file")
        config_params = self._get_config_param(params, self.PARAMS)
        config.update(config_params)
        # Path
        build_path = config_params.get("src")
        if build_path:
            build_path = os.path.join(workfolder, build_path)
        else:
            build_path = os.path.join(workfolder, "src")
            git_ssh_identity_filename = os.path.expanduser("~/.ssh/id_rsa")
            git_ssh_identity_file = open(git_ssh_identity_filename, "w")
            git_ssh_identity_file.write(source.get("src_private_key"))
            git_ssh_identity_file.close()
            os.chmod(git_ssh_identity_filename, 0o600)
            Repo.clone_from(source.get("src_uri"), build_path, branch=source.get("src_branch", "master"))

        # Extra vars (just a dictionary)
        extra_vars = config.get("extra_vars", {})
        extra_vars.update(source.get("extra_vars", {}))
        config['extra_vars'] = [extra_vars]
        # Private key
        private_key = source.get("private_key")
        if private_key:
            try:
                tmp_file = NamedTemporaryFile(delete=False, suffix='.key')
                private_key_path = tmp_file.name
                with open(private_key_path, 'w') as f:
                    f.write(private_key)
            except Exception as e:
                msg = "Cannot create private key file: %s" % (str(e))
                self.logger.error(msg)
                raise
            config['private_key_file'] = private_key_path
        elif private_key_path:
            config['private_key_file'] = os.path.join(build_path, private_key_path)
        # Inventory
        config['inventory'] = self.inventory(build_path, source, params)
        # Playbook path
        playbook_path = params.get("playbook", "playbook.yml")
        playbook_path = os.path.join(build_path, playbook_path)
        if not os.path.isfile(playbook_path):
            msg = "Cannot find playbook file '%s'" % (playbook_path)
            self.logger.error(msg)
            raise ValueError(msg)
        config['playbook'] = playbook_path
        return config

    def summarize(self, stats):
        failed = []
        unreachable = []
        hosts = stats.processed.keys()
        for h in hosts:
            s = stats.summarize(h)
            if s["failures"] > 0:
                failed.append(h)
            if s["unreachable"] > 0:
                unreachable.append(h)
        result = {
            "hosts_all": hosts,
            "hosts_failed": failed,
            "hosts_unreachable": unreachable,
            "processed": stats.processed,
            "failures": stats.failures,
            "ok": stats.ok,
            "dark": stats.dark,
            "changed": stats.changed,
            "skipped": stats.skipped
        }
        self.logger.info("Playbook summary: %s" % (result))
        return result

    def metadata(self, rcode, result):
        if rcode == 0:
            statuscode = 0
            if len(result.get("hosts_failed", [])) > 0:
                statuscode = 2
            if len(result.get("hosts_unreachable", [])) > 0:
                statuscode = 3
        else:
            statuscode = rcode
        metadata = []
        for k in result.keys():
            metadata.append({"name": str(k), "value": str(result[k])})
        metadata.append({"name": "statuscode", "value": str(statuscode)})
        return statuscode, metadata

    def update(self, folder, source, params):
        config = self.configure(folder, source, params)
        exitcode, stdout, stats = PlaybookCLI(config, self.logger).run()
        result = self.summarize(stats)
        rcode, metadata = self.metadata(exitcode, result)
        timestamp = time.time()
        version = {"timestamp": str(timestamp)}
        rvalue = {"version": version, "metadata": metadata}
        return rcode, rvalue

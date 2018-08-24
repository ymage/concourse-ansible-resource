# Ansible [Concourse](http://concourse.ci) Resource

This is [Ansible](https://www.ansible.com) resource for [Concourse](http://concourse.ci)
to be able to execute Ansible playbooks from concourse.

This a pure Python implementation using the Ansible API. It does not use the binary commands
and it defines an output plugin to send the ansible execution logs to stderr as it is
required by concourse (see `ansible/callbacks/concourse.py`).

The ansible default configuration (in `/etc/ansible`) is defined in `ansible` folder.


## Source Configuration

Parameters available to use in the resource definition. None of then are required, but
probably you will need to setup `private_key`, `remote_user` and `inventory`:

* `private_key`: A string containing the ssh private key used for ssh connections.
* `remote_user`: Remote user used to establish a ssh connection.
* `remote_pass` : If `private_key` is not provided, password for `remote_user`.
* `vault_password`: Ansible vault password to access to encrypted files with variables.
* `extra_vars`: Key-value dictionary with variables used in the playbooks.
* `inventory`: Dictionary for inventory definition:
  * `file`: Defaults to `inventory.ini` file name for inventory.
  * `path`: Folder where the hosts inventory file will be created (if needed) and additional inventory files can be defined: group_vars and host_vars are. Defaults to `inventory`.
  * `hosts`: [Ansible inventory definition](http://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#script-conventions) specifying the hosts, hosts groups and variables.
  * `executable`: Path to a dynamic inventory executable.
* `become`: If true, execute playbooks as `become_user`. Usually not needed at this level.
* `become_method`: Ansible become method (defaults to `sudo`).
* `become_user`: User to run for privileged tasks (defaults to `root`).
* `become_pass`: Password in order to become `becomer_user` with `become_method`.
* `ssh_common_args`: ssh client additional arguments to establish ssh connections.
* `forks`: Number of parallel execution threads for hosts groups.
* `tags`: Limit playbook execution to only tasks tagged with this tags.
* `skip_tags`: Tasks of playbook with these tags will be skipped.


## Behavior

### `check`, `in`

Currently this resource only supports the `put` phase of a job plan, so these
are effectively no-ops. This will likely change in the future.

### `out`: Run an Ansible playbook

Run a an ansible playbook, sending the output to `stderr` by using a `concourse`
stdout plugin (defined in the default configuration `ansible/ansible.cfg`).

The parameters are almost the same as the ones in source, except `private_key`
and `playbook` (only in `out`).

#### Parameters

* `src`: Base folder where all the ansible resources are (inventory, playbook, ...)
* `playbook`: Playbook file name to execute.
* `remote_user`: Remote user used to establish a ssh connection.
* `remote_pass` : If `private_key` is not provided, password for `remote_user`.
* `vault_password`: Ansible vault password to access to encrypted files with variables.
* `extra_vars`: Key-value dictionary with variables used in the playbooks.
* `inventory`: Dictionary for inventory definition:
  * `file`: Defaults to `inventory.ini` file name for inventory.
  * `path`: Folder where the hosts inventory file will be created (if needed) and additional inventory files can be defined: group_vars and host_vars are. Defaults to `inventory`.
  * `hosts`: [Ansible inventory definition](http://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#script-conventions) specifying the hosts, hosts groups and variables.
  * `executable`: Path to a dynamic inventory executable.
* `become`: If true, execute playbooks as `become_user`. Usually not needed at this level.
* `become_method`: Ansible become method (defaults to `sudo`).
* `become_user`: User to run for privileged tasks (defaults to `root`).
* `become_pass`: Password in order to become `becomer_user` with `become_method`.
* `ssh_common_args`: ssh client additional arguments to establish ssh connections.
* `forks`: Number of parallel execution threads for hosts groups.
* `tags`: Limit playbook execution to only tasks tagged with this tags. (array)
* `skip_tags`: Tasks of playbook with these tags will be skipped.


## Example Pipeline

```yml
---
resource_types:
- name: ansible
  type: docker-image
  source:
    repository: platformengineering/concourse-ansible-resource

resources:
- name: ansible-playbook
  type: git
  source:
    uri: git@github.com:springerpe/repository.git
    branch: master
    private_key: {{github-private-key}}
- name: ansible-executor
  type: ansible
  source:
    private_key: {{ansible-private-key}}
    remote_user: ansible
    inventory:
      hosts:
        webservers:
        - host2.example.com
        - host3.example.com
        atlanta:
            hosts:
            - host1.example.com
            - host4.example.com
            - host5.example.com
            vars:
              b: false
            children:
            - marietta
        marietta:
        - host6.example.com

jobs:
- name: run-ansible
  plan:
  - get: ansible-playbook
  - put: ansible-executor
    params:
      src: ansible-playbook
      playbook: site.yml
```

Another pipeline example:

```yml
---
resource_types:
- name: ansible
  type: docker-image
  source:
    repository: platformengineering/concourse-ansible-resource

resources:
- name: ansible-playbook
  type: git
  source:
    uri: git@github.com:springernature/ee-ansible-ironic-standalone.git
    branch: master
    private_key: |
        -----BEGIN RSA PRIVATE KEY-----
        ..................................................................
        -----END RSA PRIVATE KEY-----

- name: ansible-executor
  type: ansible
  source:
    private_key: {{ansible-private-key}}
    remote_user: {{ansible-remote-user}}
    vault_password: {{ansible-vault-password}}
    debug: false
    tags:
      - packages
    inventory:
      path: inventory
      file: pe-prod-dogo-ironic-01.ini


jobs:
- name: run-ansible
  plan:
  - get: ansible-playbook
    params:
      submodules: all
  - put: ansible-executor
    params:
      src: ansible-playbook
      playbook: setup.yml
      verbosity: 0
```


##  Ansible playbook repo structure

This is an example of a playbook git repository:

```
.
├── playbook.yml
├── inventory
│   ├── static_inventory.ini
│   └── group_vars
│       └── group.yml
├── [roles]
│   ├── role1
│   └── role2
├── [tasks]
│   ├── task1.yml
│   └── task1.yml
├── [files]
│   └── file.bin
└── [vars]
    ├── secrets.yml
    └── other_vars.yml
```

# Authors

Jose Riguera <jose.riguera@springernature.com>
(c) 2017 Springer Nature Platform Engineering
Ymage <ymage@o2php.com>

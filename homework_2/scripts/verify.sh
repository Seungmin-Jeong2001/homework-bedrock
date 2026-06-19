#!/usr/bin/env bash
set -euo pipefail

ansible-playbook -i ansible/inventory.ini ansible/playbook-verify.yml

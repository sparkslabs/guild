#
# Provide a basic global value lookup service
#
# In particular, uses STM as the shared store, within a simple wrapper
#

from __future__ import print_function

# Avoid namespace pollution
from guild.stm import Store as _Store
from guild.stm import MAXFAIL as _MAXFAIL

services = None


def init():
    global services

    if services is None:
        services = _Store()


def register(key, value):
    try:
        repo = services.checkout()
        while repo.notcheckedin:
            with repo.changeset(key) as c:
                c[key].set(value)
    except _MAXFAIL as mf:
        print("TRANSACTION COMPLETELY FAILED")


def lookup(key):
    repo = services.using(key)
    return repo[key].value

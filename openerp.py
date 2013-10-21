"various utilities for working with OpenErp"

from __future__ import division, print_function

import openerplib
from .utils import PropertyDict
from .path import Path

execfile('/etc/openerp/VSS.conf')

# format of employee dbf file
#   login C(25)
#   password C(26)
#   emp_num N(6,0)
#   name C(50)
#   active L
#   groups C(50)
#   old_login C(25)
#   image_crc N(10,0)
#   email C(50)

try:
    with open(FILE_PATHS.db) as db:
        FILE_PATHS.db = db.readline().strip()
    del db
except Exception:
    pass

def adjust_permissions(oe_groups, allowed_groups, user):
    permissions = set(user.groups_id)
    for group_name, ints in oe_groups.items():
        if group_name.endswith('_default'):
            continue
        ints = set(ints)
        if group_name in allowed_groups:
            if not ints & permissions:  # add default if nothing already there
                permissions.add(oe_groups[group_name + '_default'][0])
        else:  # remove all priveleges for this group
            permissions -= ints
    return list(permissions)

def host_site(hostname, database, login='admin', password='admin'):
    hostname = {'wsg':'westernstatesglass.com','falcon':'falcon.tzo.com','salesinq':'demo.salesinq.com'}.get(hostname, hostname)
    result = PropertyDict()
    result.connection = conn = openerplib.get_connection(hostname=hostname, database=database, login=login, password=password)
    result.user_model = um = conn.get_model('res.users')
    users = um.read(um.search([('login','!=','""')]))
    users.extend(um.read(um.search([('login','!=','""'), ('active','!=','True')])))
    result.users = [PropertyDict(d) for d in users]
    result.group_model = gm = conn.get_model('res.groups')
    groups = gm.read(gm.search([('name','!=','""')]))
    result.groups = [PropertyDict(d) for d in groups]
    return result

def update_from_nightly():
    "routine to install nightly updates"
    # rename existing openerp out of the way

    # get list of possible .tar files from http://nightly.openerp.com/trunk/nightly/deb

    # download openerp_6.2dev-latest*.tar  (* may or may not be '-1')

    # extract contents of tar file, gathering exact folder name in the process

    # run the setup.py file that was extracted

    # update links from /home/ethan -> .../openerp

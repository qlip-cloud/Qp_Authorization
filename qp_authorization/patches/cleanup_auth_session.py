import frappe

def execute():
    con = frappe.db.sql

    keep = set()

    for r in con("select distinct coalesce(enviroment,'') e from tabqp_auth_session", as_dict=True):
        g = r['e']
        for s in con("select name from tabqp_auth_session where coalesce(enviroment,'')=%s order by creation desc limit 5", (g,), as_dict=True):
            keep.add(s['name'])

    for s in con("select name from tabqp_auth_session where expire_date > now()", as_dict=True):
        keep.add(s['name'])

    for s in con("select name from tabqp_auth_session order by creation desc limit 5", as_dict=True):
        keep.add(s['name'])

    keep_list = list(keep)

    if not keep_list:
        return

    escaped = ",".join("'%s'" % n.replace("'", "") for n in keep_list)

    antes = con("select count(*) c from tabqp_auth_session", as_dict=True)[0]['c']

    while True:
        remaining = con("select count(*) c from tabqp_auth_session", as_dict=True)[0]['c']
        if remaining <= len(keep_list):
            break
        con("delete from tabqp_auth_session where name not in (%s) limit 50000" % escaped)
        frappe.db.commit()

    final = con("select count(*) c from tabqp_auth_session", as_dict=True)[0]['c']

    print("cleanup qp_auth_session: {} -> {} (conserva {})".format(antes, final, len(keep_list)))

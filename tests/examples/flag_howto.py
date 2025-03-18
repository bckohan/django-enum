from .models.flag_howto import Group

group = Group.objects.create(
    permissions=(Group.Permissions.READ | Group.Permissions.EXECUTE)
)

group1 = Group.objects.create(
    permissions=(Group.Permissions.READ | Group.Permissions.EXECUTE)
)
group2 = Group.objects.create(
    permissions=Group.Permissions.RWX
)

assert Group.Permissions.READ in group1.permissions
assert Group.Permissions.WRITE not in group1.permissions
assert Group.Permissions.EXECUTE in group1.permissions

assert Group.Permissions.READ in group2.permissions
assert Group.Permissions.WRITE in group2.permissions
assert Group.Permissions.EXECUTE in group2.permissions
assert group2.permissions is Group.Permissions.RWX

# this will return both group1 and group2
read_or_write = Group.objects.filter(
    permissions__has_any=Group.Permissions.READ | Group.Permissions.WRITE
)
assert (
    group1 in read_or_write and
    group2 in read_or_write
)

# this will return only group2
read_and_write = Group.objects.filter(
    permissions__has_all=Group.Permissions.READ | Group.Permissions.WRITE
)
assert (
    group1 not in read_and_write and
    group2 in read_and_write
)

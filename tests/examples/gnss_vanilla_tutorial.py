from .models import GNSSReceiverBasic
from django.db.models import Q

receiver1 = GNSSReceiverBasic.objects.create(
    gps=True,
    glonass=True
)

receiver2 = GNSSReceiverBasic.objects.create(
    gps=True,
    glonass=True,
    galileo=True,
    beidou=True
)

# check for GPS and BEIDOU
assert not (receiver1.gps and receiver1.beidou)
assert receiver2.gps and receiver2.beidou

# get all receives that have at least GPS and BEIDOU
qry = GNSSReceiverBasic.objects.filter(Q(gps=True) & Q(beidou=True))
assert receiver1 not in qry
assert receiver2 in qry

# get all receivers that have either GPS or BEIDOU
qry = GNSSReceiverBasic.objects.filter(Q(gps=True) | Q(beidou=True))
assert receiver1 in qry
assert receiver2 in qry

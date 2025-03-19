from .models import GNSSReceiver, Constellation

receiver1 = GNSSReceiver.objects.create(
    constellations=Constellation.GPS | Constellation.GLONASS
)

receiver2 = GNSSReceiver.objects.create(
    constellations=(
        Constellation.GPS |
        Constellation.GLONASS |
        Constellation.GALILEO |
        Constellation.BEIDOU
    )
)

wanted = Constellation.GPS | Constellation.BEIDOU

# check for GPS and BEIDOU
assert not (
    Constellation.GPS in receiver1.constellations and
    Constellation.BEIDOU in receiver1.constellations
)
assert (    
    Constellation.GPS in receiver2.constellations and
    Constellation.BEIDOU in receiver2.constellations
)

# we can treat IntFlags like bit masks so we can also check for having at
# least GPS and BEIDOU like this:
assert not wanted & receiver1.constellations == wanted
assert wanted & receiver2.constellations == wanted

# get all receives that have at least GPS and BEIDOU
qry = GNSSReceiver.objects.filter(constellations__has_all=wanted)
assert receiver1 not in qry
assert receiver2 in qry

# get all receivers that have either GPS or BEIDOU
qry = GNSSReceiver.objects.filter(constellations__has_any=wanted)
assert receiver1 in qry
assert receiver2 in qry

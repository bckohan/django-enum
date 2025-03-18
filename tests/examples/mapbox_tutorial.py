from .models.mapbox import Map

map = Map.objects.create()

assert map.style.uri == 'mapbox://styles/mapbox/streets-v12'

# uri's are symmetric
map.style = 'mapbox://styles/mapbox/light-v11'
map.full_clean()
assert map.style is Map.MapBoxStyle.LIGHT

# comparisons can be made directly to symmetric property values
assert map.style == 3
assert map.style == 'light'
assert map.style == 'mapbox://styles/mapbox/light-v11'

# so are labels (also case insensitive)
map.style = 'satellite streets'
map.full_clean()
assert map.style is Map.MapBoxStyle.SATELLITE_STREETS

# when used in API calls (coerced to strings) - they "do the right thing"
assert str(map.style) == 'mapbox://styles/mapbox/satellite-streets-v12'

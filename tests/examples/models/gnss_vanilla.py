from django.db import models


class GNSSReceiverBasic(models.Model):

    gps = models.BooleanField(default=False)
    glonass = models.BooleanField(default=False)
    galileo = models.BooleanField(default=False)
    beidou = models.BooleanField(default=False)
    qzss = models.BooleanField(default=False)
    irnss = models.BooleanField(default=False)
    sbas = models.BooleanField(default=False)

    class Meta:

        # we can create an index for all fields, which will speed up queries for
        # exact matches on these fields
        indexes = [
            models.Index(fields=[
                'gps',
                'glonass',
                'galileo',
                'beidou',
                'qzss',
                'irnss',
                'sbas'
            ])
        ]

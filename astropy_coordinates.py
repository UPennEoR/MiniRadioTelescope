import datetime
import logging
if __name__ == '__main__':
    print('Running demo.')
    logging.basicConfig(level=logging.DEBUG)

logging.debug('Importing astropy library...')
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
from astropy.time import Time
from astropy import units as u

def get_penn_state_harrisburg_lat_lon(): return 40.2042 * u.deg, 76.7452 * u.deg
def get_here():
    lat, lon = get_penn_state_harrisburg_lat_lon()
    return EarthLocation(lat=lat, lon=lon)

def get_now():
    return Time.now()
    # or return Time(datetime.datetime.utcnow(), scale='utc')
    # BE VERY CAREFUL WITH TIME ZONES.
    # We are in UTC-5:00. To get universal time, take our local time and add 5 hours.
    # No. 1 cause of bugs.

# Downloading the sky coord by name takes a long time.
# Use the TrackedObject class to only download it once.
class TrackedObject:
    def __init__(self, sky_coord=None, name=None, location=None):
        if sky_coord is None:
            if name is None:
                raise Exception('You must give a sky_coord or a name to make a tracked object.')
            logging.debug('Downloading absolute location of {}...'.format(name))
            sky_coord = SkyCoord.from_name(name)

        self.name = name if not name is None else 'Unnamed sky object'
        self.sky_coord = sky_coord
        self.location = location

    # Returns an object with '.alt' and '.az' attributes indicating current position.
    # "Degrees" are of type astropy.units.degree;
    #  the plain float is exposed as the attribute ".value",
    #  like star.get_alt_az().az.value
    def get_alt_az(self, time=None):
        if self.location is None:
            raise Exception('You must set a location to find alt az on a TrackedObject.')
        logging.debug('Computing local position of {}...'.format(self.name))

        if time is None:
            time = get_now()

        frame = AltAz(obstime=time, location=self.location)
        return self.sky_coord.transform_to(frame)

def main():
    psh = get_here()

    altair = TrackedObject(name='Altair', location=psh)
    altaz = altair.get_alt_az()
    print()
    print('Current location of Altair in alt az as viewed from penn state harrisburg:')
    print('{} altitude, {} azimuth'.format(altaz.alt, altaz.az))
    print()

    sirius_sky_coord = SkyCoord(ra='6h45m8.917s', dec='-16d42m58.02s')
    sirius = TrackedObject(sky_coord=sirius_sky_coord, location=psh)
    sirius.name = 'Sirius'
    time = Time(datetime.datetime(2023, 11, 3, 20, 0, 0), scale='utc')
    altaz = sirius.get_alt_az(time)
    print()
    print('Location of Sirius on {}:'.format(time))
    print('{} altitude, {} azimuth'.format(altaz.alt, altaz.az))
    print()

if __name__ == '__main__':
    main()


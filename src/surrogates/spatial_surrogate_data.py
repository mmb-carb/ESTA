
class SpatialSurrogateData(object):
    """ This class is designed as a helper to make organizing the huge amount of spatial
        information we pull out of the spatial surrogate files easier.
        It is just a multiply-embedded dictionary with keys for things that we find in each file:
        region, vehicle type, and activity (VMT, Trips, etc).
    """

    def __init__(self):
        self.data = {}

    def init_regions(self, regions):
        """ Helper post-init method, to flush out the dictionary some """
        for region in regions:
            if region not in self.data:
                self.data[region] = {}

    def get(self, region, label):
        """ Getter method """
        return self.data.get(region, {}).get(label, None)

    def set(self, region, label, surrogate):
        """ Setter method """
        # type validation
        if type(surrogate) != SpatialSurrogate:
            raise TypeError('Only spatial surrogates can be used in SpatialSurrogateData.')

        # auto-fill the region, if it does not already exist
        if region not in self.data:
            self.data[region] = {}

        # add surrogate
        self.data[region][label] = surrogate

    def set_nocheck(self, region, label, surrogate):
        """ Setter method - no safety checking
            NOTE: This version of the method skips certain safety and type checking. It is faster,
                  but care must be taken to do these checks earlier in the code.
        """
        self.data[region][label] = surrogate

    def add_file(self, region, surrogate_dict):
        """ Setter method to add an entire dictionary of spatial surrogates to this object.
            The dict represents an entire input text file. So it has two layers of keys:
            vehicle type and activity type, then it has a spatial surrogate
        """
        for label in surrogate_dict:
            self.set(region, label, surrogate_dict[desc])

    def surrogates(self):
        """ Finally, normalize all the spatial surrogates, so the grid cells sum to 1.0. """
        for region in self.data:
            for label in self.data[region]:
                self.data[region][label] = self.data[region][label].surrogate()


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

    def get(self, region, veh, act):
        """ Getter method """
        return self.data.get(region, {}).get(veh, {}).get(act, None)

    def set(self, region, veh, act, surrogate):
        """ Setter method """
        # type validation
        if type(surrogate) != SpatialSurrogate:
            raise TypeError('Only spatial surrogates can be used in SpatialSurrogateData.')

        # auto-fill the mulit-level dictionary format, to hide this from the user
        if region not in self.data:
            self.data[region] = {}
            self.data[region][veh] = {}
        elif veh not in self.data[region]:
            self.data[region][veh] = {}

        # add surrogate
        self.data[region][veh][act] = surrogate

    def set_nocheck(self, region, veh, act, surrogate):
        """ Setter method - no safety checking
            NOTE: This version of the method skips certain safety and type checking. It is faster,
                  but care must be taken to do these checks earlier in the code.
        """
        # auto-fill the mulit-level dictionary format, to hide this from the user
        if veh not in self.data[region]:
            self.data[region][veh] = {}

        # add surrogate
        self.data[region][veh][act] = surrogate

    def add_file(self, region, surrogate_dict):
        """ Setter method to add an entire dictionary of spatial surrogates to this object.
            The dict represents an entire input text file. So it has two layers of keys:
            vehicle type and activity type, then it has a spatial surrogate
        """
        for veh in surrogate_dict:
            for act in surrogate_dict[veh]:
                self.set(region, veh, act, surrogate_dict[veh][act])

    def surrogates(self):
        """ Finally, normalize all the spatial surrogates, so the grid cells sum to 1.0. """
        for region in self.data:
            for veh in self.data[region]:
                for act in self.data[region][veh]:
                    self.data[region][veh][act] = self.data[region][veh][act].surrogate()

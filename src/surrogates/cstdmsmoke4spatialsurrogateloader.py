
from src.surrogates.smoke4spatialsurrogateloader import Smoke4SpatialSurrogateLoader


class CstdmSmoke4SpatialSurrogateLoader(Smoke4SpatialSurrogateLoader):
    ''' This class takes a simple list of EICs and a SMOKE v4 spatial surrogate file
        and creates an ESTA spatial surrogate.
        The SMOKE spatial surrogate format is well-documented and widely used.
    '''

    def __init__(self, config, position):
        super(CstdmSmoke4SpatialSurrogateLoader, self).__init__(config, position)

    def _create_veh_act_pairs(self, i):
        ''' create list of veh/act pairs for a given set of EICs '''
        # read list of EICs from file
        label = self.eic_labels[i]
        eics = sorted([eic for eic in self.eic2dtim4 if self.eic2dtim4[eic][1] == label])

        # adjust VMT and VHT-based surrogates
        if label[:3] in ['vmt', 'vht']:
            eics = sorted([eic for eic in self.eic2dtim4 if self.eic2dtim4[eic][1][:3] in ['vmt', 'vht']])

        veh_act_pairs = [self.eic2dtim4[eic] for eic in eics]

        # split VMT and VHT-based surrogates into 4 CSTDM time periods
        vmt_pairs = filter(lambda v: v[1][:3] in ['vmt', 'vht'], veh_act_pairs)
        for veh,act in vmt_pairs:
            for period in ['_off', '_am', '_mid', '_pm']:
                veh_act_pairs.append((veh, act + period))

        return veh_act_pairs

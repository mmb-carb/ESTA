
import gzip
import numpy as np
import os
import sys
from emfac2014csvloader import Emfac2014CsvLoader
from emissions_table import EmissionsTable


class Emfac2014HdDslCsvLoader(Emfac2014CsvLoader):

    def __init__(self, config, position):
        super(Emfac2014HdDslCsvLoader, self).__init__(config, position)
        self.hd_ld = 'hd'
        self.reverse_region_names = dict(zip(self.region_names.values(), self.region_names.keys()))
        #self.vtp2eic_lower = dict(((k[0].lower(),k[1].lower(),k[2].lower()),v) for k,v in self.vtp2eic.iteritems())

    def read_emfac_file(self, file_path, region=0):
        """ Read an EMFAC2021 HD Diesel CSV emissions file and colate the data into a table
            File Format:
            2021,Alameda (SF),0.000295677007427,NG,IDLEX,T7 Single Concrete/Transit Mix Class 8,CAT,TOG
        """
        emis_by_region = {}

        # check that the file exists
        if os.path.exists(file_path):
            f = open(file_path, 'r')
        elif os.path.exists(file_path + '.gz'):
            f = gzip.open(file_path + '.gz', 'rb')
        else:
            print('    + Emissions File Not Found: ' + file_path)
            return emis_by_region

        # now that file exists, read it
        f = open(file_path, 'r')
        for line in f.readlines():
            ln = line.rstrip().split(',')
            # is pollutant relevant
            poll = ln[-1].upper()
            if poll not in Emfac2014CsvLoader.VALID_POLLUTANTS:
                continue
            # pull EIC info
            fuel_type = ln[3]
            p = ln[4]
            v = ln[5]
            t = ln[6]
            eic = self.vtp2eic[(fuel_type, v, t, p)]
            if eic not in self.eic_info:
                raise KeyError('eic_info file does not include the EIC: ' + str(eic))
            # pull emissions value
            value = np.float32(ln[2]) * np.float32(self.eic_info[eic][2])
            if not value:
                continue
            # pull region info
            region_name = ln[1]
            if region_name in self.REGION_CORRECTION:
                region_name = self.REGION_CORRECTION[region_name]
            try:
                region = self.reverse_region_names[region_name]
            except KeyError:
                region = int(region_name)

            # fill output dictionary
            if region not in emis_by_region:
                emis_by_region[region] = EmissionsTable()

            # output DPM scenario
            if self.config['Output']['dpmout']:
                # check if eic_info.py has appended element for "is DPM eic?" (True/False)
                try:
                    is_dpm_eic = self.eic_info[eic][3]
                except:
                    sys.exit('\nERROR: "Run output DPM scenario?" is true, but eic_info file does not include "Is DPM eic?" field.\nCheck file: %s' % self.config['Surrogates']['eic_info'])
                # map PM/PM10/PM2.5 to DPM/DPM10/DPM2.5 and aggregate emissions
                if is_dpm_eic:
                    try:
                        dpmpoll = self.PM2DPM[poll]  # this can fail with non-DPM pollutants --> aggregate to criteria pollutant as normally done
                        # if DPM/DPM10/DPM2.5 has been identified in config file to output to ncf
                        if dpmpoll in self.dpm_polls:
                            emis_by_region[region][eic][dpmpoll] += value

                        if poll == 'PM':  # Add DPM to PM
                            emis_by_region[region][eic][poll] += value

                        elif poll == 'PM10':
                            emis_by_region[region][eic][poll] += value

                        elif poll == 'PM25':
                            emis_by_region[region][eic][poll] += value

                    # failed to map PM/PM10/PM2.5 to DPM/DPM10/DPM2.5 (pollutant is likely CO, TOG, NOX, SOX, etc.) --> aggregate to criteria pollutant as normally done
                    except:
                        emis_by_region[region][eic][poll] += value
                # not a DPM eic, therefore aggregate criteria pollutant as normally done
                else:
                    emis_by_region[region][eic][poll] += value
            # regular scenario (should only involve criteria pollutants)
            else:
                emis_by_region[region][eic][poll] += value

        f.close()
        return emis_by_region



def eic_reduce(config_str):
    ''' This function exists to help the user potentially reduce the level
        of detail of their outputs, by adjusting the collections of EICs
        available in the output.
        This currently supports:
            + all digits / unchanged EIC
            + first 3 digits of EIC
            + "EIC7" is first 3 digits of EIC plus EICMAT (fuel type)
    '''
    if config_str.lower() in [3, '3', 'three', 'eic3']:
        return eic14_to_eic3
    elif config_str.lower() in [7, '7', 'seven', 'eic7']:
        return eic14_to_eic7
    else:
        return nochange


def eic14_to_eic3(eic):
    ''' Takes an EIC14 integer and returns and EIC3 integer '''
    return int(eic / 1e11)


def eic14_to_eic7(eic):
    ''' Return the EIC3 and the EICMAT (fuel type) '''
    return int(eic / 1e4) - (int(eic / 1e8) - int(eic / 1e11) * 1000) * 10000


def nochange(eic):
    ''' Return the EIC as-is '''
    return eic

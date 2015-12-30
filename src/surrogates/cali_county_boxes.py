""" Grid Cell Boxes by County
    This is just a data file to provide a range of grid cells for each GAI.
    NOTE: The County numbers here are FIPS codes (1 to 115).
"""


county_boxes = {1: {'lon': xrange(130, 154), 'lat': xrange(152, 168)},
                2: {'lon': xrange(177, 195), 'lat': xrange(180, 193)},
                3: {'lon': xrange(158, 184), 'lat': xrange(160, 188)},
                4: {'lon': xrange(137, 162), 'lat': xrange(202, 229)},
                5: {'lon': xrange(159, 184), 'lat': xrange(162, 184)},
                6: {'lon': xrange(122, 146), 'lat': xrange(192, 209)},
                7: {'lon': xrange(128, 151), 'lat': xrange(159, 174)},
                8: {'lon': xrange(94, 113), 'lat': xrange(259, 280)},
                9: {'lon': xrange(156, 187), 'lat': xrange(180, 200)},
                10: {'lon': xrange(160, 220), 'lat': xrange(110, 160)},
                11: {'lon': xrange(119, 145), 'lat': xrange(204, 220)},
                12: {'lon': xrange(89, 115), 'lat': xrange(222, 266)},
                13: {'lon': xrange(271, 313), 'lat': xrange(23, 51)},
                14: {'lon': xrange(206, 281), 'lat': xrange(107, 157)},
                15: {'lon': xrange(176, 238), 'lat': xrange(80, 112)},
                16: {'lon': xrange(174, 196), 'lat': xrange(107, 130)},
                17: {'lon': xrange(115, 135), 'lat': xrange(185, 214)},
                18: {'lon': xrange(154, 185), 'lat': xrange(213, 263)},  # Lassen is extra North because of bad links
                19: {'lon': xrange(205, 238), 'lat': xrange(45, 85)},
                20: {'lon': xrange(169, 205), 'lat': xrange(133, 165)},
                21: {'lon': xrange(116, 134), 'lat': xrange(162, 180)},
                22: {'lon': xrange(172, 199), 'lat': xrange(144, 168)},
                23: {'lon': xrange(97, 125), 'lat': xrange(188, 226)},
                24: {'lon': xrange(153, 183), 'lat': xrange(132, 161)},
                25: {'lon': xrange(147, 184), 'lat': xrange(253, 279)},
                26: {'lon': xrange(186, 229), 'lat': xrange(154, 188)},
                27: {'lon': xrange(137, 180), 'lat': xrange(107, 142)},
                28: {'lon': xrange(124, 140), 'lat': xrange(171, 194)},
                29: {'lon': xrange(153, 184), 'lat': xrange(194, 212)},
                30: {'lon': xrange(224, 244), 'lat': xrange(42, 61)},
                31: {'lon': xrange(149, 184), 'lat': xrange(186, 206)},
                32: {'lon': xrange(149, 182), 'lat': xrange(210, 237)},
                33: {'lon': xrange(234, 312), 'lat': xrange(44, 69)},
                34: {'lon': xrange(140, 162), 'lat': xrange(167, 191)},
                35: {'lon': xrange(145, 171), 'lat': xrange(118, 143)},
                36: {'lon': xrange(231, 317), 'lat': xrange(55, 114)},
                37: {'lon': xrange(235, 275), 'lat': xrange(19, 50)},
                38: {'lon': xrange(126, 135), 'lat': xrange(159, 169)},
                39: {'lon': xrange(146, 165), 'lat': xrange(153, 179)},
                40: {'lon': xrange(151, 196), 'lat': xrange(82, 111)},
                41: {'lon': xrange(126, 139), 'lat': xrange(143, 163)},
                42: {'lon': xrange(166, 195), 'lat': xrange(66, 92)},
                43: {'lon': xrange(133, 158), 'lat': xrange(137, 157)},
                44: {'lon': xrange(130, 150), 'lat': xrange(136, 152)},
                45: {'lon': xrange(117, 157), 'lat': xrange(230, 257)},
                46: {'lon': xrange(158, 184), 'lat': xrange(204, 219)},
                47: {'lon': xrange(105, 155), 'lat': xrange(248, 280)},
                48: {'lon': xrange(129, 150), 'lat': xrange(168, 185)},
                49: {'lon': xrange(106, 134), 'lat': xrange(169, 195)},
                50: {'lon': xrange(148, 176), 'lat': xrange(143, 173)},
                51: {'lon': xrange(139, 154), 'lat': xrange(187, 206)},
                52: {'lon': xrange(117, 156), 'lat': xrange(215, 237)},
                53: {'lon': xrange(106, 134), 'lat': xrange(221, 262)},
                54: {'lon': xrange(190, 229), 'lat': xrange(107, 137)},
                55: {'lon': xrange(166, 201), 'lat': xrange(157, 182)},
                56: {'lon': xrange(191, 216), 'lat': xrange(56, 87)},
                57: {'lon': xrange(129, 152), 'lat': xrange(175, 196)},
                58: {'lon': xrange(146, 163), 'lat': xrange(192, 215)}}


county_boxes_lat_lon = {1: [37.44,-122.38, 37.91, -121.46],
                        2: [38.31, -120.18, 38.94, -119.5],
                        3: [38.20, -121.03, 38.71, -120.0],
                        4: [39.28, -122.1, 40.16, -121.0],
                        5: [37.82, -121.0, 38.52, -120.0],
                        6: [38.91, -122.79, 39.42, -121.79],
                        7: [37.71, -122.45, 38.10, -121.53],
                        8: [41.35, -124.61, 42.10, -123.50],
                        9: [38.50, -121.15, 39.07, -119.87],
                        10: [35.90, -120.92, 37.59, -118.35],
                        11: [39.37, -122.94, 39.80, -121.84],
                        12: [39.89, -124.61, 41.49, -123.40],
                        13: [32.51, -116.11, 33.49, -114.45],
                        14: [35.77, -118.80, 37.47, -115.63],
                        15: [34.78, -120.20, 35.80, -117.61],
                        16: [35.77, -120.32, 36.49, -119.47],
                        17: [38.66, -123.10, 39.59, -122.34],
                        18: [39.70, -121.34, 41.22, -119.90],
                        19: [33.67, -118.98, 34.88, -117.60],
                        20: [36.76, -120.55, 37.78, -119.02],
                        21: [37.79, -123.06, 38.37, -122.44],
                        22: [37.19, -120.40, 37.91, -119.30],
                        23: [38.67, -123.99, 40.09, -122.82],
                        24: [36.74, -121.25, 37.64, -120.05],
                        25: [41.15, -121.47, 42.05, -119.93],
                        26: [37.46, -119.66, 38.72, -117.83],
                        27: [35.74, -122.16, 36.99, -120.15],
                        28: [38.15, -122.65, 38.87, -122.06],
                        29: [39.00, -121.28, 39.53, -120.00],
                        30: [33.35, -118.14, 33.95, -117.40],
                        31: [38.71, -121.49, 39.32, -120.00],
                        32: [39.59, -121.50, 40.45, -120.09],
                        33: [33.42, -117.68, 34.08, -114.43],
                        34: [38.01, -121.87, 38.74, -121.02],
                        35: [36.19, -121.65,  36.99, -120.59],
                        36: [33.86, -117.81, 35.81, -114.13],
                        37: [32.55, -117.70, 33.51, -115.98],
                        38: [37.69, -122.53, 37.83, -122.35],
                        39: [37.48, -121.59, 38.31, -120.92],
                        40: [34.89, -121.64, 35.80, -119.37],
                        41: [36.97, -122.70, 37.83, -122.08],
                        42: [33.70, -121.15, 35.12, -118.96],
                        43: [36.89, -122.21, 37.49, -121.20],
                        44: [36.79, -122.35, 37.29, -121.58],
                        45: [40.28, -123.07, 41.19, -121.31],
                        46: [39.39, -121.06, 39.78, -120.00],
                        47: [40.99, -123.72, 42.01, -121.44],
                        48: [38.03, -122.41, 38.54, -121.59],
                        49: [38.07, -123.65, 38.86, -122.34],
                        50: [37.13, -121.49, 38.08, -120.38],
                        51: [38.73, -121.95, 39.31, -121.41],
                        52: [39.79, -123.07, 40.46, -121.34],
                        53: [39.97, -123.63, 41.37, -122.44],
                        54: [35.78, -119.58, 36.75, -117.98],
                        55: [37.63, -120.66, 38.44, -119.19],
                        56: [33.97, -119.50, 34.91, -118.58],
                        57: [38.31, -122.43, 38.93, -121.50],
                        58: [38.91, -121.64, 39.64, -121.00]}


def get_lat_lon_box(counties):
    """ Just a quick way to get a rough lat/lon box
        for a collection of California counties,
        given their FIPS codes.
    """
    # If there area  lot of counties, just return the whole state
    if len(counties) > 10:
        min_lat = 32.25
        max_lat = 42.0
        min_lon = -124.55
        max_lon = -113.0
        return (min_lat, min_lon, max_lat, max_lon)

    min_lat = 999.0
    max_lat = -999.0
    min_lon = 999.0
    max_lon = -999.0
    for county in counties:
        corners = county_boxes_lat_lon[county]
        if corners[0] < min_lat:
            min_lat = corners[0]
        if corners[1] < min_lon:
            min_lon = corners[1]
        if corners[2] > max_lat:
            max_lat = corners[2]
        if corners[3] > max_lon:
            max_lon = corners[3]

    return (min_lat, min_lon, max_lat, max_lon)


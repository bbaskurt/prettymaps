"""
Prettymaps - A minimal Python library to draw pretty maps from OpenStreetMap Data
Copyright (C) 2021 Marcelo Prates

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

#import vsketch
import argparse
from prettymaps import *
from matplotlib import pyplot as plt
import os

import prettymaps

#plot = prettymaps.plot('Regents Park, London, United Kingdom')

#plot.show()

from matplotlib.font_manager import FontProperties

def process_location(location, output, lite, radius):
    result = [x.strip() for x in location.split(',')]
    title = result[0]

    print("Creating " + title + "...")
    '''plot = prettymaps.plot(
        (41.39491,2.17557),
        preset = 'barcelona',
    )'''

    if lite:
        plot = prettymaps.plot(
            location,
            circle = True,
            radius = int(radius),
            layers = {
                "green": {
                    "tags": {
                        "landuse": "grass",
                        "natural": ["island", "wood"],
                        "leisure": "park"
                    }
                },
                "forest": {
                    "tags": {
                        "landuse": "forest"
                    }
                },
                "water": {
                    "tags": {
                        "natural": ["water", "bay"]
                    }
                },
                "parking": {
                    "tags": {
                        "amenity": "parking",
                        "highway": "pedestrian",
                        "man_made": "pier"
                    }
                },
                "streets": {
                    "width": {
                        "motorway": 5,
                        "trunk": 5,
                        "primary": 4.5,
                        "secondary": 4,
                        "tertiary": 3.5,
                        "residential": 3,
                    }
                },
                "building": {
                    "tags": {"building": True},
                },
            },
            style = {
                "background": {
                    "fc": "#F2F4CB",
                    "ec": "#dadbc1",
                    "hatch": "ooo...",
                },
                "perimeter": {
                    "fc": "#F2F4CB",
                    "ec": "#dadbc1",
                    "lw": 0,
                    "hatch": "ooo...",
                },
                "green": {
                    "fc": "#D0F1BF",
                    "ec": "#2F3737",
                    "lw": 1,
                },
                "forest": {
                    "fc": "#64B96A",
                    "ec": "#2F3737",
                    "lw": 1,
                },
                "water": {
                    "fc": "#a1e3ff",
                    "ec": "#2F3737",
                    "hatch": "ooo...",
                    "hatch_c": "#85c9e6",
                    "lw": 1,
                },
                "parking": {
                    "fc": "#F2F4CB",
                    "ec": "#2F3737",
                    "lw": 1,
                },
                "streets": {
                    "fc": "#2F3737",
                    "ec": "#475657",
                    "alpha": 1,
                    "lw": 0,
                },
                "building": {
                    "palette": [
                        "#FFC857",
                        "#E9724C",
                        "#C5283D"
                    ],
                    "ec": "#2F3737",
                    "lw": 0.5,
                }
            }
        )
    else:
        plot = prettymaps.plot(
            #'Regent Park, London, United Kingdom',
            location,
            circle = True,
            radius = 1100,
            #credit = False,
            #title = 'Regent Park',
            dilate = 0,
            #rotation = 90
            #radius = false
            style = {
                "background": {
                    "fc": "#F2F4CB",
                    "ec": "#dadbc1",
                    "hatch": "ooo...",
                }
            },
        )

    xmin, xmax, ymin, ymax = plt.axis()
    #print(xmin, xmax, ymin, ymax)

    # Change background color
    plot.fig.patch.set_facecolor('#F2F4CB')
    # Add title
    '''plot.ax.set_title(
        'Regent Park',
        x=696877,
        y=5713791,
        verticalalignment="bottom",
        fontproperties = FontProperties(
            fname = './assets/PermanentMarker-Regular.ttf',
            size = 50
        )
    )'''
    '''plot.ax.set_title(
        'Barcelona',
        size = 50
    )'''
    plt.text((xmax+xmin)/2, ymin+((ymax-ymin)*0.05), title, horizontalalignment='center', fontproperties = FontProperties(
            fname = './assets/PermanentMarker-Regular.ttf',
            size = 25
            ))

    #plt.text((xmax+xmin)/2, ymin, 'Plaza del Sol', fontsize=30)

    #print("Plotting map...")

    #plt.show()
    if output:
        title = output
    else:
        title = title.replace(" ", "_")
        title = title + "_r" + radius
        if lite:
            title = title + '_lite'
        
        title = title + '.png'
        title = os.path.join('maps', title)
    plt.savefig(title, dpi=500)
    print("Map saved: " + title)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--location", help="place, city, country")

    parser.add_argument(
        "--bulk", help="File path containing list of the locations")

    parser.add_argument(
        "--radius", help="Radius of the map in meters",
        default=1100)

    parser.add_argument(
        "--output", help="Output file name. i.e. Regent_Park.png")

    parser.add_argument(
        "--lite", help="Activate the mode that has lite color tones",
        default = True)

    args = parser.parse_args()

    print("location: ", args.location)
    print("bulk: ", args.bulk)
    print("radius: ", args.radius)
    print("output: ", args.output)
    print("lite: ", args.lite)

    #location = 'Plaza del Sol, Madrid, Spain'
    location = args.location
    # process all the location provided by a file. Each line is a separate location in the file.
    if args.bulk:
        with open(args.bulk) as file:
            lines = [line.rstrip() for line in file]
            for line in lines:   
                try:
                    process_location(line, args.output, args.lite, args.radius)
                except:
                    print("Could not process location: ", line) 
    else:
        # generate map of a single location
        process_location(location, args.output, args.lite, args.radius)


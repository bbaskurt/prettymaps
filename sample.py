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

import prettymaps

#plot = prettymaps.plot('Regents Park, London, United Kingdom')

#plot.show()

from matplotlib.font_manager import FontProperties

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--location", help="place, city, country")

    parser.add_argument(
        "--bulk", help="File path containing list of the locations")

    args = parser.parse_args()

    print("location: ", args.location)
    print("bulk: ", args.bulk)


    #location = 'Plaza del Sol, Madrid, Spain'
    location = args.location
    result = [x.strip() for x in location.split(',')]
    title = result[0]

    print("Creating map...")
    '''plot = prettymaps.plot(
        (41.39491,2.17557),
        preset = 'barcelona',
    )'''

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

    print("map created!")

    xmin, xmax, ymin, ymax = plt.axis()
    print(xmin, xmax, ymin, ymax)

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

    print("Plotting map...")

    #plt.show()
    title = title.replace(" ", "_")
    plt.savefig(title + '.png', dpi=500)
    print("Image saved...")

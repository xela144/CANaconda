#!/usr/bin/env python3
'''
 * Copyright Alex Bardales 2015
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses.
'''

'''
This is the matplotlib plotting program that takes
CSV formatted input from stdin and plots in real time.
Currently, the code loops for up to 200 iterations of
main While loop, then restarts. This can be altered by
a command line argument that gives the upper bound
for the np.arange array called xx.
For this code to work, it is necessary for the first
line of the CSV input to be the axis labels: 'X_LABEL,Y_LABEL'
It should be decided how many columns can be plotted, and
whether that is done on a single plot, or on subplots, and
what should be the best method for obtaining axis limits,
tick intervals, etc.
'''

import sys
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pdb
import time


def main():
    if sys.stdin.isatty():
        pdb.set_trace()

    plt.xkcd()
    xx = np.arange(0, 20, 0.2)
    yy = np.zeros(xx.size)
    fig = plt.figure()
    ax = fig.add_subplot(111)

    #get axes labels
    while True:  # will it wait for readline without try except block?
        try:
            labels = sys.stdin.readline().split(',')
            print(labels)
            # more code follows below...
            break
        except:
            pass
#    if len(labels) > 0:
#        if labels[0] == 't':
#            xlabel = 'time'
#            ylabel = labels[1][:-1] # because of the \n at the end
#            print(xlabel,ylabel)
#    else:
#        ylabel = labels[0]
#    plt.xlabel(xlabel)
#    plt.ylabel(ylabel)
    ax.axes.set_xlim(0, 20)
    ax.axes.set_ylim(0, 3)
    #ax.text(5, 1.5,
    #        ("First iteration of csv plotter"),
    #         size=16)
    line, = ax.plot(xx, yy, 'r-', animated=True)
    fig.show()
    fig.canvas.draw()
    background = fig.canvas.copy_from_bbox(ax.bbox)
    i = 0
    while True:
        this_line = sys.stdin.readline()
        if this_line == '':
            time.sleep(5)
        blob = this_line.split(',')
        if len(blob) < 2:
            print("error: bloblen =",len(blob))
        else:
            yy[i] = blob[1]
            print(yy[i])
            #restore canvas, then blit
            fig.canvas.restore_region(background)
            line.set_ydata(yy)
            ax.draw_artist(line)
            fig.canvas.blit(ax.bbox)
            i += 1
            if i > yy.size - 1:
                i = 0

    return 0

if __name__ == '__main__':
    sys.exit(main())

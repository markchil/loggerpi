#!/usr/bin/python3

# Copyright 2019 Mark Chilenski
# This program is distributed under the terms of the GNU General Purpose
# License (GPL).
# Refer to http://www.gnu.org/licenses/gpl.txt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from loggerpi import DataHandler, PlotHandler

data_handler = DataHandler()
data_handler.update_trend()
plot_handler = PlotHandler(data_handler)
plot_handler.update_plot()

webpage = """<!DOCTYPE html>
<html>
<head>
    Temperature Logger 1
    <style>
        * {
            margin: 0;
            padding: 0;
        }
        .imgbox {
            display: grid;
            height: 100%;
        }
        .center-fit {
            max-width: 100%;
            max-height: 100vh;
            margin: auto;
        }
    </style>
</head>
<body>
    <div class="imgbox">
        <img class="center-fit" src="/files/temperature.png" />
    </div>
</body>
</html>
"""
print(webpage)

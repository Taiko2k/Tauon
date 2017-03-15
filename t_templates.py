# Tauon Music Box - HTML templates for web interface

# Copyright © 2015-2016, Taiko2k captain(dot)gxj(at)gmail.com

#     This file is part of Tauon Music Box.
#
#     Tauon Music Box is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Tauon Music Box is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.
#
#    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE

from string import Template

remote_template = Template("""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Tauon Remote</title>

<style>
body {background-color:#1A1A1A;
font-family:sans-serif;
}
p {
color:#D1D1D1;
font-family:sans-serif;
 }
a {
color:#D1D1D1;
font-family:sans-serif;
 }
l {
color:#737373;
font-family:sans-serif;
font-size: 85%;
 }
</style>
<link rel="icon" href="/favicon.ico" type="image/x-icon" />
</head>

<body>

<div style="width:100%;">
<div style="float:left; width:50%;">

<p>

<a href="/remote/downplaylist">Previous Playlist </a> &nbsp
$pline  &nbsp
<a href="/remote/upplaylist">Next Playlist</a>
<br><br> <br> &nbsp; &nbsp; &nbsp;Now Playing: $play

$image

<br> <br> <br><br> <br> <br><br> <br> <br><br> <br> <br> <br> <br> <br> <br>
<a href="/remote/pause">Pause</a>
<a href="/remote/play">Play</a>
<a href="/remote/stop">Stop</a>
&nbsp;
<a href="/remote/back">Back</a>
<a href="/remote/forward">Forward</a>

<br> <br>
<a href="/remote/random">Random</a>  $isran
<br> <br>
<a href="/remote/repeat">Repeat</a> $isrep

<br> <br>
<a href="/remote/vup">Vol +</a>
<a href="/remote/vdown">Vol -</a>
&nbsp; &nbsp;
<br><br> Seek [ $seekbar ]
<br>

<br>
<a href="/remote">Reload</a>


</div>
<div style="float:left; ">

<br><br>
<a href="/remote/pl-up" STYLE="text-decoration: none">Up</a>
<br><br>
$list
<br>
<a href="/remote/pl-down" STYLE="text-decoration: none">Down</a>

</p>
</div>
</div>

</body>

</html>
""")

radio_template = Template("""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Radio Album Art</title>

<style>
body {background-color:#1A1A1A;
font-family:sans-serif;
}
p {
color:#D1D1D1;
font-family:sans-serif;
 }
</style>
<link rel="icon" href="/favicon.ico" type="image/x-icon" />
</head>

<body>
<br>
<p><br> <br> <br>
$image
<br> <br>  &nbsp; &nbsp; &nbsp; $play
</p>
</body>

</html>
""")

sample_template = Template("""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Track Preview</title>

<style>
body {background-color:#1A1A1A;
font-family:sans-serif;
}
p {
color:#D1D1D1;
font-family:sans-serif;
 }
</style>
<link rel="icon" href="/favicon.ico" type="image/x-icon" />
</head>

<body>
<br>
<p><br> <br> <br>
$image
<br> <br>  &nbsp; &nbsp; &nbsp; $play
</p>
</body>

</html>
""")
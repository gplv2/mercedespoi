# Building:
    qmake -project
    qmake -makefile 
    make all

# mercedespoi
Convert real GPX files to the extentions abomination of them known as Mercedes-Benz format 

This tool converts plain GPX files of a certain format into a version of GPX that is readable by a mercedes benz COMAND online 

only tested on the car I own , which is a C-class W205 (2014).  It works perfectly there but this tool needs adaptations to allow Openstreetmap exports
as a source of speed camera's and 30-zones.

Will document as much as I can while making it compatible.

# GPX sources

This tool is written to use OSM GPX export files made via Overpass API.  The idea is to run the overpass query below on the area of interest.  After downloading the GPX export, you need to lint it using xmllint so proper line endings are put consistently in the same spots.  It's a shortcoming in the code to assume \r\n is put at the right places.  Hence after downloading run this xmllint command

    xmllint --format --pretty 1 download.gpx > pretty_download.gpx

# Overpass query

You can play with this query, even make a more advanced one to split speed camera's from redlight ones.  Here in Belgium almost all camera's have a dual function, speed and redlight detection.

    <query type="node">
        <bbox-query {{bbox}}/>
        <has-kv k="highway" v="speed_camera"/>
    </query>
    <print mode="meta"/>  

If you want to split the maxspeeds you'll have to create more than 1 file.  The hard limit is 30 000 according to multiple sources, so you might focus on the countries you actually will visit instead of the whole of Europe/USA.

After linting , use this tool to create a GPX that your Benz will be able to import.  Put this on an SD card


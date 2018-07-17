#include <stdio.h>    /* Standard input/output definitions */
#include <stdlib.h>
#include <stdint.h>   /* Standard types */
#include <string.h>   /* String function definitions */
#include <unistd.h>   /* UNIX standard function definitions */
#include <fcntl.h>    /* File control definitions */
#include <errno.h>    /* Error number definitions */

#include <QFile>
#include <QString>
#include <QTextStream>

int main(int argc, char **argv)
{
    QString in_file, out_file;
    QString header1 = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n";
    QString header2 = "<gpx:gpx creator=\"\" version=\"1.1\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:gpx=\"http://www.topografix.com/GPX/1/1\" xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd\" xmlns:gpxd=\"http://www.daimler.com/DaimlerGPXExtensions/V2.4\">\n";
    // IconID="6" gives a camera icon - however 7, a red heart shows up far better - but this can be changed using Comand
    QString header3 = "\t\t<gpx:extensions><gpxd:WptExtension><gpxd:WptIconId IconId=\"6\"></gpxd:WptIconId>\n";
    QString header4 = "\t\t<gpxd:POICategory Cat=\"Speedcamera\"></gpxd:POICategory>\n";
    QString header5 = "\t\t<gpxd:Activity Active=\"true\" Level=\"warning\" Unit=\"second\" Value=\"50\"></gpxd:Activity>\n";
    QString header6 = "\t\t<gpxd:Presentation ShowOnMap=\"true\"></gpxd:Presentation>\n";

    QString footer1 = "\t</gpxd:WptExtension>\n\t</gpx:extensions>\n\t</gpx:wpt>\n";
    QString footer2 = "</gpx:gpx>\n";

    QString str, str2, str3;
    int x, y;
    bool bStarted = false;

    if(argc < 2)
    {
        puts("Usage: Comand-convert input-file.gpx output-file.gpx");
        return(1);
    }

    QFile inf(in_file = argv[1]);
    QFile outf(out_file = argv[2]);

    if ( inf.open( QIODevice::ReadOnly ) && outf.open( QIODevice::WriteOnly) )
    {
        QTextStream instream( &inf);
        QTextStream outstream( &outf);

        outstream << header1 << header2;

        while(!instream.atEnd())
        {
            str = instream.readLine();
            if (str.contains("lat="))
            {
                if(bStarted)
                    outstream << footer1;
                else
                    bStarted = true;

                x = (str.indexOf("lat=") );
                y = (str.indexOf(">"));
                str2 = str.mid(x, y - x);
                str3 = "\t<gpx:wpt " + str2 + ">\n\t<gpx:name>\"";

                str = instream.readLine();  // is next line down

                x = str.indexOf(">") + 1;
                y = str.indexOf("</");
                str2 = str.mid(x, y - x);

                str3 = str3 + str2 + "\"</gpx:name>\n";
                outstream << str3;
                outstream << header3 << header4 << header5 << header6;
            }
            else if(str.contains("StreetAddress>"))
            {
                x = (str.indexOf("StreetAddress>") + 14);
                y = (str.indexOf("</gpxx:StreetAddress>") );
                str2 = str.mid(x, y - x);
                str3 = "\t\t<gpxd:Address ISO=\"GB\" Country=\"GREAT BRITAIN\" State=\"\" City=\"\" CityCenter=\"\" Street=\"" + str2 + "\" Street2=\"\" HouseNo=\"\" ZIP=\"\"/>\n";
                outstream << str3;
            }
        }
        outstream << footer1 << footer2;
        inf.close();
        outf.close();
    }
    else
    {
        puts("Error: Unable open a specified file");
        return(1);
    }

    return(0);
}

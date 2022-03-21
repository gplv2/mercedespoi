fetch("https://overpass-api.de/api/interpreter", {
  "headers": {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "Referer": "https://overpass-turbo.eu/",
    "Referrer-Policy": "strict-origin-when-cross-origin"
  },
  "body": "data=%3C%3Fxml+version%3D%221.0%22+encoding%3D%22UTF-8%22%3F%3E%3C!--%0AThis+query+looks+for+nodes%2C+ways+and+relations+%0Awith+the+given+key+present%0AChoose+your+region+and+hit+the+Run+button+above!%0A--%3E%0A%0A%0A%0A%0A%3Cosm-script+output%3D%22gpx%22%3E%0A++%3C!--+fetch+area+%E2%80%9Cbelgium%E2%80%9D+to+search+in+--%3E%0A++%3Cid-query+type%3D%22area%22+ref%3D%223600052411%22+into%3D%22area%22%2F%3E%0A++%3C!--+gather+results+--%3E%0A++%3Cunion%3E%0A+++%3Cquery+type%3D%22node%22%3E%0A++++++%3Chas-kv+k%3D%22highway%22+%2F%3E%0A++++++%3Carea-query+from%3D%22area%22%2F%3E%0A+++%3C%2Fquery%3E%0A++%3C%2Funion%3E%0A++%3Cprint+from%3D%22_%22+limit%3D%22%22+mode%3D%22meta%22+order%3D%22id%22%2F%3E%0A++%3Cprint+mode%3D%22meta%22%2F%3E%0A++%3Crecurse+type%3D%22down%22%2F%3E%0A++%3Cprint+mode%3D%22meta%22%2F%3E%0A%3C%2Fosm-script%3E",
  "method": "POST"
});

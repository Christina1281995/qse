function init () {
    // =================================== BASE LAYERS CONFIGURATION =====================================
    // These layers are used as background maps, between which the user can choose.

    let baseLayers = [];

    let osm = new ol.layer.Tile({
        title: 'OSM',
        type: 'base',
        visible: true,
        crossOrigin: "Anonymous",
        source: new ol.source.OSM()
    })
    baseLayers.push(osm);

    let google_sat = new ol.layer.Tile({
        title: 'Google Satellite',
        type: 'base',
        visible: false,
        crossOrigin: "Anonymous",
        source: new ol.source.XYZ({
            url: 'http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}'
        })
    })
    baseLayers.push(google_sat);

    let google_road = new ol.layer.Tile({
        title: 'Google Road',
        type: 'base',
        visible: false,
        crossOrigin: "Anonymous",
        source: new ol.source.XYZ({
            url: 'http://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}'
        })
    })
    baseLayers.push(google_road);

    let google_terr = new ol.layer.Tile({
        title: 'Google Terrain',
        type: 'base',
        visible: false,
        crossOrigin: "Anonymous",
        source: new ol.source.XYZ({
            url: 'http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}'
        })
    })
    baseLayers.push(google_terr);

    // To be used in the LayerSwitcher panel
    baseLayers = new ol.layer.Group({
        title: "Background Maps",
        fold: 'open',
        collapsible: 'False',
        layers: baseLayers
    });

    // =================================== CREATE LAYER SWITCHER ==================================

    var layerSwitcher = new ol.control.LayerSwitcher({
        activationMode: "mouseover",
        tipLabel: 'Layers',
        groupSelectStyle: 'group',
        reverse: false
    });

    // -------------------------------------------- GEOLOCATION --------------------------------------------------

    //add current geolocation of user
    var geolocation = new ol.Geolocation({
        trackingOptions: {
            enableHighAccuracy: true,
        }
    });

    var markerSource = new ol.source.Vector();

    // Once location is found ("change") draw marker, set geolocation to false, zoom to location
    geolocation.on('change', function(){
        var currentPosition = ol.proj.transform(geolocation.getPosition(), 'EPSG:4326', 'EPSG:3857');
        console.log(currentPosition);
        drawMarkerCurrentPosition(currentPosition);
        geolocation.setTracking(false);
        map.getView().setCenter(currentPosition);
        map.getView().setZoom(15);
    });

    // Create a marker for the current geolocation position
    function drawMarkerCurrentPosition(currentPosition) {
        var marker = new ol.Feature({
            geometry: new ol.geom.Point(currentPosition)
        });

        var vectorStyle = new ol.style.Style({
            image: new ol.style.Icon(({
                scale: 0.5,
                src: 'https://github.com/Christina1281995/minktstories_webmap/blob/main/docs/static/current_position.png?raw=true'
            }))
        });
        marker.setStyle(vectorStyle);
        markerSource.addFeature(marker);
    }

    // Create vector layer
    var markerLayer = new ol.layer.Vector({
        // title: "My Position",
        visible: true,
        source: markerSource
    });

    // ---------------------------------------  CREATE BASIC MAP ----------------------------------------------------

    // Create a variable home position in the middle of Salzburg
    var homePos = ol.proj.transform ([13.048968315124512, 47.79982634240321], 'EPSG:4326', 'EPSG:3857');





    var map = new ol.Map({
        layers: [
            baseLayers,
            markerLayer
        ],
        controls: ol.control.defaults({
            attributionOptions: ({
                collapsible: true
            })
        }).extend([
            layerSwitcher,
            new ol.control.FullScreen(),
            new ol.control.ScaleLine()
        ]),
        target: 'map',
        view: new ol.View({
            center: homePos,
            zoom: 15
        })
    });

    // ---------------------------- PV

    // create PV Rectangle
    var pvSource = new ol.source.Vector();

    // Create vector layer
    var pv = new ol.layer.Vector({
        // title: "A Mock PV",
        visible: true,
        source: pvSource
    });

    map.addLayer(pv)

    // Create a marker for the current geolocation position
    function drawPV(coord) {
        // get count of features in the user position layer
        var featureCount = pv.getSource().getFeatures().length;
        if (featureCount > 0){
            // delete the other feature in the vector source first
            pvSource.clear()
        }
        var marker_pv = new ol.Feature({
            geometry: new ol.geom.Polygon([[
                [(coord[0] - 0.8), (coord[1] + 1.5)],
                [(coord[0] - 0.8), (coord[1] - 1.5)],
                [(coord[0] + 0.8), (coord[1] - 1.5)],
                [(coord[0] + 0.8), (coord[1] + 1.5)],
                [(coord[0] - 0.8), (coord[1] + 1.5)]
            ]])
        });
        var pvStyle = new ol.style.Style({
            stroke: new ol.style.Stroke({
              color: 'red',
              width: 1,
            }),
            fill: new ol.style.Fill({
                color: 'rgba(255, 0, 0, 0.1)',
            }),
        })
        marker_pv.setStyle(pvStyle)
        pvSource.addFeature(marker_pv);
    }

    map.on('click', function (evt) {
        console.log("map clicked)")
        drawPV(evt.coordinate);

        map.getView().setCenter(evt.coordinate);
        map.getView().setZoom(21);
        osm.setVisible(false);
        google_road.setVisible(false);
        google_terr.setVisible(false);
        google_sat.setVisible(true);

        // display current coordinates below map
        var coords = ol.proj.transform(evt.coordinate, 'EPSG:3857', 'EPSG:4326');
        document.getElementById("coords").innerHTML = "<p>Currently selected coordinates:  <b>"
            + coords[0].toFixed(4) + "</b>, <b> " + coords[1].toFixed(4) + " </b></p>";

        // fill form on right-hand side automatically with pin location
        document.getElementById("coord_x").value = coords[0].toFixed(5);
        document.getElementById("coord_y").value = coords[1].toFixed(5);


        // ----------------------- Rotation functionality -----------------------------

        const select = new ol.interaction.Select()
        select.getFeatures()
        // const select = new ol.SelectInteraction()
        // select.getFeatures().extend([polygon])

        const rotate = new RotateFeatureInteraction({
          features: select.getFeatures(),
          anchor: [ 0, 0 ],
          angle: -90 * Math.PI / 180
        })

        rotate.on('rotatestart', evt => console.log('rotate start', evt))
        rotate.on('rotating', evt => console.log('rotating', evt))
        rotate.on('rotateend', evt => select.getFeatures().clear(), console.log('rotate end', evt))

        rotate.on('rotateend', evt => {
            // get total angle in degrees
            console.log(evt.angle + ' is '+ (-1 * evt.angle * 180 / Math.PI ) + '°')
            // Fill form on right-hand side automatically with pin location
            document.getElementById("rotation").value = (-1 * evt.angle * 180 / Math.PI ).toFixed(2);
        })

        map.addInteraction(select)
        map.addInteraction(rotate)

    });

    // ----------------------------------- Geocoder ----------------------------

    var geocoder = new Geocoder('nominatim', {
      provider: 'mapquest',
      key: 'uTxP90JzA0grdbfUKUlo76J2EG0PAqKE',
      lang: 'en-US', //en-US, fr-FR
      placeholder: 'Search for ...',
      targetType: 'text-input',
      limit: 5,
      keepOpen: false
    });
    map.addControl(geocoder);

    geocoder.on('addresschosen', function(evt){
      //var feature = evt.feature,
          //coord = evt.coordinate,
          //address = evt.address;
      // some popup solution
        map.getView().setCenter(evt.coordinate);
        map.getView().setZoom(19);
      //content.innerHTML = '<p>'+ address.formatted +'</p>';
      // overlay.setPosition(coord);
    });

    // ------------------------------------ Geolocation button in map ----------------------------------------------
    function el(id) {
        return document.getElementById(id)
    }

    el('track').addEventListener('click', function() {
        geolocation.setTracking(this.checked);

    });

     // ------------------------------------ Home Button ------------------------------------------------------------

    const zoomHome = document.getElementById('home');
    zoomHome.addEventListener('click', function() {
        map.getView().setCenter(homePos);
        map.getView().setZoom(6);
    }, false);
}


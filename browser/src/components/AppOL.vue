<template>
  <div style="background-color: orange; height: 600px">

    <!-- ========== map & view ========= -->
    <vl-map  :load-tiles-while-animating="true"
             :load-tiles-while-interacting="true"
             data-projection="EPSG:4326"
             ref="map"
              @mounted="onMapMounted"
           >

    <vl-view ref="view"
             :zoom.sync="zoom"
             :center.sync="center"
             :rotation.sync="rotation"></vl-view>

      <!-- ========== layers ========= -->
      <!-- OpenStreetMap base layer
      -->
      <vl-layer-tile id="osm">
        <vl-source-osm></vl-source-osm>
      </vl-layer-tile>

      <!-- flight path features layer - geojson file retrieval via url
          TODO: swap out default url loader for custom loader (for error checking)
          almost: https://github.com/ghettovoice/vuelayers/issues/59
          uses style function/factory to color item based on geojson properties

      -->
      <vl-layer-vector >
        <vl-source-vector :url="geojsonUrl"
                          :features.sync="geojFeatures" />
        <vl-style-func :factory="geojStyleFuncFactory"></vl-style-func>
      </vl-layer-vector>

      <!-- ===================== FeatureCollection everything ========= -->

      <vl-layer-vector >
        <vl-source-vector :features.sync="everythingFeatures" />
        <vl-style-func    :factory="everyFormatFactory"></vl-style-func>
      </vl-layer-vector>

      <!-- ===================== FeatureCollection everything ========= -->

      <!-- kml features layer
      -->
      <vl-layer-vector >
          <vl-source-vector :url="kmlUrl"
                            :format-factory="kmlFormatFactory" />
      </vl-layer-vector>

      <!-- asdex layer ==========================  -->
      <vl-layer-vector >

<!-- note: PostGIS put id (which is track num) in geojson at the same
     level with type and geometry which allows this to work: -->

<!-- ============ use loader-factory ============ -->
        <vl-source-vector
                  :features.sync="pathFeatures"
                  :url="pathUrl"
                  :loader-factory="loaderFactoryOuter"
                  />

       <vl-style-func :factory="asdexStyleFuncFac" />

<!-- ============ use loader-factory ============ -->
        <vl-source-vector
                  :features.sync="fvfFeatures"
                  :url="fvfUrl"
                  :loader-factory="loaderFactoryOuterFvf"
                  />

       <vl-style-func :factory="asdexStyleFuncFac" />

<!-- ======================================================= -->

      </vl-layer-vector>

      <!-- ========== popup =========
          note: 'display' string in geojson properties was crafted by python
      -->
   <vl-interaction-select :features.sync="geojFeatures"></vl-interaction-select>

    <vl-overlay v-for="feature in geojFeatures"
                :key="feature.id"
                :position="feature.geometry.coordinates[0]">
      <div style="background: #ccf">
        {{ feature.properties.display }}
      </div>
    </vl-overlay>

      <!-- ========== end layers ========= -->
    </vl-map>

    <!-- p v-if="everythingFeatures.length > 0">
      Loaded features: {{ everythingFeatures.map(feature => feature.id) }}
    </p -->

  </div>
</template>

<script>

// $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

import ZoomSlider from 'ol/control/ZoomSlider'
import ScaleLine  from 'ol/control/ScaleLine'
import KML        from 'ol/format/KML'

import Stroke     from 'ol/style/Stroke'
import Style      from 'ol/style/Style'
import Text       from 'ol/style/Text'
import Fill       from 'ol/style/Fill'
import Circle     from 'ol/style/Circle'

import { Vector as VectorLayer } from 'ol/layer'

// ==========================================================

// -------------- linestrings
const unk_style   =new Style({ stroke: new Stroke({ color: 'grey',   width: 2.0 }) })
const plainStyle  =new Style({ stroke: new Stroke({ color: 'purple', width: 3.0 }) })

// -------------- SAME colors as in Charts.vue
const wt_map_colors = [
            '#996600'    // (sched) brown
           ,'#3399ff'    // (at entry) blue
           ,'green' ];   // (flown)

const src_s_style =new Style({ stroke: new Stroke({ color: wt_map_colors[0], width: 2.0 }) })
const src_a_style =new Style({ stroke: new Stroke({ color: wt_map_colors[1], width: 2.0 }) })
const src_f_style =new Style({ stroke: new Stroke({ color: wt_map_colors[2], width: 2.0 }) })

//const activeStyle =new Style({ stroke: new Stroke({ color: 'orange', width: 5.0 }) })
//const highlightSt =new Style({ stroke: new Stroke({ color: 'magenta',width: 5.0 }) })
//const undoStyle   =new Style({ stroke: new Stroke({ color: 'green',  width: 5.0 }) })

// -------------- target symbols
const image_circle = new Circle({ radius: 10,
                             fill: new Fill({ color: '#fff', }),
                             stroke: new Stroke({ color: '#F44336', }),   })
const image_h_circle = new Circle({ radius: 15,
                             fill: new Fill({ color: 'yellow', }),
                             stroke: new Stroke({ color: 'green', }),   })
// ==================================================================================

const methods = {

    // ==========================================================
    // https://firstclassjs.com/remove-duplicate-objects-from-javascript-array-how-to-performance-comparison/
    // TypeError: array.filter is not a function
    removeDuplicates_2(array, key) {
        return array.filter((obj, index, self) =>
            index === self.findIndex((el) => (
                el[key] === obj[key]
            ))
        )
    },

    // ==========================================================
    loaderFactoryOuter() {
      return (extent, resolution, projection) => this.loaderFactoryInner(extent, resolution, projection)
    },

    loaderFactoryInner(extent, resolution, projection) {

console.log("inside loaderFactoryInner:", extent, resolution, projection);
console.log(this.pathUrl);

if (this.pathUrl == 'bogus') { console.log("bogus url, no fetch"); return; }

      return fetch(this.pathUrl)
        .then(response => response.json())
        .then(data =>  {

          return(data); // <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

            /*********************************************
          // clean up data
          // NOTE: but ONLY for the Points, not the LineStrings
          // which is track/id < 900000

          let dlist = [];
          for (let k = 0; k < data.features.length; k++) {
              if (data.features[k].id < 900000) {
                  let elem = { track:  data.features[k].properties.track,
                               acid:   data.features[k].properties.acid,
                               actype: data.features[k].properties.actype  };
                  dlist.push(elem);
              }
          }

          // ---------------------------------
          const sortedlist = dlist.sort(function(a, b) {
              if (a.acid < b.acid) {
                return -1; //nameA comes first
              }
              if (a.acid > b.acid) {
                return 1; // nameB comes first
              }
              return 0;  // names must be equal
            });
          // ---------------------------------

          this.$root.$emit('dlist', (sortedlist) );

          return(data);
            *********************************************/
       })
    },
    // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    loaderFactoryOuterFvf() {
      return (extent, resolution, projection) => this.loaderFactoryInnerFvf(extent, resolution, projection)
    },

    loaderFactoryInnerFvf(extent, resolution, projection) {

console.log("inside loaderFactoryInnerFvf:", extent, resolution, projection);

if (this.fvfUrl == 'bogus') { console.log("bogus url, no fetch"); return(

{
  "type": "FeatureCollection",
  "features": []
}

); }

      return fetch(this.fvfUrl)
        .then(response => response.json())
        .then(data =>  {
          return(data);
       })
    },

    // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    onMapMounted () {
      // now ol.Map instance is ready and we can work with it directly
      this.$refs.map.$map.getControls().extend([
        new ScaleLine( { units: 'nautical'} ),
        new ZoomSlider(),
      ])
    },

    kmlFormatFactory () {
      return new KML()
    },

    // ------------ ASDEX attempt to color lines
    // sun pm: now works all the time, and nothing undefined:
    asdexStyleFuncFac() {

      return (feature) => {
// console.log("aSFF+g:" + feature.get('track') + "," +
//              this.highLightMe + ',' + feature.getGeometry().getType() );

        // ------------------------------
        // can't be const because of feature acid:
        let targetStyle = new Style({
          image: image_circle,
          text: new Text({ text: String(feature.get('acid')), }),
        });
        let targetHigh = new Style({
          image: image_h_circle,
          text: new Text({ text: String(feature.get('acid')), }),
        })

        // ------------------------------

        if (feature.getGeometry().getType() == "Point") {
            if (feature.key == this.highLightMe) {
                return targetHigh;
            } else {
                return targetStyle;
            }
        }
        return plainStyle;
     }
    },
    // ------------ attempt to color lines
    geojStyleFuncFactory() {

      return (feature) => {
        if (feature.get('SOURCE_TYPE')) {
          if (feature.get('SOURCE_TYPE')=='S') { return src_s_style; }
          if (feature.get('SOURCE_TYPE')=='F') { return src_f_style; }
          if (feature.get('SOURCE_TYPE')=='A') { return src_a_style; }
          return unk_style;
        }
        return unk_style;
     }
   },
       // ------------ everything paths have color in them
   everyFormatFactory() {
      return (feature) => {
        if (feature.get('ptype')) {
          if (feature.get('ptype')=='flw') { return src_f_style; }
          if (feature.get('ptype')=='ate') { return src_a_style; }
          if (feature.get('ptype')=='sch') { return src_s_style; }
          return unk_style;
        }
        return unk_style;
     }
   },

   populate_datalist(features_list) {

       let dlist = [];
       for (let k = 0; k < features_list.length; k++) {

           if ((features_list[k].geometry.type == "LineString")  ||
               (features_list[k].geometry.type == "MultiLineString")) {

              if (features_list[k].id < 900000) {
                  //HELP: let elem = { track:  features_list[k].properties.flight_index,
                  // pick out important fields from GeoJson properties
                  // and populate object to send to DataPos
                  let elem = { acid:     features_list[k].properties.acid,
                               flt_ndx:  features_list[k].properties.flt_ndx,
                               corner:   features_list[k].properties.corner,
                               dep_apt:  features_list[k].properties.dep_apt,
                               actype:   features_list[k].properties.actype,
                               arr_time: features_list[k].properties.arr_time,

                               sdist:    features_list[k].properties.sdist,
                               adist:    features_list[k].properties.adist,
                               fdist:    features_list[k].properties.fdist,
                               pct:      features_list[k].properties.pct,
                              };
                  dlist.push(elem);
              }
           }
       }

       // ---------------------------------
       const sortedlist = dlist.sort(function(a, b) {
           if (a.acid < b.acid) {
                return -1; //nameA comes first
           }
           if (a.acid > b.acid) {
                return 1; // nameB comes first
           }
           return 0;  // names must be equal
       });
       // ---------------------------------
console.log("populate-d:");
//console.log(dlist);

       this.$root.$emit('dlist', (sortedlist) );
   }
}

// ==========================================================

// center map on center of usa
//r KSTL = [ -90.3700289, 38.7486972];
var KDEN = [-104.6731667, 39.8616667];

export default {
    methods,
    data () {
      return {
        zoom: 5,
        center: KDEN,
        rotation: 0,

        geojsonUrl: '',
        geojFeatures: [],

        everythingFeatures: [],

        kmlUrl: '',

        // all OLD, INOP:
        pathUrl: 'bogus',
        fvfUrl: 'bogus',
        pathFeatures: [],
        fvfFeatures: [],
        aaaFeatures: [],   // rather old: https://github.com/ghettovoice/vuelayers/issues/25
        highLightMe: 15,  // track id of item to highlight

        // NEW:
        highlightedFeat: 0
      }
    },

// ==========================================================

  mounted () {

    // ---- receive vuejs message from AppUI, insert query into reactive
    // ---- location which apparently fires off a url request
    // -------------------------
    this.$root.$on('geojsonurl', (the_query) => {
      console.log("geojson:"+the_query);

      this.geojsonUrl = the_query;   // << that's all we have to do!
    })
    // -------------------------
    this.$root.$on('kmlurl', (the_query) => {
      console.log("kml:"+the_query);

      this.kmlUrl = the_query;
    })
    // -------------------------
    this.$root.$on('highlightthis', (the_target) => {

      // old: the_target = the_target+900000;  // just the tracks, not the target

      //console.log("highLightMe:"+the_target);
      this.highLightMe = the_target;

// ================================  Q: does asdexStyleFuncFac replace this???

      // turn off the previous one:
      if (this.highlightedFeat != 0) {
        // ------------------------------
        // can't be const because of feature acid:
        let targetStyle = new Style({
          image: image_circle,
          text: new Text({ text: String(this.highlightedFeat.get('acid')), }),
        });
          this.highlightedFeat.setStyle(targetStyle);
      }

      // find the vector layer that has a Feature with this id
      const a_layer = this.$refs.map.getLayers().filter(layer => {
        return layer instanceof VectorLayer &&
                   layer.getSource().getFeatureById(the_target)
      })

      // --------- this statement causes aSFF to fire with valid arguments
      if (a_layer[0] === undefined) {
          console.log("could not find the_target=" + the_target)
          } else {

          this.highlightedFeat = a_layer[0].getSource().getFeatureById(the_target);

              /// ------ need Style, not Circle!
        let targetHigh = new Style({
          image: image_h_circle,
          text: new Text({ text: String(this.highlightedFeat.get('acid')), }),
        })
              /// ------

          this.highlightedFeat.setStyle(targetHigh);
      }

      // ================================
    })

    // -------------------------
    this.$root.$on('pathsurl', (the_query) => {
      console.log("paths::"+the_query);

      // this fires off loaderFactory via vl-source-vector which does the actual fetch
      this.pathUrl = the_query;
    }),
    // -------------------------
    this.$root.$on('fvfurl', (the_query) => {
      console.log("fvf::"+the_query);

      // this fires off loaderFactory via vl-source-vector which does the actual fetch
      this.fvfUrl = the_query;
    })
    // -------------------------
    this.$root.$on('draw_all_fc', (map_args) => {

      let all_flights  = map_args.mdata;  // this is the FC, should it be just the Features[] ???
      let hour_to_disp = map_args.hour;
      hour_to_disp = "2020-01-10T" +  String(hour_to_disp).padStart(2,'0');  // do here or by caller?

      console.log(hour_to_disp)

       let flts_to_disp = [ ]
       for (let k = 0; k < all_flights.features.length; k++) {

           //console.log(all_flights.features[k].geometry.type);

           // Q: should this just check for existance of an 'arr_time' property???

           // if it is a (Multi) LineString (i.e. flight), then check arr time
           if ( (all_flights.features[k].geometry.type == "LineString") ||
                (all_flights.features[k].geometry.type == "MultiLineString")) {

               if (all_flights.features[k].properties.arr_time.substr(0,13) == hour_to_disp) {
                  // TODO: COMBINE this with DataPos generation!!!
                  // (maybe not so bad; DataPos list is constructed from this list)
                  flts_to_disp.push(all_flights.features[k]);
               }
           } else {

              // and always draw everything else
              flts_to_disp.push(all_flights.features[k]);
           }
       }

      this.everythingFeatures = flts_to_disp;

      this.populate_datalist(flts_to_disp);
console.log("done with new flights.");
    })
  } // ---- mounted
}

</script>

<style lang="scss">
.map {
    height: 600px;
}


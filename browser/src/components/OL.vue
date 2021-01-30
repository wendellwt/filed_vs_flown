<template>
  <div style="background-color: orange; height: 400px">

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

      <!-- ========== OpenStreetMap base layer ================== -->

      <vl-layer-tile id="osm">
        <vl-source-osm></vl-source-osm>
      </vl-layer-tile>

      <!-- ===================== FeatureCollection everything ========= -->

      <vl-layer-vector >
        <vl-source-vector :features.sync="everythingFeatures" />
        <vl-style-func    :factory="everythStyleFactory"></vl-style-func>
      </vl-layer-vector>

      <!-- ========== popup ========= -->

   <vl-interaction-select :features.sync="geojFeatures"></vl-interaction-select>

    <vl-overlay v-for="feature in geojFeatures"
                :key="feature.id"
                :position="feature.geometry.coordinates[0]">
      <div style="background: #ccf">
        {{ feature.properties.display }}
      </div>
    </vl-overlay>

      <!-- ========== skull layer ========= -->

    <!-- vl-layer-vector ref="skull_featuresLayer">
      <vl-source-vector :features="skull_features"></vl-source-vector>
      <vl-style-func :factory="skull_styleFuncFactory"></vl-style-func>
    </vl-layer-vector -->

      <!-- ========== end layers ========= -->
    </vl-map>

    <!-- ========== legend ========= -->
    <!-- pretty LAME, but works... -->
    <div class="legend">
flown: <input type="text" class="flown"/>
sched: <input type="text" class="at_entry"/>
    </div>

    <!-- ========== svg layer ========= -->
    <!-- https://jsfiddle.net/ghettovoice/m3j0zydr/ -->

  <!-- svg id="skull" version="1.1"  xmlns="http://www.w3.org/2000/svg" x="0px" y="0px"
     width="100px" height="100px" viewBox="0 0 100 100" enable-background="new 0 0 100 100" xml:space="preserve">
<g>
     <path d="M87.255,72.316c-2.248-2.246-5.832-2.318-8.118-0.208l-9-9c2.459-3.77,3.894-8.27,3.894-13.107s-1.435-9.337-3.894-13.107
          l8.949-8.949c2.287,2.111,5.87,2.042,8.118-0.207c2.306-2.3,2.329-6.017,0.054-8.293c-1.371-1.371-3.264-1.9-5.058-1.603
          c0.33-1.82-0.196-3.755-1.592-5.151c-2.274-2.275-5.985-2.252-8.291,0.055c-2.246,2.248-2.318,5.832-0.208,8.118l-9.001,9.001
          c-3.77-2.459-8.27-3.893-13.107-3.893c-4.837,0-9.336,1.434-13.107,3.893l-8.95-8.95c2.11-2.286,2.04-5.869-0.206-8.118
          c-2.305-2.304-6.018-2.328-8.293-0.054c-1.372,1.372-1.901,3.266-1.604,5.059c-1.82-0.33-3.756,0.197-5.152,1.591
          c-2.275,2.275-2.248,5.986,0.055,8.291c2.249,2.25,5.834,2.319,8.121,0.209l9,9c-2.46,3.77-3.894,8.27-3.894,13.107
          s1.434,9.337,3.894,13.107l-8.95,8.95c-2.286-2.11-5.869-2.04-8.118,0.206c-2.304,2.305-2.327,6.018-0.054,8.293
          c1.372,1.372,3.266,1.901,5.059,1.604c-0.33,1.82,0.197,3.756,1.591,5.152c2.275,2.275,5.986,2.248,8.291-0.055
          c2.249-2.249,2.319-5.834,0.209-8.121l8.726-8.726v5.946c3.645,2.985,8.303,4.779,13.382,4.779c5.079,0,9.738-1.794,13.383-4.779
          V70.41l8.674,8.674c-2.111,2.287-2.043,5.871,0.206,8.119c2.301,2.306,6.018,2.329,8.293,0.054c1.371-1.371,1.9-3.265,1.603-5.058
          c1.82,0.331,3.755-0.196,5.151-1.591C89.585,78.333,89.562,74.623,87.255,72.316z M43.445,58.989c-2.539,0-4.596-2.056-4.596-4.592
          s2.057-4.597,4.596-4.597c2.535,0,4.591,2.061,4.591,4.597S45.979,58.989,43.445,58.989z M56.556,59.056
          c-2.536,0-4.592-2.056-4.592-4.592c0-2.541,2.056-4.592,4.592-4.592c2.539,0,4.595,2.051,4.595,4.592
          C61.151,57,59.095,59.056,56.556,59.056z"/>
</g>
</svg -->

    <!-- ========== svg layer ========= -->

  </div>
</template>

<script>

// $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

import ZoomSlider from 'ol/control/ZoomSlider'
import ScaleLine  from 'ol/control/ScaleLine'

import Stroke     from 'ol/style/Stroke'
import Style      from 'ol/style/Style'

import { Vector as VectorLayer } from 'ol/layer'

//soon: import * as d3 from 'd3';

// this was helpful: https://stackoverflow.com/questions/50020722/initialize-svg-js-in-vuejs-component
// $ npm install svg.js
// nope: import SVG from 'svg.js'

// ==========================================================

const HELPME_OFFSET = 1000000; // flight_ndx offset to at_ent flight_ndx

// -------------- linestrings

const unk_style   =new Style({ stroke: new Stroke({ color: 'grey',   width: 2.0 }) })

// -------------- SAME colors as in Charts.vue
const wt_map_colors = [
            '#996600'    // (sched) brown
           ,'#3399ff'    // (at entry) blue
           ,'green' ];   // (flown)

const src_s_style = new Style({ stroke: new Stroke({ color: wt_map_colors[0], width: 2.0 }) })
const src_a_style = new Style({ stroke: new Stroke({ color: wt_map_colors[1], width: 2.0 }) })
const src_f_style = new Style({ stroke: new Stroke({ color: wt_map_colors[2], width: 2.0 }) })

// ==================================================================================
let skull_features_list = [
     {
      "type": "Feature",
      "id": 1,
      "properties": {
        "color": "red",
      },
      "geometry": {
        "type": "Point",
        "coordinates": [
          -30.761718749999996,
          58.90464570302001
        ]
      }
    },
    {
      "type": "Feature",
      "id": 2,
      "properties": {
        "color": "green",
      },
      "geometry": {
        "type": "Point",
        "coordinates": [
          36.73828124999999,
          44.59046718130883
        ]
      }
    },
    {
      "type": "Feature",
      "id": 3,
      "properties": {
        "color": "purple",
      },
      "geometry": {
        "type": "Point",
        "coordinates": [
          -23.37890625,
          32.10118973232094
        ]
      }
    }
]

// ==================================================================================

const methods = {

    // ==========================================================
    onMapMounted () {
      // now ol.Map instance is ready and we can work with it directly
      this.$refs.map.$map.getControls().extend([
        new ScaleLine( { units: 'nautical'} ),
        new ZoomSlider(),
      ])
    },

   // ------------ everything paths have color in them

   everythStyleFactory() {
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

  // pick out important fields from GeoJson properties
  // and populate object to send to DataPos
   populate_datalist(features_list) {

       let dlist = [];
       for (let k = 0; k < features_list.length; k++) {

           if ((features_list[k].geometry.type == "LineString")  ||
               (features_list[k].geometry.type == "MultiLineString")) {

              if (features_list[k].id < HELPME_OFFSET) {
                  let elem = {
                      acid:     features_list[k].properties.acid,
                      flt_ndx:  features_list[k].properties.flt_ndx,
                      corner:   features_list[k].properties.corner,
                      dep_apt:  features_list[k].properties.dep_apt,
                      actype:   features_list[k].properties.actype,
                      arr_time: features_list[k].properties.arr_time,

                      sdist:    features_list[k].properties.sdist,
                      adist:    features_list[k].properties.adist,
                      fdist:    features_list[k].properties.fdist,
                      diff:     (parseFloat(features_list[k].properties.adist) -
                                 parseFloat(features_list[k].properties.fdist)
                                ).toFixed(1)
                              };
                  dlist.push(elem);
              }
           }
       }

       // ---------------------------------
       /******************** sort by diff ***********/
       // but need floats, not strings!
       const sortedlist = dlist.sort(function(a, b) {
           let a_diff = parseFloat(a.diff);
           let b_diff = parseFloat(b.diff);
           if (a_diff < b_diff) {
                return -1; //a comes first
           }
           if (a_diff > b_diff) {
                return 1; // b comes first
           }
           return 0;  // names must be equal
       });
       /******************** sort by acid
       const sortedlist = dlist.sort(function(a, b) {
           if (a.acid < b.acid) {
                return -1; //nameA comes first
           }
           if (a.acid > b.acid) {
                return 1; // nameB comes first
           }
           return 0;  // names must be equal
       });
       ********************/

       // and send to DataPos list component
       this.$root.$emit('dlist', (sortedlist) );
   },
   // ==========================================================
   /* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    skull_styleFuncFactory () {

      console.log("create style func - skull")
      // get raw svg using http://svgjs.com/
      // vladimir's:
      let svg = SVG('skull')
console.log("skull.1");
      // mine: let svg = d3.select("#my_map_skull")

      return feature => {
console.log("skull.a");
        let featureSvg = svg.clone()
        featureSvg.attr('width', 100 + 'px')
        featureSvg.attr('height', 100 + 'px')
        // set color from feature data
        let path = featureSvg.select('path')
        path.fill(feature.get('color'))
console.log("skull.b");

        let img = new Image()
        img.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(featureSvg.svg())
        featureSvg.remove()
console.log("skull.c");
//console.log(src)
        // apply color by some rule: here we use proprty from feature
        let icon = new ol.style.Icon({
          img: img,
          imgSize: [100, 100],
          size: [100, 100],
        })
console.log("skull.d");

        return [
          new ol.style.Style({
            image: icon,
          })
        ]
      }
    },
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% */

   // ==========================================================
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

        geojFeatures: [], // USED???

        everythingFeatures: [],

        highlightedFeat_flw : 0,   // the current (old) item that may need to be turned off
        highlightedFeat_sch : 0,   // the current (old) item that may need to be turned off

        skull_features: skull_features_list
      }
    },

// ==========================================================

  mounted () {

    // -------------------------
    this.$root.$on('highlightthis', (the_target) => {

        let high_me = the_target;
        // ========== hightlight path -- FLOWN version
      // ---- turn off the previous one:
      if (this.highlightedFeat_flw != 0) {
        // ------------------------------
        // need to set back to PROPER color, which is always flown, right?
        this.highlightedFeat_flw.setStyle(src_f_style);
        this.highlightedFeat_flw = 0;
      }

      // ---- find the vector layer that has a Feature with this id
      const a_layer = this.$refs.map.getLayers().filter(layer => {
        return layer instanceof VectorLayer &&
                   layer.getSource().getFeatureById(high_me)
      })

      // ---- this statement causes aSFF(?) to fire with valid arguments
      if (a_layer[0] === undefined) {
          console.log("could not find high_me=" + high_me)
          } else {

          this.highlightedFeat_flw = a_layer[0].getSource().getFeatureById(high_me);

          // ---- need Style
          // ---- need Style >> MAKE this a const if no acid!
          let targetHigh_flw = new Style({
              stroke: new Stroke({ color: 'red', width: 4.0 })
              //text: new Text({ text: String(this.highlightedFeat_flw.get('acid')), }),
           })

          this.highlightedFeat_flw.setStyle(targetHigh_flw);
      }

        // ========== hightlight path -- AT_ENTRY version

      high_me = the_target + HELPME_OFFSET; // flight_ndx offset to at_ent path
      // ---- turn off the previous one:
      if (this.highlightedFeat_sch != 0) {
        // ------------------------------
        // need to set back to PROPER color, which is always flown, right?
        this.highlightedFeat_sch.setStyle(src_s_style);  // <<< DIFF
        this.highlightedFeat_sch = 0;
      }

      // ---- find the vector layer that has a Feature with this id
      let b_layer = this.$refs.map.getLayers().filter(layer => {
        return layer instanceof VectorLayer &&
                   layer.getSource().getFeatureById(high_me)
      })
      // ---- this statement causes aSFF(?) to fire with valid arguments
      if (b_layer[0] === undefined) {
          console.log("could not find high_me=" + high_me)
          } else {

          this.highlightedFeat_sch = b_layer[0].getSource().getFeatureById(high_me);

              // ---- need Style >> MAKE this a const if no acid!
          let targetHigh_sch = new Style({
              stroke: new Stroke({ color: '#990033', width: 4.0 }) // << diff
           })

          this.highlightedFeat_sch.setStyle(targetHigh_sch);
      }
    })

    // ================================

    // called from Panel because new dataset received or hour changed

    this.$root.$on('draw_all_fc', (map_args) => {

      let all_flights  = map_args.mdata;  // this is the FC, should it be just the Features[] ???
      let hour_to_disp = map_args.hour;

      let flts_to_disp = [ ]
      for (let k = 0; k < all_flights.features.length; k++) {

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

    })
  } // ---- mounted
}

</script>

<style lang="scss">
.map {
    height: 300px;
}

.legend {
    font-size: small;
}
.flown    { background-color: green;   width: 20px; height: 16px; }
.at_entry { background-color: #3399ff; width: 20px; height: 16px; }

</style>

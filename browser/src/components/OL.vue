<template>
  <div style="background-color: orange; height: 500px">

    <!-- ========== map & view ========= -->
    <vl-map  :load-tiles-while-animating="true"
             :load-tiles-while-interacting="true"
             data-projection="EPSG:4326"
             ref="map"
              @mounted="onMapMounted"
              class="svg_parent"
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

           <!-- ========== svg container layers ========= -->
      <!--csv: CornerCircBar v-for="corner in corners"
                     v-bind:key="corner.ident"
                     v-bind:corner_data="corner" >
      </CornerCircBar -->

      <!-- ========== end layers ========= -->
    </vl-map>

    <!-- ========== legend ========= -->
    <!-- pretty LAME, but works... -->
    <div class="legend">
flown: <input type="text" class="flown"/>
sched: <input type="text" class="at_entry"/>
<b-button type="is-warning is-light"
                    size="is-small"
                    rounded
                    v-on:click="do_some_d3()"
                    >do_some_d3</b-button>
    </div>

  </div>
</template>

<script>

// $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

import ZoomSlider from 'ol/control/ZoomSlider'
import ScaleLine  from 'ol/control/ScaleLine'

import Stroke     from 'ol/style/Stroke'
import Style      from 'ol/style/Style'

import { Vector as VectorLayer } from 'ol/layer'

//csv: import CornerCircBar from './CornerCircBar'

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
                      //flt_ndx:  features_list[k].properties.flt_ndx,
                      corner:   features_list[k].properties.corner,
                      dep_apt:  features_list[k].properties.dep_apt,
                      //actype:   features_list[k].properties.actype,
                      //arr_time: features_list[k].properties.arr_time,

                      //sdist:    features_list[k].properties.sdist,
                      //adist:    features_list[k].properties.adist,
                      //fdist:    features_list[k].properties.fdist,
                      //diff:     (parseFloat(features_list[k].properties.adist) -
                      //           parseFloat(features_list[k].properties.fdist)
                      //          ).toFixed(1)
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

   do_some_d3() {
     let corner_data = 1;
     this.$root.$emit('draw_this_corner', (corner_data));
   }
   // ==========================================================
}

// ==========================================================

// center map on center of usa
//r KSTL = [ -90.3700289, 38.7486972];
var KDEN = [-104.6731667, 39.8616667];

export default {
    methods,
    components: {
      //csv: CornerCircBar
    },
    data () {
      return {
        zoom: 5,
        center: KDEN,
        rotation: 0,

        geojFeatures: [], // USED???

        everythingFeatures: [],

        highlightedFeat_flw : 0,   // the current (old) item that may need to be turned off
        highlightedFeat_sch : 0,   // the current (old) item that may need to be turned off
        corners: [
          { dir: "ne", ident: 'LANDR', coords: [-104.002963888889, 40.3575722222222], colr: 'green'  },
          { dir: "se", ident: 'DANDD', coords: [-103.939133333333, 39.3970944444444], colr: 'blue'   },
          { dir: "sw", ident: 'LARKS', coords: [-105.305161111111, 39.2573972222222], colr: 'orange' },
          { dir: "nw", ident: 'RAMMS', coords: [-105.238811111111, 40.49355],         colr: 'magenta'},
        ]

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
// console.log("k="+k);
          // Q: should this just check for existance of an 'arr_time' property???

          // if it is a (Multi) LineString (i.e. flight), then check arr time
          // i.e., don't do the artcc polygon!
          if ( (all_flights.features[k].geometry.type == "LineString") ||
               (all_flights.features[k].geometry.type == "MultiLineString")) {
//console.log(all_flights.features[k].properties.arr_time.substr(0,13));
//console.log(hour_to_disp);

               if (all_flights.features[k].properties.arr_time.substr(0,13) == hour_to_disp) {
//console.log(hour_to_disp);
//console.log(all_flights.features[k].properties.arr_time.substr(0,13));

                  // TODO: COMBINE this with DataPos generation!!!
                  // (maybe not so bad; DataPos list is constructed from this list)
                  flts_to_disp.push(all_flights.features[k]);
//console.log("push:"+k);
               }
           } else {

              // and always draw everything else (the artcc)
              flts_to_disp.push(all_flights.features[k]);
           }
      }
      this.everythingFeatures = flts_to_disp;

      //new_fvf: 
      this.populate_datalist(flts_to_disp);

    })
  } // ---- mounted
}

</script>

<style lang="scss">
.map {
    height: 500px;
}
.svg_parent {
  position: relative;
}

.legend {
    font-size: small;
}
.flown    { background-color: green;   width: 20px; height: 16px; }
.at_entry { background-color: #3399ff; width: 20px; height: 16px; }

svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  position: absolute;
}
</style>

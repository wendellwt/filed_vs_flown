<template>
  <div style="background-color: orange; height: 700px">

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
        <vl-source-vector :features.sync="display_data" />
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
           <!-- was very cool, but CR didn't want it: div>
              <CornerCircBar v-for="corner in corners"
                             v-bind:key="corner.ident"
                             v-bind:corner_data="corner"
                             v-bind:show_yourself="draw_circles" >
              </CornerCircBar>
           </div -->

      <!-- ========== end layers ========= -->
    </vl-map>

    <!-- ========== legend ========= -->
    <!-- pretty LAME, but works... -->
    <div class="legend">
flown: <input type="text" class="flown"/>
sched: <input type="text" class="at_entry"/>
&nbsp; &nbsp; &nbsp;
    <b-checkbox type="is-info"
                        size="is-small"
                        v-model="draw_circles">draw_circles</b-checkbox>

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

// cool, but not desired: import CornerCircBar from './CornerCircBar'

// ==========================================================

//const HELPME_OFFSET = 1000000; // flight_ndx offset to at_ent flight_ndx
//30200302036612
const HELPME_OFFSET = 30000000000000;  // if FID is larger than this it is a
                      // schedule and not to be in datapos list

// -------------- linestrings

const unk_style   =new Style({ stroke: new Stroke({ color: 'grey',   width: 2.0 }) })

// -------------- SAME colors as in Charts.vue
// const wt_map_colors = [
//             '#996600'    // (sched) brown
//            ,'#3399ff'    // (at entry) blue
//            ,'green' ];   // (flown)
//
// const src_s_style = new Style({ stroke: new Stroke({ color: wt_map_colors[0], width: 2.0 }) })
// const src_a_style = new Style({ stroke: new Stroke({ color: wt_map_colors[1], width: 2.0 }) })
// const src_f_style = new Style({ stroke: new Stroke({ color: wt_map_colors[2], width: 2.0 }) })

const src_hi_style = new Style({ stroke: new Stroke({ color: 'red', width: 2.0 }) })

const wt_corner_colors = [
    '#002664',   // from ajr style guide
    '#007934',
    '#AB8422',
    '#5E6A71'
  ];

const cnr_ne_style = new Style({ stroke: new Stroke({ color: wt_corner_colors[0], width: 2.0 }) })
const cnr_se_style = new Style({ stroke: new Stroke({ color: wt_corner_colors[1], width: 2.0 }) })
const cnr_sw_style = new Style({ stroke: new Stroke({ color: wt_corner_colors[2], width: 2.0 }) })
const cnr_nw_style = new Style({ stroke: new Stroke({ color: wt_corner_colors[3], width: 2.0 }) })


//document.addEventListener('resize', <yourfunction>);
// ==================================================================================

const methods = {

    resize_yourself()  {  // MADE NO DIFFERENCE
          this.$refs.map.updateSize();
console.log("map timeout: updateSize");
    },
    // ==========================================================
    onMapMounted () {
      // now ol.Map instance is ready and we can work with it directly
      this.$refs.map.$map.getControls().extend([
        new ScaleLine( { units: 'nautical'} ),
        new ZoomSlider(),
      ]);
      this.$refs.map.updateSize();   // when map is in a tab, do this
    },

    // ==========================================================
    // worked, but made no difference in initial display...
  myEventHandler() {   // param 'e' removed
      this.$refs.map.updateSize();
// console.log("RESIZE event");
  },

   // ------------ everything paths have color in them
   // ------------ everything paths have color in them

   everythStyleFactory() {
      return (feature) => {
        if (feature.get('corner')) {
          if (feature.get('corner')=='ne') { return cnr_ne_style; }
          if (feature.get('corner')=='se') { return cnr_se_style; }
          if (feature.get('corner')=='sw') { return cnr_sw_style; }
          if (feature.get('corner')=='nw') { return cnr_nw_style; }
          return unk_style;
        }
        return unk_style;
     }
   },

    /**********************************
                "properties": {
        "acid": "FFT756",
                    "arr_time": "2020-01-10T02:05:00-05:00",
                    "b4_dep_dist": 325.01551865834,
                    "b4_ent_dist": 325.01551865834,
        "corner": "sw",
        "dep_apt": "PHX",
                    "dep_time": "2020-01-10T00:44:00-05:00",
        "fid": 20200110461222,
                    "flw_dist": 299.98276884894005,
                    "ptype": "flw"
                },
    **********************************/
  // pick out important fields from GeoJson properties
  // and populate object to send to DataPos
   populate_datalist(features_list) {

       let dlist = [];
       for (let k = 0; k < features_list.length; k++) {
//console.log("pop_datalist,k="+k+',id='+features_list[k].id);
           if ((features_list[k].geometry.type == "LineString")  ||
               (features_list[k].geometry.type == "MultiLineString")) {

              if (features_list[k].id < HELPME_OFFSET) {
                  let elem = {
                      acid:     features_list[k].properties.acid,
                      fid:      features_list[k].properties.fid,
                      corner:   features_list[k].properties.corner,
                      ac_type:  features_list[k].properties.ac_type,
                      dep_apt:  features_list[k].properties.dep_apt,
                      // reformat date here to make it look nice on datablock
                      // because it was too hard to do it later
                      arr_time: features_list[k].properties.arr_time.substr(8,2) + '-' +
                                features_list[k].properties.arr_time.substr(11,8),

                      sch_dist_f: parseFloat(features_list[k].properties.sch_dist).toFixed(1),
                      fld_dist_f: parseFloat(features_list[k].properties.fld_dist).toFixed(1),
                      dep_dist_f: parseFloat(features_list[k].properties.dep_dist).toFixed(1),
                      ent_dist_f: parseFloat(features_list[k].properties.ent_dist).toFixed(1),
                      flw_dist_f: parseFloat(features_list[k].properties.flw_dist).toFixed(1)

                      };
                  dlist.push(elem);
              }
           }
       }

       // ---------------------------------

       // and send to DataPos list component

       this.$root.$emit('dlist', (dlist) );
   },
   // ==========================================================

    // called from anywhere when display needs to be updated
    // * new model data received
    // * hour changed

    help_display_model_data() {

// console.log("OL:help_disp");
//console.log(this.model_data);

      let flts_to_disp = [ ]
      for (let k = 0; k < this.model_data.features.length; k++) {

          // Q: should this just check for existance of an 'arr_time' property???

          // if it is a (Multi) LineString (i.e. flight), then check arr time
          // i.e., don't do the artcc polygon!
          if ( (this.model_data.features[k].geometry.type == "LineString") ||
               (this.model_data.features[k].geometry.type == "MultiLineString")) {
               if (this.model_data.features[k].id < HELPME_OFFSET) {

//console.log("++++"+this.model_data.features[k].properties.arr_time);
let land_mins = parseInt(this.model_data.features[k].properties.arr_time.substr(14,2));
//console.log("lm:"+land_mins);
let mins_qh = String(Math.floor(land_mins/15)*15).padStart(2,'0');
//console.log(mins_qh);
let land_qh = this.model_data.features[k].properties.arr_time.substr(0,13)+':'+mins_qh;
//console.log("lq:"+land_qh);
//console.log("re:"+this.hour_to_disp);

                   if (land_qh == this.hour_to_disp) {

                  // TODO: COMBINE this with DataPos generation!!!
                  // (maybe not so bad; DataPos list is constructed from this list)
                  flts_to_disp.push(this.model_data.features[k]);
                 }
               }
           } else {

              // and always draw everything else (the artcc)
              flts_to_disp.push(this.model_data.features[k]);
           }
      }
      this.display_data = flts_to_disp;
      this.$refs.map.updateSize();  // when map is in a tab, do this

      this.populate_datalist(flts_to_disp);
    }

}

// ==========================================================

// center map on center of usa
//r KSTL = [ -90.3700289, 38.7486972];
var KDEN = [-104.6731667, 39.8616667];

export default {
    methods,
    components: {
        // cool, but not wanted: CornerCircBar
    },
    data () {
      return {
        zoom: 5,
        center: KDEN,
        rotation: 0,

        geojFeatures: [], // USED???

        model_data: [],     // model data from source
        display_data: [],   // hour data selected for display

        draw_circles : false,

        hour_to_disp: '2020_01_10T16',

        highlightedFeat_flw : 0,   // the current (old) item that may need to be turned off
        highlightedFeat_sch : 0,   // the current (old) item that may need to be turned off
        corners: [
          { dir: "ne", ident: 'LANDR', coords: [-104.002963888889, 40.3575722222222], colr: '#002664' },
          { dir: "se", ident: 'DANDD', coords: [-103.939133333333, 39.3970944444444], colr: '#007934' },
          { dir: "sw", ident: 'LARKS', coords: [-105.305161111111, 39.2573972222222], colr: '#AB8422' },
          { dir: "nw", ident: 'RAMMS', coords: [-105.238811111111, 40.49355],         colr: '#5E6A71' },
        ]

      }
    },

// ==========================================================

created() {
  window.addEventListener("resize", this.myEventHandler);
},
destroyed() {
  window.removeEventListener("resize", this.myEventHandler);
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
        this.highlightedFeat_flw.setStyle(src_hi_style);
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
        this.highlightedFeat_sch.setStyle(cnr_ne_style);  // WRONG
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
    }),

    // ================================
    this.$root.$on('map_tab_entered', () => { // param 'bogus' removed
          this.$refs.map.updateSize();   // when map is in a tab, do this
console.log("map tab entered; updateSize");

setTimeout( this.resize_yourself(), 100);
    //map.updateSize();   // when map is in a tab, do this
      // this.$refs.map.updateSize();
//console.log("map timeout: updateSize");
//}, 100);


    }),
    // ================================

    // called from Model because new dataset received or hour changed
    // NEW feb13: this is ALL of the data, and it is not kept elsewhere, btw

    this.$root.$on('new_model_data', (map_args) => {

      this.model_data  = map_args.mdata;  // this is the FC, should it be just the Features[] ???

      this.hour_to_disp = map_args.hour;

// console.log("OL: new_model_data");

      this.help_display_model_data();

setTimeout( this.resize_yourself(), 100);  // q: does this help???

    }),

    this.$root.$on('new_hour_slider', (map_args) => {

        this.hour_to_disp =  map_args.hour.getUTCFullYear() + '-' +
                      String(map_args.hour.getUTCMonth()+1).padStart(2,'0') + '-' +
                      String(map_args.hour.getUTCDate()   ).padStart(2,'0') + 'T' +
                      String(map_args.hour.getUTCHours()  ).padStart(2,'0') + ':' +
                      String(map_args.hour.getUTCMinutes()).padStart(2,'0');

// console.log("OL: new_hour_slider:"+this.hour_to_disp);

      this.help_display_model_data();
    })

  } // ---- mounted
}

</script>

<style lang="scss">
.map {
    height: 700px;
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

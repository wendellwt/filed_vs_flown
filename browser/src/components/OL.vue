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

      <!-- ========== end layers ========= -->
    </vl-map>

  </div>
</template>

<script>

// $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

import ZoomSlider from 'ol/control/ZoomSlider'
import ScaleLine  from 'ol/control/ScaleLine'

import Stroke     from 'ol/style/Stroke'
import Style      from 'ol/style/Style'

import { Vector as VectorLayer } from 'ol/layer'

// ==========================================================

// -------------- linestrings

const unk_style   =new Style({ stroke: new Stroke({ color: 'grey',   width: 2.0 }) })

// -------------- SAME colors as in Charts.vue
const wt_map_colors = [
            '#996600'    // (sched) brown
           ,'#3399ff'    // (at entry) blue
           ,'green' ];   // (flown)

const src_s_style =new Style({ stroke: new Stroke({ color: wt_map_colors[0], width: 2.0 }) })
const src_a_style =new Style({ stroke: new Stroke({ color: wt_map_colors[1], width: 2.0 }) })
const src_f_style =new Style({ stroke: new Stroke({ color: wt_map_colors[2], width: 2.0 }) })

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

              if (features_list[k].id < 900000) {
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
       /******************** sort by pct ***********/
       const sortedlist = dlist.sort(function(a, b) {
           let a_pct = parseFloat(a.pct);
           let b_pct = parseFloat(b.pct);
           if (a_pct < b_pct) {
                return -1; //a comes first
           }
           if (a_pct > b_pct) {
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

        geojFeatures: [], // USED???

        everythingFeatures: [],

        highLightMe     : 15,  // flight_index of item to highlight
        highlightedFeat : 0    // the current (old) item that may need to be turned off
      }
    },

// ==========================================================

  mounted () {

    // -------------------------
    this.$root.$on('highlightthis', (the_target) => {

      //console.log("highLightMe:"+the_target);
      this.highLightMe = the_target;

      /*************************** OLD, but need something that works:

      // ==========  Q: does asdexStyleFuncFac replace this???

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
        ***************************/
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


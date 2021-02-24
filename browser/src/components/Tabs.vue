<template>
    <section>
        <b-tabs position="is-centered" class="block"
                                       @input="tabChanged"
            >

         <!-- ============= map tab ============== -->
         <!-- PROBLEM: if map is in some other tab, then it REQUIRES resize to get itself drawn!!! -->

         <b-tab-item label="Map" value="map">

             <!-- FiledEntry / --> <!-- looks better here, but uses too much real estate -->

            <div class="columns">
              <div class="column">
                <OL></OL>
              </div>
              <div class="column is-one-quarter">
                <DataPos></DataPos>
              </div>
            </div>
         </b-tab-item>

         <!-- ============= bar chart tab ============== -->

         <b-tab-item label="Corner charts" value="chart">

              <Chart v-for="corner in corners"
                     v-bind:key="corner.ident"
                     v-bind:corner_data="corner" >
              </Chart>

         </b-tab-item>

         <!-- ============= bar chart tab ============== -->
         <!-- OLD: b-tab-item label="Charts"> <Charts /> </b-tab-item -->

         <!-- ============= stacked chart tab ============== -->
         <!-- b-tab-item label="Stacked"> <Stacked /> </b-tab-item -->

         <!-- ============= circular chart tab ============== -->
         <!-- old: b-tab-item label="Circular"> <Circular /> </b-tab-item -->

         <!-- ============= table tab ==============
         <b-tab-item label="Table"><mytable /></b-tab-item> -->

         <!-- ============= details tab ============== -->
         <b-tab-item label="Details" value="details"><Details /></b-tab-item>

         <!-- ============= about tab ============== -->
         <b-tab-item label="About" value="about"><About /></b-tab-item>

        </b-tabs>
        <Model />  <!-- pointless??? -->
    </section>
</template>

<script>

import Model      from "./Model.vue";
import OL         from './OL.vue';
import DataPos    from "./DataPos.vue";
import Details    from "./Details.vue";
import About      from "./About.vue";
import Chart     from "./Chart.vue";

export default {
  name: 'Tabs',
    components: {
      Model,
      Chart,
      OL,
      DataPos,
      Details,
      About

  },
  props: {
    msg: String
  },
/****************************************/
    data() {
      return {

        corners: [
 { dir: "ne", ident: 'LANDR', coords: [-104.002, 40.357], colr: '#002664', offs:   0 },
 { dir: "se", ident: 'DANDD', coords: [-103.939, 39.397], colr: '#007934', offs: 250 },
 { dir: "sw", ident: 'LARKS', coords: [-105.305, 39.257], colr: '#AB8422', offs: 500 },
 { dir: "nw", ident: 'RAMMS', coords: [-105.238, 40.493], colr: '#5E6A71', offs: 750 },
        ]

      };
    },
/****************************************/
    methods: {
        tabChanged: function(index) {
console.log("tabChanged:"+index);
            if (index == "map") {  // OL is the only one that needs it
                this.$root.$emit('map_tab_entered', (true) );
            }
        }
    }
/****************************************/
}
</script>

<style lang="scss" scoped>
</style>


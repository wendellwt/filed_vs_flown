<template>
    <section>
        <b-tabs position="is-centered" class="block">

         <!-- ============= filed & at_entry chart tab ============== -->
         <b-tab-item label="Filed vs At Entry"> <FiledEntry /> </b-tab-item>

         <!-- ============= map tab ============== -->

         <b-tab-item label="Map">

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
         <!-- OLD: b-tab-item label="Charts"> <Charts /> </b-tab-item -->

         <!-- ============= stacked chart tab ============== -->
         <!-- b-tab-item label="Stacked"> <Stacked /> </b-tab-item -->

         <!-- ============= circular chart tab ============== -->
         <!-- old: b-tab-item label="Circular"> <Circular /> </b-tab-item -->

         <!-- ============= table tab ==============
         <b-tab-item label="Table"><mytable /></b-tab-item> -->

         <!-- ============= details tab ============== -->
         <b-tab-item label="Details"><Details /></b-tab-item>

         <!-- ============= about tab ============== -->
         <b-tab-item label="About"><About /></b-tab-item>

        </b-tabs>
        <Model />  <!-- pointless??? -->
    </section>
</template>

<script>

import Model      from "./Model.vue";
import FiledEntry from "./FiledEntry.vue";
import OL         from './OL.vue';
import DataPos    from "./DataPos.vue";
import Details    from "./Details.vue";
import About      from "./About.vue";
//import Charts     from "./Charts.vue";
//import Stacked    from "./Stacked.vue";
// import Circular   from "./Circular.vue";
//import Table   from "./Table.vue";

export default {
  name: 'Tabs',
    components: {
      Model,
      FiledEntry,
      OL,
      DataPos,
      Details,
      About

        // old, experimental:
      //Charts,
      //Stacked,
      // Circular,
      // 'mytable'  : Table,    // duh! 'table' is bad choice for a local html component!

  },
  props: {
    msg: String
  },
    data() {
      return {
          foo : 1
      };
    },
}
</script>

<style lang="scss" scoped>
</style>


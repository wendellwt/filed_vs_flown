<template>
    <section>
        <b-tabs position="is-centered" class="block">

         <!-- ============= map tab ============== -->

         <b-tab-item label="Map">

         <FiledEntry />

            <div class="columns">
              <div class="column">
                <app-ol></app-ol>
              </div>
              <div class="column is-one-quarter">
                <data-pos></data-pos>
              </div>
            </div>
         </b-tab-item>

         <!-- ============= bar chart tab ============== -->
         <b-tab-item label="Charts"> <Charts /> </b-tab-item>

         <!-- ============= filed & at_entry chart tab ============== -->
         <!-- b-tab-item label="Filed vs At Entry"> <FiledEntry /> </b-tab-item -->

         <!-- ============= stacked chart tab ============== -->
         <b-tab-item label="Stacked"> <Stacked /> </b-tab-item>

         <!-- ============= table tab ==============
         <b-tab-item label="Table"><mytable /></b-tab-item> -->

         <!-- ============= details tab ============== -->
         <b-tab-item label="Details"><mydetails /></b-tab-item>

         <!-- ============= about tab ============== -->
         <b-tab-item label="About"><About /></b-tab-item>

        </b-tabs>
    </section>
</template>

<script>

import OL         from './OL.vue';
import DataPos    from "./DataPos.vue";
import Charts     from "./Charts.vue";
import Stacked    from "./Stacked.vue";
import FiledEntry from "./FiledEntry.vue";
import Details    from "./Details.vue";
import About      from "./About.vue";
//import Table   from "./Table.vue";

export default {
  name: 'Tabs',
    components: {
      'app-ol'   : OL,
      'data-pos' : DataPos,
      // 'mytable'  : Table,    // duh! 'table' is bad choice for a local html component!
      'mydetails': Details,
      Charts,
      Stacked,
      FiledEntry,
      About
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


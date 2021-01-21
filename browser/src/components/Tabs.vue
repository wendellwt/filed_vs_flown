<template>
    <section>
        <b-tabs position="is-centered" class="block">

            <!-- ============= map tab ============== -->

            <b-tab-item label="Map">

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
            <!-- ============= YIPEE!! one finally worked! ============== -->

            <b-tab-item label="Charts"> <Charts /> </b-tab-item>

            <!-- ============= table tab ============== -->

            <b-tab-item label="Table"><mytable /></b-tab-item>

        </b-tabs>
    </section>
</template>

<script>

import AppOL   from './AppOL.vue';
import DataPos from "./DataPos.vue";
import Table   from "./Table.vue";
import Charts  from "./Charts.vue";

export default {
  name: 'Tabs',
    components: {
      'app-ol'   : AppOL,
      'data-pos' : DataPos,
      'mytable'  : Table,    // duh! 'table' is bad choice for a local html component!
      Charts
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



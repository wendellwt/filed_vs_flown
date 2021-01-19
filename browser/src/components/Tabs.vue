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

<!-- ********************************************
            <b-tab-item label="BarChart">
    <BarChart
      class="chart"
      :data-set="data"
      :margin-left="40"
      :margin-top="40"
      :tick-count="5"
      :bar-padding="0.5"
    />
            </b-tab-item>
******************************************** -->

            <!-- ============= v3bar chart tab ============== -->

<!-- ********************************************
            <b-tab-item label="Vd3Chart">
                        <Vd3Charts />
            </b-tab-item>
            < ! xx b-tab-item label="ChartJs">
                   <Chartjs :chartdata="chartData" :options="chartOptions"/>
            </b-tab-item xx >

            <!xx b-tab-item label="Codepen"> <CodePen /> </b-tab-item xx>

            <!xx b-tab-item label="BarJs"> <BarJs /> </b-tab-item xx >

            <!xx b-tab-item label="Fiddle"> <Fiddle /> </b-tab-item xx >

            <!xx b-tab-item label="Random"> <Random /> </b-tab-item xx >
            <!xxmissing: b-tab-item label="Vc"> <Vc /> </b-tab-item xx >
            <b-tab-item label="D3bc"> <D3bc /> </b-tab-item>
******************************************** -->

            <!-- ============= table tab ============== -->

            <b-tab-item label="Table"><mytable /></b-tab-item>

        </b-tabs>
    </section>
</template>

<script>

import AppOL   from './AppOL.vue';
import DataPos from "./DataPos.vue";
import Table   from "./Table.vue";
            /*******************************
//import Charts  from "./Charts.vue";
import BarChart  from "./BarChart.vue";
import Vd3Charts  from "./Vd3Charts.vue";
//blank: import Chartjs    from "./Chartjs.vue";
//import CodePen    from "./CodePen.vue";
//blank: import BarJs    from "./BarJs.vue";
//import Fiddle    from "./Fiddle.vue";
//chartData: import Random    from "./Random.vue";
//missing: import Vc    from "./Vc.vue";
import D3bc    from "./D3bc.vue";
            *******************************/

export default {
  name: 'Tabs',
    components: {
      'app-ol'   : AppOL,
      'data-pos' : DataPos,
      'mytable'  : Table    // duh! 'table' is bad choice for a local html component!
/*******************************
       Vd3Charts,
      BarChart,
      //blank: Chartjs,
        //CodePen,
        //blank: BarJs,
        //Fiddle,
        //chartData: Random,
        //missing: Vc,
         D3bc
*******************************/
  },
  props: {
    msg: String
  },
    data() {
      return {
          // BarChart
        data: [
          ["Bob", 33],
          ["Robin", 24],
          ["Mark", 22],
          ["Joe", 29],
          ["Eve", 38],
          ["Karen", 21],
          ["Kirsty", 25],
          ["Chris", 30],
        ],
    chartData: {
      labels: ['January', 'February'],
      datasets: [
        {
          label: 'Data One',
          backgroundColor: '#f87979',
          data: [40, 20]
        }
      ]
    },
    chartOptions: {
      responsive: true,
      maintainAspectRatio: false
    }

      };
    },
}
</script>

<style lang="scss" scoped>
  .chart {
    margin: 40px auto 0;
    display: block;
  }
</style>



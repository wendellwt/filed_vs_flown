<template>
  <div>
      <h3>NEW experimental Circular Chart {{the_date}}</h3>

    <!-- Create a div where the graph will take place -->
    <!-- div name is NOT local to this component; it is global for the web page! -->
    <div id="my_dataviz_circ" class="chart_circ"></div>

  </div>
</template>

<script>

// ======================== common to maps and charts

import * as d3 from 'd3';

// overall chart size
var chart_width  = 560;
var chart_height = 300;

// position of legend
//unused: var legend_x = 300;
//unused: var legend_y =   5;
//unused: var leg_size =  15;

// List of subgroups = header of the csv files
//unused: var wt_subgroups = [ "ne", "se", "sw", "nw"];

// https://tools.aspm.faa.gov/confluence/display/prod/Tableau+Dashboard+Style+Guide
//var wt_chart_colors = [
//     '#002664'   // RGB (0, 38, 100)
//    ,'#007934'   // RGB (0, 121, 52)
//    ,'#AB8422'   // RGB (171, 132, 34)
//    ,'#5E6A71'   // RGB (94, 106, 113)
//          ];

// ========================

export default {
  name: 'Circular',
    data() {
      return {
        the_date: new Date()  // in header/title
      }
    },

  mounted: function() {
      this.$root.$on('draw_circ_chart', (chart_args) => {

          let cdata     = chart_args.cdata;
          let ymax      = chart_args.slider_vals[1];
          this.the_date = chart_args.title_date

          let wt_groups = [ ];
          for (let k = 0; k < cdata.length; k++ ) {
                  wt_groups.push(cdata[k].arr_hr);
          }

console.log("circ cdata currently:");
console.log(cdata);
console.log("wt_groups:");
console.log(wt_groups);

          this.displayCircularData(cdata, ymax);
      })
  },

    methods: {
        displayCircularData : function(cdata, y_max) {

  // set the dimensions and margins of the graph
            // bottom margin of 80 leaves room for x-axis label rotated
  let margin = {top: 10, right: 30, bottom: 80, left: 50},
      width  = chart_width  - margin.left - margin.right,
      height = chart_height - margin.top  - margin.bottom;

  // "svg" is apparently the name of the component _and_ the type
console.log("do something with this:"+y_max);

  // ---- remove previous sub-components, if any
  d3.select("#my_dataviz_circ").selectAll("svg").remove();

  // ---- define the main div of the chart
  let svg = d3.select("#my_dataviz_circ")
    .append("svg")
      .attr("width",  width  + margin.left + margin.right)
      .attr("height", height + margin.top  + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + width / 2 + "," + ( height/2+100 )+ ")");
            // Add 100 on Y translation, cause upper bars are longer

      //.attr("transform",
      //      "translate(" + margin.left + "," + margin.top + ")");

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

var   innerRadius = 50;
var   outerRadius = Math.min(width, height) / 2;
            // the outerRadius goes from the middle of the SVG area to the border

  // X scale
  // X axis goes from 0 to 2pi = all around the circle. If I stop at 1Pi, it will be around a half circle
  var x = d3.scaleBand()
      .range([0, 2 * Math.PI])
      .align(0)                  // This does nothing ?
      .domain( cdata.map(function(d) { return d.arr_hr; }) );

  // Y scale
  var y = d3.scaleRadial()
      .range([innerRadius, outerRadius])   // Domain will be define later.
      .domain([0, y_max]); // Domain of Y is from 0 to the max seen in the data

  // Add bars
  svg.append("g")
    .selectAll("path")
    .data(cdata)
    .enter()
    .append("path")
      //.attr("fill", "green")
      .attr("fill", function(d) {return d['dist']==30 ? "orange" : "green"})
      .attr("d", d3.arc()     // imagine your doing a part of a donut plot
          .innerRadius(innerRadius)
          .outerRadius(function(d) { return y(d['dist']); })
          .startAngle(function(d) { return x(d.arr_hr); })
          .endAngle(function(d) { return x(d.arr_hr) + x.bandwidth(); })
          .padAngle(0.01)
          .padRadius(innerRadius))

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    } // displayGData function
  } // methods
} // export

</script>

<style lang="scss">

/* need to specify at page load so it won't be empty/ small */
/* numbers are same as in script */
div.chart_circ {
  width:  560px;
  height: 300px;
  background-color: #f8f8f8;
}

p.chsmall {
  font-size: 80%;
}

</style>

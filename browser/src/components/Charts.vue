<template>
  <div>
      <h3>Grouped Corner Chart {{the_date}}</h3>

    <!-- Create a div where the graph will take place -->
    <div id="my_dataviz"></div>

  </div>
</template>

<script>

import * as d3 from 'd3';

// ======================== common to maps and charts

// List of groups = species here = value of the first column called group
var wt_groups = [ "ne", "se", "sw", "nw" ];

// List of subgroups = header of the csv files
var wt_subgroups = [ "first_sch_dist", "at_ent_dist", 'flown_dist' ];

// let y_max = 70000;    // <<<<<<<<<<<<<<<<<<<<<<<<

var wt_chart_colors = [ // I think these look nice:
            '#996600'    // brown
           ,'#3399ff'    // blue
           ,'green'
          ];

// ======================== common to maps and charts

export default {
  name: 'Charts',
    data() {
      return {
        the_date: new Date()  // in header/title
      }
    },

  mounted: function() {
      this.$root.$on('draw_new_chart', (chart_args) => {

          let ndata     = chart_args.cdata;
          let ymin      = chart_args.slider_vals[0] * 100;
          let ymax      = chart_args.slider_vals[1] * 100;
          this.the_date = chart_args.title_date

          this.displayGData(ndata, ymin, ymax);
      })
  },

    /**************** Charts ***************/
    /* FINALLY, an example d3 chart that works!!!:     */
    /* https://www.d3-graph-gallery.com/graph/barplot_stacked_basicWide.html */
    /**************** Charts ***************/

    methods: {
        displayGData : function(ndata, y_min, y_max) {

    // =========================== my edits
    // =========================== my edits - end

  // set the dimensions and margins of the graph
  let margin = {top: 10, right: 30, bottom: 20, left: 50},
      width  = 460 - margin.left - margin.right,    // WIDTH is fixed!!!
      height = 200 - margin.top  - margin.bottom;   // HEIGHT is fixed!!!

  // "svg" is apparently the name of the component _and_ the type

  // ---- remove previous sub-components, if any
  d3.select("#my_dataviz").selectAll("svg").remove();

  // ---- define the main dif of the chart
  let svg = d3.select("#my_dataviz")
    .append("svg")
      .attr("width",  width  + margin.left + margin.right)
      .attr("height", height + margin.top  + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

  // ---- Add X axis
  let x = d3.scaleBand()
      .domain(wt_groups)
      .range([0, width])
      .padding([0.2])
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x).tickSizeOuter(0));

  // ---- Add Y axis
  let y = d3.scaleLinear()
    .domain([y_min, y_max])
    .range([ height, 0 ]);
  svg.append("g")
    .call(d3.axisLeft(y));

  // ---- another scale for subgroup position(?)
  var xSubgroup = d3.scaleBand()
    .domain(wt_subgroups)
    .range([0, x.bandwidth()])
    .padding([0.05])

  // ---- color palette = one color per subgroup
  let color = d3.scaleOrdinal()
    .domain(wt_subgroups)
    .range(wt_chart_colors)

  // ---- Show the bars
  svg.append("g")
    .selectAll("g")
    .data(ndata)
    .enter()
    .append("g")
      .attr("transform", function(d) { return "translate(" + x(d.corner) + ",0)"; })
    .selectAll("rect")
    .data(function(d) { return wt_subgroups.map(function(key) { return {key: key, value: d[key]}; }); })
    .enter().append("rect")
      .attr("x", function(d) { return xSubgroup(d.key); })
      .attr("y", function(d) { return y(d.value); })
      .attr("width", xSubgroup.bandwidth())
      .attr("height", function(d) { return height - y(d.value); })
      .attr("fill", function(d) { return color(d.key); });

    } // displayGData function
  } // methods
} // export

</script>


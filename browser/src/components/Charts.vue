<template>

    <!-- Create a div where the graph will take place -->
    <div id="my_dataviz"></div>

</template>

<script>

import * as d3 from 'd3';

export default {
  name: 'Charts',
    data() {
      return {
        jdata:   [
  {"group" :   "banana", "Nitrogen" : 12, "normal" :  1, "stress" : 13},
  {"group" :   "poacee", "Nitrogen" :  6, "normal" :  6, "stress" : 33},
  {"group" :   "sorgho", "Nitrogen" : 11, "normal" : 28, "stress" : 33},
  {"group" : "triticum", "Nitrogen" : 19, "normal" :  6, "stress" :  1}
]
      }
    },

  mounted: function() {
      this.$root.$on('update', (ndata) => {
          console.log("Charts received update");
          this.displayGData(ndata);
          console.log("Charts done");
      })
  },

    /**************** Charts ***************/
    /* https://www.d3-graph-gallery.com/graph/barplot_stacked_basicWide.html */
    /**************** Charts ***************/

    methods: {
        displayGData : function(ndata) {

    // =========================== my edits

  // List of groups = species here = value of the first column called group
  //var groups = d3.map(data, function(d){return(d.group)}).keys()
  let wt_groups = [ "ne", "se", "sw", "nw" ];  // <<<<<<<<<< FIXME

  // List of subgroups = header of the csv files
  //var subgroups = data.columns.slice(1)
  let wt_subgroups = [ "sched_dist_zdv", "flown_dist_zdv" ];  // <<<< FIXME

  let y_max = 120000;    // <<<<<<<<<<<<<<<<<<<<<<<<

    // =========================== my edits - end

  // set the dimensions and margins of the graph
  let margin = {top: 10, right: 30, bottom: 20, left: 50},
      width  = 460 - margin.left - margin.right,
      height = 400 - margin.top  - margin.bottom;

  // append the svg object to the body of the page
  let svg = d3.select("#my_dataviz")
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

  // Add X axis
  let x = d3.scaleBand()
      .domain(wt_groups)
      .range([0, width])
      .padding([0.2])
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x).tickSizeOuter(0));

  // Add Y axis
  let y = d3.scaleLinear()
    .domain([0, y_max])
    .range([ height, 0 ]);
  svg.append("g")
    .call(d3.axisLeft(y));

  // color palette = one color per subgroup
  let color = d3.scaleOrdinal()
    .domain(wt_subgroups)
    .range(['#e41a1c','orange'])
    //.range(['#e41a1c','#377eb8','#4daf4a'])

  //stack the data? --> stack per subgroup
  let stackedData = d3.stack().keys(wt_subgroups)(ndata)

  // Show the bars
  svg.append("g")
    .selectAll("g")
    // Enter in the stack data = loop key per key = group per group
    .data(stackedData)
    .enter().append("g")
      .attr("fill", function(d) { return color(d.key); })
      .selectAll("rect")
      // enter a second time = loop subgroup per subgroup to add all rectangles
      .data(function(d) { return d; })
      .enter().append("rect")
        //.attr("x", function(d) { return x(d.data.group); })
        .attr("x", function(d) { return x(d.data.corner); })  // <<<<<<<<<<<<<<<< wt
        .attr("y", function(d) { return y(d[1]); })
        .attr("height", function(d) { return y(d[0]) - y(d[1]); })
        .attr("width",x.bandwidth())
    } // displayGData
  } // methods
} // export

</script>



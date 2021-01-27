<template>
  <div>
      <h3>filed &amp; at_entry Corner Chart {{the_date}}</h3>
      <p class="chsmall">bars are sum of flown distances by hour and corner</p>
      <p class="chsmall">red dot is sum of the at-entry schedule by hour</p>

    <!-- Create a div where the graph will take place -->
    <!-- div name is NOT local to this component; it is global for the web page! -->
    <div id="my_dataviz_fe"></div>

  </div>
</template>

<script>

import * as d3 from 'd3';

var chart_width = 560;
var chart_height = 300;

var legend_x = 400;
var legend_y = 20;

// ======================== common to maps and charts

// List of groups = species here = value of the first column called group
// unused: var use_this_as_key = "arr_hr";  // TODO: use this somehow

// List of subgroups = header of the csv files
var wt_subgroups = [ "ne", "se", "sw", "nw"];

// let y_max = 70000;    // <<<<<<<<<<<<<<<<<<<<<<<<

var wt_chart_colors = [ // https://tools.aspm.faa.gov/confluence/display/prod/Tableau+Dashboard+Style+Guide
     '#002664'   // RGB (0, 38, 100)
    ,'#007934'   // RGB (0, 121, 52)
    ,'#AB8422'   // RGB (171, 132, 34)
    ,'#5E6A71'   // RGB (94, 106, 113)
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
      this.$root.$on('draw_fe_chart', (chart_args) => {

          let ndata     = chart_args.cdata;
          let ate_data  = chart_args.atedata;
          let ymin      = chart_args.slider_vals[0] * 1000;
          let ymax      = chart_args.slider_vals[1] * 1000;
          this.the_date = chart_args.title_date

          let wt_groups = [ ];
          for (let k = 0; k < ndata.length; k++ ) {
                  wt_groups.push(ndata[k].arr_hr);
          }

// console.log("fe data currently:");
// console.log(ndata);
// console.log("ate data currently:");
// console.log(ate_data);
// console.log("wt_groups:");
// console.log(wt_groups);

          this.displayGData(ndata, ate_data, wt_groups, ymin, ymax);
      })
  },

    /**************** Charts ***************/
    /* FINALLY, an example d3 chart that works!!!:     */
    /* https://www.d3-graph-gallery.com/graph/barplot_stacked_basicWide.html */
    // and now for something completely different:  The Larch.
    // clickable legend, mouseover values:
    // http://bl.ocks.org/KatiRG/5f168b5c884b1f9c36a5
    /**************** Charts ***************/

    methods: {
        displayGData : function(ndata, ate_data, wt_groups, y_min, y_max) {

    // =========================== my edits
    // =========================== my edits - end

  // set the dimensions and margins of the graph
            // bottom margin of 80 leaves room for x-axis label rotated
  let margin = {top: 10, right: 30, bottom: 80, left: 50},
      width  = chart_width  - margin.left - margin.right,
      height = chart_height - margin.top  - margin.bottom;

  // "svg" is apparently the name of the component _and_ the type

  // ---- remove previous sub-components, if any
  d3.select("#my_dataviz_fe").selectAll("svg").remove();

  // ---- define the main div of the chart
  let svg = d3.select("#my_dataviz_fe")
    .append("svg")
      .attr("width",  width  + margin.left + margin.right)
      .attr("height", height + margin.top  + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

  // ---- Add X axis
  let x = d3.scaleBand()  // function named xScale in other examples
      .domain(wt_groups)
      .range([0, width])
      .padding([0.2])

  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x).tickSizeOuter(0))
      .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-65)");

  // ---- Add Y axis
  let y = d3.scaleLinear()    // function named yScale in other examples
    .domain([y_min, y_max])
    .range([ height, 0 ]);

  svg.append("g")
    .call(d3.axisLeft(y));

  // ---- stack the data? --> stack per subgroup
  var stackedData = d3.stack().keys(wt_subgroups)(ndata)

  // ---- color palette = one color per subgroup
  let color = d3.scaleOrdinal()
    .domain(wt_subgroups)
    .range(wt_chart_colors)

  // ---- show the _stacked_ bars
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
        .attr("x", function(d) { return x(d.data.arr_hr); })   // was: group
        .attr("y", function(d) { return y(d[1]); })
        .attr("height", function(d) { return y(d[0]) - y(d[1]); })
        .attr("width",x.bandwidth())

    // from: https://www.d3-graph-gallery.com/graph/area_lineDot.html
    // Add the dots
    svg.selectAll("myCircles")
      .data(ate_data)
      .enter()
      .append("circle")
        .attr("fill", "red")
        .attr("stroke", "none")
        .attr("cx", function(d) { return x(d.arr_hr)+10 }) // +10 is my own fudge offset
        .attr("cy", function(d) { return y(d.at_ent_dist) })
        .attr("r", 5)

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
//  https://www.d3-graph-gallery.com/graph/custom_legend.html
var size = 20;

// Add one dot in the legend for each name.
svg.selectAll("mydots")
  .data(wt_subgroups)
  .enter()
  .append("rect")
    .attr("x", legend_x)
    .attr("y", function(d,i){ return legend_y + i*(size+5)}) // 100 is where the first dot appears. 25 is the distance between dots
    .attr("width", size)
    .attr("height", size)
    .style("fill", function(d){ return color(d)})

// Add one dot in the legend for each name.
svg.selectAll("mylabels")
  .data(wt_subgroups)
  .enter()
  .append("text")
    .attr("x", legend_x + size*1.2)
    .attr("y", function(d,i){ return legend_y + i*(size+5) + (size/2)}) // 100 is where the first dot appears. 25 is the distance between dots
    //.style("fill", function(d){ return color(d)})
    //.text(function(d){ return wt_subgroups[d]})
    .text(function(d){ return String(d)})
    .attr("text-anchor", "left")
    .style("alignment-baseline", "middle")


// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    } // displayGData function
  } // methods
} // export

</script>

<style lang="scss">
p.chsmall {
  font-size: 80%;
}

</style>

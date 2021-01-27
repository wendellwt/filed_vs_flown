<template>
  <div>
      <h3>filed &amp; at_entry Corner Chart {{the_date}}</h3>

    <!-- Create a div where the graph will take place -->
    <!-- div name is NOT local to this component; it is global for the web page! -->
    <div id="my_dataviz_fe"></div>

  </div>
</template>

<script>

import * as d3 from 'd3';

// ======================== common to maps and charts

// List of groups = species here = value of the first column called group
var wt_groups = [
"2020_01_10_03",
"2020_01_10_04",
"2020_01_10_05",
"2020_01_10_06",
"2020_01_10_07",
"2020_01_10_11",
"2020_01_10_13",
"2020_01_10_14",
"2020_01_10_15",
"2020_01_10_16",
"2020_01_10_17",
"2020_01_10_18",
"2020_01_10_19",
"2020_01_10_20",
"2020_01_10_21",
"2020_01_10_22",
"2020_01_10_23",
"2020_01_11_00",
"2020_01_11_01",
"2020_01_11_02" ];

// List of subgroups = header of the csv files
var wt_subgroups = [ "ne", "se", "sw", "nw"];

// let y_max = 70000;    // <<<<<<<<<<<<<<<<<<<<<<<<

var wt_chart_colors = [ // I think these look nice:
            '#996600'    // brown
           ,'#3399ff'    // blue
           ,'green'
           ,'orange'
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

console.log("fe data currently:");
console.log(ndata);
console.log("ate data currently:");
console.log(ate_data);

          this.displayGData(ndata, ate_data, ymin, ymax);
      })
  },

    /**************** Charts ***************/
    /* FINALLY, an example d3 chart that works!!!:     */
    /* https://www.d3-graph-gallery.com/graph/barplot_stacked_basicWide.html */
    /**************** Charts ***************/

    methods: {
        displayGData : function(ndata, ate_data, y_min, y_max) {

    // =========================== my edits
    // =========================== my edits - end

  // set the dimensions and margins of the graph
            // bottom margin of 80 leaves room for x-axis label rotated
  let margin = {top: 10, right: 30, bottom: 80, left: 50},
      width  = 460 - margin.left - margin.right,    // WIDTH is fixed!!!
      height = 500 - margin.top  - margin.bottom;   // HEIGHT is fixed!!!

  // "svg" is apparently the name of the component _and_ the type

  // ---- remove previous sub-components, if any
  d3.select("#my_dataviz_fe").selectAll("svg").remove();

  // ---- define the main dif of the chart
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

  /*********** this way for grouped
  // ---- another scale for subgroup position(?)
  var xSubgroup = d3.scaleBand()
    .domain(wt_subgroups)
    .range([0, x.bandwidth()])
    .padding([0.05])
  ***********/
  /*********** this way for stacked */
  //stack the data? --> stack per subgroup
  var stackedData = d3.stack().keys(wt_subgroups)(ndata)

  // ---- color palette = one color per subgroup
  let color = d3.scaleOrdinal()
    .domain(wt_subgroups)
    .range(wt_chart_colors)

  /*********** this way for stacked */
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

    } // displayGData function
  } // methods
} // export

</script>


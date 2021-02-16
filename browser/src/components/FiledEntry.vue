<template>
  <div>
      <h3>on File at artcc entry and Flown Chart {{the_date}}</h3>
      <p class="chsmall">bars are sum of flown distances by quarter hour and corner</p>
      <!-- not: p class="chsmall">red dot is sum of the at-entry schedule by hour</p -->

    <!-- Create a div where the graph will take place -->
    <!-- div name is NOT local to this component; it is global for the web page! -->
    <div id="my_dataviz_fe" class="chart_fe"></div>

    <div id="tooltip" class="tooltip"></div>
  </div>
</template>

<script>

// ======================== common to maps and charts (?)

// overall chart size -- HELP this MUST match the css in <style>
var chart_width  = 760;
var chart_height = 450;

// bottom margin of ? leaves room for x-axis label rotated
var margin = {top: 90, right: 30, bottom: 20, left: 50};

// position of legend
var legend_x = 300;
var legend_y =   5;
var leg_size =  15;

// List of subgroups = header of the csv files
var wt_subgroups = [ "ne_flw", "se_flw", "sw_flw", "nw_flw"];

// https://tools.aspm.faa.gov/confluence/display/prod/Tableau+Dashboard+Style+Guide
var wt_chart_colors = [
     '#002664'   // RGB (0, 38, 100)
    ,'#007934'   // RGB (0, 121, 52)
    ,'#AB8422'   // RGB (171, 132, 34)
    ,'#5E6A71'   // RGB (94, 106, 113)
          ];

// ========================

import * as d3 from 'd3';

//*********** WRONG:
// https://stackoverflow.com/questions/53715028/d3-js-in-vue-component-how-to-hook-mouse-events-to-elements

// ========================

export default {
  name: 'Charts',
    data() {
      return {

        ef_data   : [],          // the data to draw
        the_date  : new Date(),  // in header/title
        wt_groups : [],
        xLabels   : [],
        ymin      : 0,
        ymax      : 6000
      }
    },

  mounted: function() {

/*********************
                "columns": [ "arr_qh",
"ne_flw",  "se_flw",  "sw_flw",  "nw_flw",
"ne_ate",  "se_ate",  "sw_ate",  "nw_ate",
"ne_diff", "se_diff", "sw_diff", "nw_diff" ],

        "data": [

            [ "2020-01-10T05:00:00.000Z",
228.9242318776, 474.0443257578, 332.1119153879, 173.239155921,
252.1244843646, 483.4809662288, 334.0080910996, 171.6641628169,
-23.200252487, -9.436640471, -1.8961757118, 1.5749931041  ],

            [ "2020-01-10T05:15:00.000Z",
456.8877513607, 357.576098375, 331.7720443895, 0.0,
501.556690982, 396.1441334338, 333.1322582447, 0.0,
-44.6689396213, -38.5680350589, -1.3602138552, 0.0 ],
 *********************/

      this.$root.$on('new_ef_data', (chart_args) => {

          this.the_date = chart_args.title_date;

          // convert input as a list of lists into an assoc array

          this.ef_data   = [];
          this.wt_groups = [ ];
          this.xLabels   = [ ];

          for(var k = 0; k < chart_args.ef_data.data.length; k++) {

              // collect chart data for contents
              var item = { 'arr_qh'  : chart_args.ef_data.data[k][0].substr(5,11),
                           "ne_flw"  : chart_args.ef_data.data[k][1],
                           "se_flw"  : chart_args.ef_data.data[k][2],
                           "sw_flw"  : chart_args.ef_data.data[k][3],
                           "nw_flw"  : chart_args.ef_data.data[k][4] }
                this.ef_data.push(item);

                // collect grouping elements and x-axis data/labels
                this.wt_groups.push(chart_args.ef_data.data[k][0].substr(5,11));
                this.xLabels  .push(chart_args.ef_data.data[k][0].substr(5,11));
          }

          this.display_EF_Data(this.ef_data, 1, this.wt_groups, this.ymin, this.ymax, this.xLabels);
      }),

      this.$root.$on('chart_slider_vals', (chart_ef_args) => {

          // BROKEN: this.ymin = chart_ef_args.slider_vals[0] * 100;
          this.ymax = chart_ef_args.slider_vals[1] * 100;

          this.display_EF_Data(this.ef_data, 1, this.wt_groups, this.ymin, this.ymax, this.xLabels);
      })

  },

    /**************** Charts ***************/
    /* FINALLY, an example d3 chart that works!!!:     */
    /* https://www.d3-graph-gallery.com/graph/barplot_stacked_basicWide.html */
    // and now for something completely different:  The Larch.
    // clickable legend, mouseover values:
    // http://bl.ocks.org/KatiRG/5f168b5c884b1f9c36a5
    /**************** Charts ***************/

    //  editing:
    // By convention, selection methods that return the current selection use four
    // spaces of indent, while methods that return a new selection use only two.

    methods: {

//       nice_x_label: function(d) {
//console.log("nxl");
//            return x(d.data.arr_qh);
//        },

        /* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% */

        display_EF_Data : function(ef_data, ate_data, wt_groups, y_min, y_max, xLabels) {


  // set the dimensions and margins of the graph
  let width  = chart_width  - margin.left - margin.right;
  let height = chart_height - margin.top  - margin.bottom;

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
  let xScale = d3.scaleBand()  // function named xScale in other examples
      .domain(wt_groups)
      .range([0, width])
      .padding([0.2])

      // https://ghenshaw-work.medium.com/customizing-axes-in-d3-js-99d58863738b
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(xScale) // x-axis generator
              .tickSizeOuter(0)
              .tickFormat((d,i) => i % 4 == 0 ? xLabels[i] : "" )
         )
      .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-65)");

  // ---- Add Y axis
  let yScale = d3.scaleLinear()    // function named yScale in other examples
    .domain([y_min, y_max])
    .range([ height, 0 ]);

  svg.append("g")
    .call(d3.axisLeft(yScale));

  // ---- stack the data? --> stack per subgroup

  // good reading: http://using-d3js.com/05_06_stacks.html
  // api def: d3.stack() - returns a stack generator.
  // which creates the generator using wt_subgroups as the keys
  // then _invoke_ the generator passing it the data to use

  var stackedData = d3.stack().keys(wt_subgroups)(ef_data)

console.log("stackedData");
console.log(stackedData);

  // ---- color palette = one color per subgroup
  let colorScale = d3.scaleOrdinal()
    .domain(wt_subgroups)
    .range(wt_chart_colors)

  // ---- show the _stacked_ bars
  svg.append("g")
    .selectAll("g")

    // Enter in the stack data === loop over keys (group by group?)
    .data(stackedData)
    .enter().append("g")
      .attr("fill", function(d) { return colorScale(d.key); })
      .selectAll("rect")

      // enter a second time = loop over subgroups to add all rectangles
      .data(function(d) { return d; })
      .enter().append("rect")
        .attr("x",      function(d) { return xScale(d.data.arr_qh);       })
        .attr("y",      function(d) { return yScale(d[1]);                })
        .attr("height", function(d) { return yScale(d[0]) - yScale(d[1]); })
        .attr("width",xScale.bandwidth())

        // https://bl.ocks.org/d3noob/a22c42db65eb00d4e369
       .on("mouseover", function(event,d) {

           let disp_val = (parseFloat(d[1])-parseFloat(d[0])).toFixed(1)+"nm";

           let tooltip = d3.select("#tooltip");

           // HELP: wtf are the x and y offsets????
           tooltip.html(disp_val)
                 .style("opacity", .9)
                 .style("left", (event.clientX-250) + "px")
                 .style("top",  (event.clientY-50)  + "px");
                  })
       .on("mouseout", function() {   // faa laptop: removed 'd' from arg
           let tooltip = d3.select("#tooltip");
           tooltip.style("opacity", 0);
       });


// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% legend

//  https://www.d3-graph-gallery.com/graph/custom_legend.html

// Add one square in the legend area for each color
svg.selectAll("leg_dots")
  .data(wt_subgroups)
  .enter()
  .append("rect")
    .attr("x", function(d,j){ return legend_x + j*(leg_size+25)})
    .attr("y", legend_y)
    .attr("width", leg_size)
    .attr("height", leg_size)
    .style("fill", function(d){ return colorScale(d)})

// Add one text element in the legend area for each subgroup
svg.selectAll("leg_text")
  .data(wt_subgroups)
  .enter()
  .append("text")
    .attr("x", function(d,j){ return legend_x + j*(leg_size+25) + (leg_size+3)})
    .attr("y", legend_y + leg_size*0.8)
    .text(function(d){ return String(d).substr(0,2)})
    .attr("text-anchor", "left")
    .style("alignment-baseline", "middle")
// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    }   // displayGData function
  } // methods
} // export

</script>

<style lang="scss">

/* need to specify at page load so it won't be empty/ small */
/* numbers are same as in script */
div.chart_fe {
  width:  760px;
  height: 450px;
  background-color: #f8f8f8;
}

p.chsmall {
  font-size: 80%;
}

div.tooltip {
    position: absolute;
    text-align: center;
    width: 80px;
    height: 28px;
    padding: 2px;
    font: 12px sans-serif;
    background: lightsteelblue;
    border: 2px;
    border-radius: 8px;
    pointer-events: none;
}

.tt-country {
    font-size: 1.1rem;
    font-weight: 900;
}

</style>

<template>
  <div>
      <h3>filed &amp; at_entry Corner Chart {{the_date}}</h3>
      <p class="chsmall">bars are sum of flown distances by hour and corner</p>
      <p class="chsmall">red dot is sum of the at-entry schedule by hour</p>

    <!-- Create a div where the graph will take place -->
    <!-- div name is NOT local to this component; it is global for the web page! -->
    <div id="my_dataviz_fe" class="chart_fe"></div>

    <div id="tooltip" class="tooltip"></div>
  </div>
</template>

<script>

// ======================== common to maps and charts


// overall chart size -- HELP this MUST match the css in <style>
var chart_width  = 560;
var chart_height = 450;
var margin = {top: 90, right: 30, bottom: 80, left: 50};

// position of legend
var legend_x = 300;
var legend_y =   5;
var leg_size =  15;

// List of subgroups = header of the csv files
var wt_subgroups = [ "ne", "se", "sw", "nw"];

// https://tools.aspm.faa.gov/confluence/display/prod/Tableau+Dashboard+Style+Guide
var wt_chart_colors = [
     '#002664'   // RGB (0, 38, 100)
    ,'#007934'   // RGB (0, 121, 52)
    ,'#AB8422'   // RGB (171, 132, 34)
    ,'#5E6A71'   // RGB (94, 106, 113)
          ];

// ========================

import * as d3 from 'd3';

    /***********
// https://stackoverflow.com/questions/53715028/d3-js-in-vue-component-how-to-hook-mouse-events-to-elements
import { select, selectAll, event, customEvent } from 'd3-selection'

WRONG:
export const d3.event() = function{ return event };

  select,
  selectAll,
  //tree,
  //hierarchy,
  //zoom,
  // event,
  get event() { return event; },
  customEvent
}
    ***********/

// ========================

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
          let ymin      = chart_args.slider_vals[0] * 100;
          let ymax      = chart_args.slider_vals[1] * 100;
          this.the_date = chart_args.title_date

          let wt_groups = [ ];
          let xLabels = [ ];
          for (let k = 0; k < ndata.length; k++ ) {
                  wt_groups.push(ndata[k].arr_qh);
                  xLabels  .push(ndata[k].arr_qh.substr(8,8));
          }

console.log("fe data currently:");
console.log(ndata);
console.log("ate data currently:");
console.log(ate_data);
console.log("wt_groups:");
console.log(wt_groups);
console.log("xLabels:");
console.log(xLabels);

          this.displayGData(ndata, ate_data, wt_groups, ymin, ymax, xLabels);
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

        nice_x_label: function(d) {
console.log("nxl");
            return x(d.data.arr_qh);
        },

        displayGData : function(ndata, ate_data, wt_groups, y_min, y_max, xLabels) {

    // =========================== my edits
    // =========================== my edits - end

  // set the dimensions and margins of the graph
            // bottom margin of 80 leaves room for x-axis label rotated
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
  let x = d3.scaleBand()  // function named xScale in other examples
      .domain(wt_groups)
      .range([0, width])
      .padding([0.2])

      // https://ghenshaw-work.medium.com/customizing-axes-in-d3-js-99d58863738b
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x) // x-axis generator
                .tickSizeOuter(0)
                .tickFormat((d,i) => i % 4 == 0 ? xLabels[i] : "" )
                )
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
        // HELP: .attr("x", function(d) { this.nice_x_label(d) })
        .attr("x", function(d) {
                                   return x(d.data.arr_qh);
                                })   // was: group, was arr_hr
        .attr("y", function(d) { return y(d[1]); })
        .attr("height", function(d) { return y(d[0]) - y(d[1]); })
        .attr("width",x.bandwidth())

        // https://bl.ocks.org/d3noob/a22c42db65eb00d4e369
       .on("mouseover", function(event,d) {

           let disp_val = (parseFloat(d[1])-parseFloat(d[0])).toFixed(1)+"nm";

           let tooltip = d3.select("#tooltip");

           // HELP: wtf are the x and y offsets????
           tooltip.html(disp_val)
                 .style("opacity", .9)
                 .style("left", (event.clientX-250) + "px")
                 .style("top",  (event.clientY-50)  + "px");

                // console.log("left:"+event.clientX + "px");
                // console.log("top:"+event.clientY + "px");
                // HELP: .style("left", `${d3.event.pageX}px`)
                // HELP: .style("top",  `${d3.event.pageY}px`);
                // help: .style("left", (d3.event.pageX) + "px")
                // help: .style("top", (d3.event.pageY - 28) + "px");

                  })
       .on("mouseout", function(d) {
           let tooltip = d3.select("#tooltip");
           tooltip.style("opacity", 0);
       });

            /***********************
    .on("mouseenter", function(d) {
      // https://github.com/d3/d3-format/blob/master/README.md#format
      const format = d3.format(",");

      d3
        .select(this)
        .attr("fill", "rgba(0, 0, 0, .5)")
        .attr("stroke", "rgba(255, 255, 255, .5)");

      tooltip
        .append("div")
        .text("9999")
        .attr("class", "tt-region");

      //tooltip
      //  .append("div")
      //  .text(d.data.key)
      //  .attr("class", "tt-country");

      //tooltip
      //  .append("div")
      //  .text(format(d.value))
      //  .attr("class", "tt-population");

      //help: const tooltipElement = tooltip.node().getBoundingClientRect();
      //help: const tooltipElement = tooltip.getBoundingClientRect();
      //help: const { height: elementHeight } = tooltipElement;

      tooltip
        .style("opacity", 1)
        // https://github.com/d3/d3-selection/blob/master/README.md#event
        //HELP: .style("left", `${d3.event.pageX}px`)
        //HELP: .style("top", `${d3.event.pageY - elementHeight}px`);
    })
    .on("mouseout", function() {
      d3
        .select(this)
        .attr("fill", "rgba(0, 0, 0, .1)")
        .attr("stroke", "rgba(255, 255, 255, .25)");

      tooltip
        .style("opacity", 0)
        .selectAll("div")
        .remove();
    });
    ****************/


    // from: https://www.d3-graph-gallery.com/graph/area_lineDot.html
    // Add the dots
    svg.selectAll("myCircles")
      .data(ate_data)
      .enter()
      .append("circle")
        .attr("fill", "red")
        .attr("stroke", "none")
        .attr("cx", function(d) { return x(d.arr_qh)+2 }) // +10 is my own fudge offset
        .attr("cy", function(d) { return y(d.at_ent_dist) })
        .attr("r", 2)

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
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
    .style("fill", function(d){ return color(d)})

// Add one text element in the legend area for each subgroup
svg.selectAll("leg_text")
  .data(wt_subgroups)
  .enter()
  .append("text")
    .attr("x", function(d,j){ return legend_x + j*(leg_size+25) + (leg_size+3)})
    .attr("y", legend_y + leg_size*0.8)
    .text(function(d){ return String(d)})
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
  width:  560px;
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

.tooltipTRACEY {
    position: absolute;
    opacity: 0;
    pointer-events: none;
    transition: all 0.2s ease-in-out;
    max-width: 500px;
    border-radius: 4px;
    background: #fff;
    box-shadow: 0 1px 5px rgba(51,51,51,0.5);
    padding: 1rem;
}

.tt-country {
    font-size: 1.1rem;
    font-weight: 900;
}

</style>

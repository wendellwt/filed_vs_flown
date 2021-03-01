<template>
  <div style="height: 250px">
      <h3>total miles
corner: <b>{{ corner_data.dir }}</b>;
arr apt:<b>{{arr_apt}}</b>;
path center:<b>{{center}}</b>;
path type:<b>{{path}}</b>;
path source:<b>{{source}}</b>
</h3>

    <!-- Create a div where the graph will take place -->
    <!-- div name is NOT local to this component; it is global for the web page! -->
    <div :id="'svg_div_'+corner_data.dir"
           class="chart_simp" >
    </div>

    <!-- mouseover: div id="tooltip" class="tooltip"></div -->
  </div>
</template>

<script>

// ======================== common to maps and charts (?)

// overall chart size -- HELP this MUST match the css in <style>
var chart_width  = 960; // MISSING: 760
var chart_height = 250;

// bottom margin of ? leaves room for x-axis label rotated
var margin = {top: 40, right: 30, bottom: 60, left: 50};

// position of legend
//leg: var legend_x = 300;
//leg: var legend_y =   5;
//leg: var leg_size =  15;
// List of subgroups = header of the csv files
//leg: var wt_subgroups = [ "ne_flw", "se_flw", "sw_flw", "nw_flw"];

// https://tools.aspm.faa.gov/confluence/display/prod/Tableau+Dashboard+Style+Guide

import * as d3 from 'd3';

//*********** WRONG:
// https://stackoverflow.com/questions/53715028/d3-js-in-vue-component-how-to-hook-mouse-events-to-elements

export default {
  name: 'Charts',
  props: {
      corner_data: Object,
   },

    data() {
      return {

        my_corner_data : [],    // the chart data

        the_date   : new Date(),  // in header/title
        arr_qh_set : [],
        //xLabels    : [],
        ymin       : 0,
        ymax       : 4000,
        high_qh    : "01_10_14:00",

        center     : "na",
        path       : "na",
        source     : "na",
        arr_apt    : "na"
      }
    },

  mounted: function() {

// %%%%%%%%%%%%%%%%%%%%%%%%%%%% incomming chart data

      this.$root.$on('new_bar_data', (chart_args) => {

// console.log("rcvd: new_bar_data:"+this.corner_data.dir);

          this.center   = chart_args.center;
          this.path     = chart_args.path;
          this.source   = chart_args.source;
          this.arr_apt  = chart_args.arr_apt;

          this.the_date = chart_args.title_date;

          this.arr_qh_set = [ ];

          // convert input as a list of lists into an assoc array

          let foo = this.json2array(chart_args.cdata[this.corner_data.dir]);

          this.my_corner_data = foo.d;
          this.arr_qh_set     = foo.x;
//console.log(this.arr_qh_set);
//console.log(this.my_corner_data);

          this.display_Bar_Data(this.my_corner_data, this.arr_qh_set, this.ymin, this.ymax,
                                this.high_qh);
      }),

// %%%%%%%%%%%%%%%%%%%%%%%%%%%% incomming max y-val slider

      this.$root.$on('chart_slider_vals', (chart_ef_args) => {

// console.log("rcvd: chart_slider_vals");

          // BROKEN: this.ymin = chart_ef_args.slider_vals[0] * 100;
          this.ymax = chart_ef_args.slider_vals[1] * 100;

          this.display_Bar_Data(this.my_corner_data, this.arr_qh_set, this.ymin, this.ymax, this.high_qh);
      }),

// %%%%%%%%%%%%%%%%%%%%%%%%%%%% quarter-hour indicator

    this.$root.$on('new_hour_slider', (map_args) => {

         this.high_qh = String(map_args.hour.getUTCMonth()+1).padStart(2,'0') + '_' +
                        String(map_args.hour.getUTCDate()   ).padStart(2,'0') + '_' +
                        String(map_args.hour.getUTCHours()  ).padStart(2,'0') + ':' +
                        String(map_args.hour.getUTCMinutes()).padStart(2,'0');

        this.display_Bar_Data(this.my_corner_data, this.arr_qh_set, this.ymin, this.ymax, this.high_qh);
    })


  },

    //  editing:
    // By convention, selection methods that return the current selection use four
    // spaces of indent, while methods that return a new selection use only two.

    methods: {

/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
output of python's df.to_json(orient='split') :
  "columns": [ "arr_qh", "flw_dist" ],
  "data":    [ [ "2020_01_10_08:00", 0.0 ],
               [ "2020_01_10_13:00", 228.7225525225 ],
               [ "2020_01_10_13:15", 819.3925476606 ],
               [ "2020_01_10_13:30", 1864.0145658695 ],
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% */
        // convert input as a list of lists into an assoc array
        json2array : function(json_data) {
          let c_data   = [];
          let x_labels = [];
          //let columns = json_data.columns;
          for(var k = 0; k < json_data.data.length; k++) {

              // HELP: how to get js to use column[0] as the name???
              var item = { 'arr_qh' : json_data.data[k][0],
                           'dist'   : json_data.data[k][1]  };

              c_data.push(item);
              x_labels.push( json_data.data[k][0]);  // always the first one, right?
          }

          return( {d:c_data, x:x_labels} );
      },
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% */

/* %%%%%%%%%%%%%%%%%%%%%%  display_Bar_Data  %%%%%%%%%%%%%%%%%%%%%%%%%%%% */

        display_Bar_Data : function(simp_data, arr_qh_lbls, y_min, y_max, phigh_qh) {

  // set the dimensions and margins of the graph
  let width  = chart_width  - margin.left - margin.right;
  let height = chart_height - margin.top  - margin.bottom;

  // "svg" is apparently the name of the component _and_ the type
  //get the vector layer (unique) name of _our_ div element
  let my_div = "#svg_div_"+this.corner_data.dir;
  let my_stupid_translate = this.corner_data.offs + margin.top;

  // down inside the depths, d3 doesn't know what 'this' is, so retrieve
  // items here and pass down as explicit variables
  let my_corner_colr = this.corner_data.colr;

  // "svg" is apparently the name of the component _and_ the type
  // ---- remove previous sub-components, if any
  d3.select(my_div).selectAll("svg").remove();

  // ---- define the main div of the chart
  let svg = d3.select(my_div)
    .append("svg")
      .attr("width",  width  + margin.left + margin.right)
      .attr("height", height + margin.top  + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + my_stupid_translate + ")");

  // ---- Add X axis
  let xScale = d3.scaleBand()  // function named xScale in other examples
      .domain(arr_qh_lbls)
      .range([0, width])
      .padding([0.2])

      // https://ghenshaw-work.medium.com/customizing-axes-in-d3-js-99d58863738b
  svg.append("g")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(xScale) // x-axis generator
              .tickSizeOuter(0)
              .tickFormat((d,i) => i % 4 == 0 ? arr_qh_lbls[i] : "" )
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

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% The Chart

svg.append("g")
    .selectAll('rect')
    .data(simp_data)
    .enter()
      .append("rect")
      .attr("fill",   (d) => (d.arr_qh == phigh_qh) ? "orange" : my_corner_colr )
      //.attr("fill",   (d) => (d.arr_qh == phigh_qh) ? "orange" : 'green' )
      .attr("x",      (d) => xScale(d.arr_qh) )
      .attr("y",      (d) => yScale(d.dist)   )
      .attr("height", (d) => height - yScale(d.dist)   )
      .attr("width",  xScale.bandwidth())
      //.attr('fill',   'green')

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% mouseover
/*************
        // https://bl.ocks.org/d3noob/a22c42db65eb00d4e369
       .on("mouseover", function(event,d) {

           let disp_val = d.dist.toFixed(1)+"nm<br/>"+ d.arr_qh;

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
       ***********/
/********************
// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% legend
//  https://www.d3-graph-gallery.com/graph/custom_legend.html

// Add one square in the legend area for each color
svg.selectAll("leg_dots")
  .data(wt_subgroups)
  .enter()
  .append("rect")
    .attr("x", (d,j) => legend_x + j*(leg_size+25) )
    .attr("y", legend_y)
    .attr("width",  leg_size)
    .attr("height", leg_size)
    .style("fill",  'blue' )
    //stacked: .style("fill",  (d) => colorScale(d) )

// Add one text element in the legend area for each subgroup
svg.selectAll("leg_text")
  .data(wt_subgroups)
  .enter()
  .append("text")
    .attr("x", (d,j) => legend_x + j*(leg_size+25) + (leg_size+3) )
    .attr("y", legend_y + leg_size*0.8)
    .text( (d) => String(d).substr(0,2) )
    .attr("text-anchor", "left")
    .style("alignment-baseline", "middle")
***************/
    }   // displayGData function
  } // methods
} // export

</script>

<style lang="scss">

/* need to specify at page load so it won't be empty/ small */
/* numbers are same as in script */
/* MISSING: width: 760px; */
div.chart_simp {
  width:  960px;
  height: 250px;
  background-color: #f8f8f8;
}

span.chsmall {
  font-size: 80%;
}


div.tooltip {
    position: absolute;
    text-align: center;
    width: 80px;
    height: 38px;
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
/*** no difference: (useful for circle charts on map, however) */
svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  position: absolute; /* ??? */
}

</style>

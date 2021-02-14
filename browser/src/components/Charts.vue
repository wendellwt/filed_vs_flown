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
var wt_subgroups = [ "b4_dep_dist", "b4_ent_dist", "flw_dist"];
//var wt_subgroups = [ "first_sch_dist", "at_ent_dist", 'flown_dist' ];

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
        cadata : [],            // the chart data
        the_date: new Date(),  // in header/title
        ymin  : 0,         // chart y mimn
        ymax  : 4000         // cyart y max
      }
    },

  mounted: function() {
      this.$root.$on('new_barchart_data', (chart_args) => {
/*****************
        "ZDV": {
            "columns": [
                "index",
                "arr_qh",
                "corner",
                "b4_dep_dist",
                "b4_ent_dist",
                "flw_dist"
            ],
            "data": [
                [
                    0,
                    "2020-03-02T08:00:00.000Z",
                    "ne",
                    227.3117248064,
                    227.3117248064,
                    228.0891889659
                ],
 * ******************/
          // convert input as a list of lists into an assoc array
console.log("chart.cdata >>>>>>>>>>>:");
console.log(chart_args.cdata);
          this.cadata = [];
          for(var k = 0; k < chart_args.cdata.data.length; k++) {
            var item = { 'arr_qh'       : chart_args.cdata.data[k][1].substr(0,16),
                          'corner'      : chart_args.cdata.data[k][2],
                          'b4_dep_dist' : chart_args.cdata.data[k][3],
                          'b4_ent_dist' : chart_args.cdata.data[k][4],
                          'flw_dist'    : chart_args.cdata.data[k][5] };
//console.log("k="+k);
//console.log(item);
              this.cadata.push(item);
          }
//console.log("this.cadata");
//console.log(this.cadata);
          this.the_date = chart_args.title_date

          this.displayGData(this.cadata, this.ymin, this.ymax);
      }),

      this.$root.$on('chart_slider_vals', (chart_s_args) => {

          this.ymin = chart_s_args.slider_vals[0] * 100;
          this.ymax = chart_s_args.slider_vals[1] * 100;

          //HELPthis.displayGData(this.cadata, this.ymin, this.ymax);
      })
  },

    /**************** Charts ***************/
    /* FINALLY, an example d3 chart that works!!!:     */
    /* https://www.d3-graph-gallery.com/graph/barplot_stacked_basicWide.html */
    /**************** Charts ***************/

    methods: {
        displayGData : function(ndata, y_min, y_max) {
console.log("chart ndata-x:");
console.log(ndata);
console.log(y_min, y_max);

  // set the dimensions and margins of the graph
  let margin = {top: 10, right: 30, bottom: 20, left: 50},
      width  = 460 - margin.left - margin.right,    // WIDTH is fixed!!!
      height = 600 - margin.top  - margin.bottom;   // HEIGHT is fixed!!!

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

<style lang="scss">
.my_dataviz {
  height: 600px;
}
#my_dataviz {
  height: 600px;
}
my_dataviz {
  height: 500px;
}


</style>

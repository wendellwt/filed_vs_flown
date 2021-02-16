<template>

    <vl-overlay :id="'ovrly_'+corner_data.ident" :position="corner_data.coords"
                positioning='center-center' >
        <div :id="'svg_div_'+corner_data.ident"
              style="width: 150px; height: 150px;  background-color:#80808040">
          {{corner_data.ident}}
        </div>
    </vl-overlay>

</template>

<script>

import * as d3 from 'd3'
// overall chart size
var chart_width  = 150;
var chart_height = 150;

// ==========================================================

export default {
  name: "CornerCircBar",
  props: {
    corner_data: Object
  },
    data () {
      return {
        foo : 1
      }
    },
    /********************************************************** */
    methods: {
        displayCircularData : function(cdata, y_max) {

  // set the dimensions and margins of the graph
            // bottom margin of 80 leaves room for x-axis label rotated
  let margin = {top: 0, right: 0, bottom: 0, left: 0},
      width  = chart_width  - margin.left - margin.right,
      height = chart_height - margin.top  - margin.bottom;

  // "svg" is apparently the name of the component _and_ the type
console.log("do something with this:"+y_max);

      //get the vector layer div element
  let my_div = "#svg_div_"+this.corner_data.ident;

  // ---- remove previous sub-components, if any
  d3.select(my_div).selectAll("svg").remove();

  // ---- define the main div of the chart
  let svg = d3.select(my_div)
    .append("svg")
      .attr("width",  width  + margin.left + margin.right)
      .attr("height", height + margin.top  + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
            // Add 100 on Y translation, cause upper bars are longer

      //.attr("transform",
      //      "translate(" + margin.left + "," + margin.top + ")");

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

var   innerRadius = 20;
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
  }, // methods

// ==========================================================
// this was slightly helpful:
// https://stackoverflow.com/questions/50020722/initialize-svg-js-in-vuejs-component

  mounted () {

    this.$root.$on('draw_this_corner', (corner_datax) => {
      console.log("about to do some d3!");
      console.log(this.corner_data);
      console.log("ident:");
      console.log(this.corner_data.ident);
      let stupid_color = this.corner_data.colr;
      console.log("sc:");
      console.log(stupid_color);

      console.log(corner_datax);

      //get the vector layer div element
      let div = d3.selectAll("#svg_div_"+this.corner_data.ident);

      //remove the existing svg element and create a new one
      div.selectAll("svg").remove();

      let svg = div.append("svg")
      // and give it some dimensions and background
        .attr("width", 400)           // FIXME: these had better be same as map div, right?
        .attr("height", 400)          // FIXME
        .style('background-color', 'transparent');

      // add a 'circle' element
      svg.append("circle")
        .attr("fill", function () {return stupid_color})
        .attr("cx", 50)
        .attr("cy", 50)
         .attr("r", 50);

 console.log("part done.");
   }),
/*************************************************************/
      this.$root.$on('draw_circ_chart', (chart_args) => {
console.log("draw_circ_chart:"+this.corner_data.ident);
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

  } // ---- mounted???
}

</script>

<style lang="scss">

svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  position: absolute;
}
</style>

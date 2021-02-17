<template>

    <vl-overlay :id="'ovrly_'+corner_data.dir" :position="corner_data.coords"
                positioning='center-center' >
        <div :id="'svg_div_'+corner_data.dir"
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
    // { dir: "ne", ident: 'LANDR', coords: [-104.00, 40.35], colr: 'green' },
  },
    data () {
      return {
        my_corner_orig : [ ],
        my_corner_data : [ ]
      }
    },

    methods: {
        displayCircularData : function(cdata, y_max, corner_color) {

  // set the dimensions and margins of the graph
  let margin = {top: 0, right: 0, bottom: 0, left: 0},
      width  = chart_width  - margin.left - margin.right,
      height = chart_height - margin.top  - margin.bottom;

  // "svg" is apparently the name of the component _and_ the type
  //get the vector layer (unique) name of _our_ div element
  let my_div = "#svg_div_"+this.corner_data.dir;

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

var   innerRadius = 20;
var   outerRadius = Math.min(width, height) / 2;
            // the outerRadius goes from the middle of the SVG area to the border

  // X scale
// X axis goes from 0 to 2pi = all around the circle. If I stop at 1Pi, it will be around a half circle
  var xScale = d3.scaleBand()
      .range([0, 2 * Math.PI])
      .align(0)                  // This does nothing ?
      .domain( cdata.map( (d) => d.arr_hr ));

  // Y scale
  var yScale = d3.scaleRadial()
      .range([innerRadius, outerRadius])   // Domain will be define later.
      .domain([0, y_max]); // Domain of Y is from 0 to the max seen in the data

  // Add bars
  svg.append("g")
    .selectAll("path")
    .data(cdata)
    .enter()
    .append("path")
      //.attr("fill", function(d) {return d['dist']==30 ? "orange" : "green"})
      .attr("fill", corner_color)
      .attr("d", d3.arc()     // imagine your doing a part of a donut plot
        .innerRadius(innerRadius)
        .outerRadius( (d) => yScale(d['dist']) )
        .startAngle(  (d) => xScale(d.arr_hr)  )
        .endAngle(    (d) => xScale(d.arr_hr) + xScale.bandwidth() )
        .padAngle(0.01)
        .padRadius(innerRadius))

    } // displayGData function
  }, // methods

// ==========================================================
// this was slightly helpful:
// https://stackoverflow.com/questions/50020722/initialize-svg-js-in-vuejs-component

  mounted () {

      this.$root.$on('new_corner_data', (corner_args) => {

          this.my_corner_orig = corner_args.corner_data[this.corner_data.dir].data;

          // convert input as a list of lists into an assoc array
          this.my_corner_data = [];
          for(var k = 0; k < this.my_corner_orig.length; k++) {
            var item = { 'arr_hr' : this.my_corner_orig[k][0],
                         'dist'   : this.my_corner_orig[k][1] }
              this.my_corner_data.push(item);
          }

          this.the_date       = corner_args.title_date; // arb, prob. useless

          let wt_groups = [ ];
          for (let k = 0; k < this.my_corner_data.length; k++ ) {
                  wt_groups.push(this.my_corner_data[k].arr_hr);
          }

          let ymax = 5000; // ????

          this.displayCircularData(this.my_corner_data, ymax, this.corner_data.colr);
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

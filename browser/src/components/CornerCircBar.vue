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
    // { dir: "ne", ident: 'LANDR', coords: [-104.002963888889, 40.3575722222222], colr: 'green'  },
    corner_data: Object
  },
    data () {
      return {
        my_corner_orig : [ ],
        my_corner_data : [ ]
      }
    },
    /********************************************************** */
    methods: {
        get_my_color : function() {
            if (this.corner_data.dir == 'ne') { return '#002664';}   // RGB (0, 38, 100)
            if (this.corner_data.dir == 'se') { return '#007934';}   // RGB (0, 121, 52)
            if (this.corner_data.dir == 'sw') { return '#AB8422';}   // RGB (171, 132, 34)
            if (this.corner_data.dir == 'nw') { return '#5E6A71';}   // RGB (94, 106, 113)
            return('red');
        },

    /********************************************************** */
        displayCircularData : function(cdata, y_max, corner_color) {

  // set the dimensions and margins of the graph
            // bottom margin of 80 leaves room for x-axis label rotated
  let margin = {top: 0, right: 0, bottom: 0, left: 0},
      width  = chart_width  - margin.left - margin.right,
      height = chart_height - margin.top  - margin.bottom;

  // "svg" is apparently the name of the component _and_ the type
console.log("do something with this:"+y_max);

      //get the vector layer div element
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
      //.attr("fill", function(d) {return d['dist']==30 ? "orange" : "green"})
      //.attr("fill", function(d) {return this.get_my_color(); })
      .attr("fill", corner_color)
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

/********************* DRAW A DOT >>>>>> OLD <<<<< ***************/
    this.$root.$on('draw_this_corner', (corner_datax) => {
      console.log("about to do some d3!");
      console.log(this.corner_data);
      console.log("dir:");
      console.log(this.corner_data.dir);
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
      this.$root.$on('new_corner_data', (corner_args) => {

          this.my_corner_orig = corner_args.corner_data[this.corner_data.dir].data;
// console.log("my data is:");
// console.log(this.my_corner_data);

/*****************************
        "ne": {
            "columns": [ "arr_hour", "flw_dist" ],
            "data": [
                [ 0, 4614.9540688637 ],
                [ 1, 1769.4923150382 ],
                [ 2, 2804.1062837474 ],
        ...
                [ 23, 4880.1052169843 ]
            ],
"index": [ 0, 1, 2, 3, 4, 5, ...
        },
"nw": {
            "columns": [ "arr_hour", "flw_dist" ],
            "data": [
                [ 0, 846.185468761 ],
                [ 1, 2197.651969371 ],
                [ 2, 2619.7360797493 ],
                [ 3, 225.2490231881 ],
                [ 4, 1099.8194817083 ],
*****************************/
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

// console.log("circ data currently:");
// console.log(this.my_corner_data);
// console.log("wt_groups:");
// console.log(wt_groups);

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

<template>
  <div class="datacolumn">

<h3>Data Position List</h3>
<div class="timestamp">{{last_rcvd}}</div>

<ul id="example-1" class="scrolling" >

    <!-- create a datablock within the li for each aircraft -->
    <li  class="datalist"
       v-for="item in datablocks"
       :key="item.flt_ndx"
       @click="datablockclicked(item)" >
          {{ item.acid    }} &nbsp; &nbsp;
          {{ item.corner  }} &nbsp; &nbsp;
          {{ item.dep_apt }} &nbsp; &nbsp;
          <br/>
          <div class="dbsmall">
               {{ item.fid  }} &nbsp; &nbsp;
              ({{ item.diff }})
          </div-->
    </li>
  </ul>

  </div>
</template>

<script>

/******************
   acid:     features_list[k].properties.acid,
   fid:      features_list[k].properties.fid,
   corner:   features_list[k].properties.corner,
   dep_apt:  features_list[k].properties.dep_apt,
   diff:   ...
*********************/
export default {
    data () {
      return {
        last_rcvd: new Date(),

        datablocks : [
          { fid: 1, acid: 'N111', actype: 'C172', corner: 'ne' },
          { fid: 2, acid: 'N112', actype: 'C172', corner: 'se' },
          { fid: 3, acid: 'N113', actype: 'C172', corner: 'sw' },
          { fid: 4, acid: 'N114', actype: 'C172', corner: 'nw' },
          { fid: 5, acid: 'N115', actype: 'C172', corner: 'ne' } ]
      }
    },

  mounted () {

      this.$root.$on('dlist', (dlist) => {
      // console.log("DataPos received dlist");

      // FIXME: find out how/why PostGIS allowed duplicate track
      // why do we need to do this here?: remove duplicate key / track
      // WAIT: is this an old hold-over from asdex ops???

      this.datablocks = dlist;  // no FID yet???
      //this.datablocks = this.removeDuplicates(dlist, 'fid');

    })
  },

  methods: {

  // =========================
  // https://firstclassjs.com/remove-duplicate-objects-from-javascript-array-how-to-performance-comparison/
  removeDuplicates: function(array, key) {
    return array.filter((obj, index, self) =>
        index === self.findIndex((el) => (
            el[key] === obj[key]
        ))
    )
 },
 // =========================

  datablockclicked: function(item) {

        console.log("highlightthis-emit:" + item.fid + ":" + item.acid); // + "_" + item.actype);

        this.$root.$emit('highlightthis', (item.fid) );
    }
  }
}

</script>

<style lang="scss">
/* https://www.w3schools.com/css/default.asp */

div.datacolumn {
    background-color: #ffecb3;
}

div.timestamp {
  font-size: 70%;
}

div.dbsmall {
  font-size: 70%;
}

li.datalist {
    border-style: solid;
    border-color: brown;
    background-color: #e6ffcc;

    margin-top: 2px;
    margin-bottom: 2px;
}

ul.scrolling {
        max-height: 500px;
        overflow: scroll;
}

</style>


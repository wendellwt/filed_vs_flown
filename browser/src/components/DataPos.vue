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
              {{ item.flt_ndx }} &nbsp; &nbsp;
              {{ item.actype  }} &nbsp; &nbsp;
              {{ item.adist   }} &nbsp; &nbsp;
              {{ item.fdist   }} &nbsp; &nbsp;
              ({{ item.diff   }})
          </div>
    </li>
  </ul>

  </div>
</template>

<script>

export default {
    data () {
      return {
        last_rcvd: new Date(),

        datablocks : [
          { flt_ndx: 1, acid: 'N111', actype: 'C172', corner: 'ne' },
          { flt_ndx: 2, acid: 'N112', actype: 'C172', corner: 'se' },
          { flt_ndx: 3, acid: 'N113', actype: 'C172', corner: 'sw' },
          { flt_ndx: 4, acid: 'N114', actype: 'C172', corner: 'nw' },
          { flt_ndx: 5, acid: 'N115', actype: 'C172', corner: 'ne' } ]
      }
    },

  mounted () {

      this.$root.$on('dlist', (dlist) => {
      // console.log("DataPos received dlist");

      // FIXME: find out how/why PostGIS allowed duplicate track
      // why do we need to do this here?: remove duplicate key / track
      // WAIT: is this an old hold-over from asdex ops???

      this.datablocks = this.removeDuplicates(dlist, 'flt_ndx');
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

        console.log("highlightthis-emit:" + item.flt_ndx + ":" + item.acid + "_" + item.actype);

        this.$root.$emit('highlightthis', (item.flt_ndx) );
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
        max-height: 400px;
        overflow: scroll;
}

</style>


<template>
  <div class="datacolumn">

<b>Data Position List</b>
<!-- div class="timestamp">{{last_rcvd}}</div> TOO LONG -->
&nbsp; &nbsp; &nbsp;
    <b-dropdown :triggers="['hover']"
                aria-role="list"
                v-model="sort_selected" >
        <button class="button is-light is-small" slot="trigger">
            <span>sort</span>
            <b-icon icon="menu-down"></b-icon>
        </button>
            <b-dropdown-item  v-for="srt_by_v in sort_list"
                              v-bind:value="srt_by_v"
                              :key="srt_by_v">{{ srt_by_v }}
            </b-dropdown-item>
    </b-dropdown>

<ul id="example-1" class="scrolling" >

    <!-- ====================================================== -->

    <!-- create a datablock within the li for each aircraft -->
    <li    class="datalist"
           v-bind:class="item.corner"
           v-for="item in datablocks"
           :key="item.flt_ndx"
           @click.exact="datablockclicked(item)"
           @click.ctrl.exact="datablockclicked_ctrl(item)" >

           <span v-if="fids_selected.includes(item.fid)" class="highlt">{{ item.acid }}</span>
           <span v-else                                                >{{ item.acid }}</span>
           &nbsp; &nbsp;
           {{ item.corner     }} &nbsp; &nbsp;
           <span v-if="sort_selected=='flown in artcc'"><b>{{ item.flw_dist_f }}</b></span>
           <span v-if="sort_selected=='arr time'"      >{{    item.flw_dist_f }}</span>
         <br/>
         <div class="dbsmall">
            {{ item.dep_apt  }} &nbsp; &nbsp;
           <span v-if="sort_selected=='flown in artcc'">{{    item.arr_time }}</span>
           <span v-if="sort_selected=='arr time'"      ><b>{{ item.arr_time }}</b></span>
            &nbsp; &nbsp;
            {{ item.ac_type   }} &nbsp; &nbsp;
            <br/>
            s:{{ item.sch_dist_f }} &nbsp;
            f:{{ item.fld_dist_f }} &nbsp;
            d:{{ item.dep_dist_f }} &nbsp;
            e:{{ item.ent_dist_f }} &nbsp;
            t:{{ item.flw_dist_f }}

         </div>

       <!-- BAD li SIZE:  div>
           <span class="dblft">{{ item.acid       }}</span>
           <span class="dbctr">{{ item.corner     }}</span>
           <span class="dbrgt">{{ item.flw_dist_f }}</span>
         <br/>
         <div class="dbsmall">
            <span class="dblft">{{ item.dep_apt  }}</span>
            <span class="dbctr">{{ item.arr_time }}</span>
            <span class="dbrgt">({{ item.diff     }})</span>
         </div>
        </div -->
    </li>
    <!-- ====================================================== -->
  </ul>

  </div>
</template>

<script>

  /***************************************************************/

export default {
    data () {
      return {
        last_rcvd     : new Date(),
        sort_selected : "flown in artcc",
        sort_list     : ["flown in artcc", "arr time"],
        srt_by        : "flown",

        datablocks : [
          { fid: 1, acid: 'N111', actype: 'C172', corner: 'ne' },
          { fid: 2, acid: 'N112', actype: 'C172', corner: 'se' },
          { fid: 3, acid: 'N113', actype: 'C172', corner: 'sw' },
          { fid: 4, acid: 'N114', actype: 'C172', corner: 'nw' },
          { fid: 5, acid: 'N115', actype: 'C172', corner: 'ne' } ],

        fids_selected : [ ]  // list of fids to highlight
      }
    },

  /***************************************************************/

  mounted () {

      this.$root.$on('dlist', (dlist) => {
      // console.log("DataPos received dlist");

      // FIXME: find out how/why PostGIS allowed duplicate track
      // why do we need to do this here?: remove duplicate key / track
      // WAIT: is this an old hold-over from asdex ops???

      this.datablocks = dlist;  // DEFAULT???

          if (this.sort_selected == "flown in artcc") {
              this.datablocks = this.sort_by_flown_dist(dlist);
              //console.log("by dist");
          }

          if (this.sort_selected == "arr time") {
              this.datablocks = this.sort_by_arr_time(dlist);
              //console.log("by time");
          }
    })
  },

  /***************************************************************/

  watch: {
      sort_selected: function() {

          console.log("sort by:"+this.sort_selected);

          if (this.sort_selected == "flown in artcc") {
              this.datablocks = this.sort_by_flown_dist(this.datablocks);
              //console.log("by dist");
          }

          if (this.sort_selected == "arr time") {
              this.datablocks = this.sort_by_arr_time(this.datablocks);
              //console.log("by time");
          }
      }
  },

  /***************************************************************/

  methods: {

  // ========================= =========================

      sort_by_flown_dist : function(dlist) {

          let sortedlist = dlist.sort(function(a, b) {
              let a_srt = parseFloat(a.flw_dist_f);
              let b_srt = parseFloat(b.flw_dist_f);
              if (a_srt < b_srt) { return -1; }
              if (a_srt > b_srt) { return  1; }
              return 0;  // names must be equal
           });
           return(sortedlist);
    },

  // ========================= =========================

      sort_by_arr_time : function(dlist) {
          let sortedlist = dlist.sort(function(a, b) {
              let a_srt = a.arr_time;   // UNITS???
              let b_srt = b.arr_time;
              if (a_srt < b_srt) { return -1; }
              if (a_srt > b_srt) { return  1; }
              return 0;  // names must be equal
           });
           return(sortedlist);
    },

  // ========================= =========================

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

        console.log("highlightthis-emit:" + item.fid + ":" + item.acid);

        this.fids_selected = [ item.fid ];

console.log("fids_selected:"+this.fids_selected);
        this.$root.$emit('highlightthis', this.fids_selected );
  },

 // =========================

  datablockclicked_ctrl: function(item) {

        console.log("highlightthis_CTRL-emit:" + item.fid + ":" + item.acid);

        this.fids_selected.push( item.fid );  // TODO: REMOVE DUPLICATES!!!

console.log("fids_selected:"+this.fids_selected);
        this.$root.$emit('highlightthis', this.fids_selected );
    }
  }
}

</script>

<style lang="scss">
/* https://www.w3schools.com/css/default.asp */

div.datacolumn { background-color: #ffecb3; }
div.timestamp  { font-size: 70%; }
div.dbsmall    { font-size: 70%; }


li.datalist {
    border-style:     solid;
    background-color: #e6ffcc;

    margin-top:    2px;
    margin-bottom: 2px;
    cursor: pointer;
}

li.ne { border-color:  #002664; }
li.se { border-color:  #007934; }
li.sw { border-color:  #AB8422; }
li.nw { border-color:  #5E6A71; }

span.highlt { color: blue; font-weight: bold ; }
span.dblft { float: left; width: 33.333%; text-align: left  ; }
span.dbctr { float: left; width: 33.333%; text-align: center; }
span.dbrgt { float: left; width: 33.333%; text-align: right ; }

ul.scrolling {
        max-height: 500px;
        overflow: scroll;
}

</style>


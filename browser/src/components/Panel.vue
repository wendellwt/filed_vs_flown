<template>

<nav class="panel">
  <p class="panel-heading">
    Retrieve Dataset
  </p>
  <div class="panel-block">
      <!-- FIXME:  put label left of entry ===================== -->
      <b-field label="Date">
          <b-datepicker
            placeholder="Click to select..."
             v-model="sel_date"
             :min-date="our_min_date"
             :max-date="our_max_date"
             maxlength=11
            >
          </b-datepicker>
        </b-field>
  </div>

        <!-- ========== arrival ========= -->
        <div class="panel-block">
          <div class="columns">
            <div class="column is-three-quarters">
              <b-dropdown :triggers="['hover']" aria-role="list"
                    v-model="arr_selected" >
              <button class="button is-light is-small" slot="trigger">
                <span>Arrival</span>
                <b-icon icon="menu-down"></b-icon>
              </button>

              <b-dropdown-item  v-for="apt in airportlist"
                          v-bind:value="apt"
                          :key="apt">{{ apt }}</b-dropdown-item>
              </b-dropdown>
            </div>
            <div class="column">{{arr_selected}}</div>
          </div>
       </div>
        <!-- ========== center ========= -->
        <div class="panel-block">
          <div class="columns">
            <div class="column is-three-quarters">
              <b-dropdown :triggers="['hover']" aria-role="list"
                    v-model="center_selected" >
              <button class="button is-light is-small" slot="trigger">
                <span>Center</span>
                <b-icon icon="menu-down"></b-icon>
              </button>

              <!-- b-dropdown-item  v-for="ctr in centerlist"
                          v-bind:value="ctr"
                          :key="ctr">{{ ctr }}</b-dropdown-item>
              </b-dropdown -->

              <b-dropdown-item  v-for="ctr in tierlist"
                          v-bind:value="ctr[0]"
                          :key="ctr[0]">{{ ctr[1] }}</b-dropdown-item>
              </b-dropdown>

            </div>
            <div class="column">{{center_selected}}</div>
          </div>
       </div>

        <!-- ========== brought over from AppUI ========= -->

        <div class="panel-block">

          <b-button type='is-info'
                    size="is-small"
                    :loading.sync="go_button_loading"
                    rounded
                    v-on:click="GoEverything()"
                    >GET DATA</b-button>
                &nbsp; &nbsp; &nbsp;
            <b-checkbox type="is-info"
                        size="is-small"
                        v-model="use_pickle">use pickle</b-checkbox>
        </div>
        <div class="panel-block">

          <b-button type="is-danger is-light"
                    size="is-small"
                    rounded
                    v-on:click="CallAFunction_draw_circle()"
                    >draw_circle()</b-button>
          <b-button type="is-danger is-light"
                    size="is-small"
                    rounded
                    v-on:click="CallAFunction_fvf_geojson()"
                    >fvf_geojson()</b-button>

        </div>

  <p class="panel-heading">
    Analyze Dataset
  </p>
        <!-- ========== hour slider ========= -->
        <div class="panel-block">
          <b-field label="Hour of map">
              <b-slider size="is-medium" :min="0" :max="23"
                            type="is-info"
                            v-model="hour_val"
                  >
              </b-slider>
          </b-field>
       </div>
        <!-- ========== max/min slider ========= -->
        <div class="panel-block">
          <b-field label="min/max chart y-axis">
              <b-slider size="is-medium" :min="0" :max="70"
                            type="is-info"
                            v-model="slider_vals"
                  >
              </b-slider>
          </b-field>
        </div>
        <!-- ========== end ========= -->

  </nav>
</template>

<script>

// a file captured from ./everything.py over on rserver:
// not for flask:
//import sample_json_data from "./files/output_everything.json";
//import e_zdv from "./files/e_ZDV.json";
import e_feb from "./files/e_2020_01_10.json";
//soon: import e_zlc from "./files/e_ZLC.json";

export default {
  name: 'panel',
  prop: ['valid'],

  data () {
      return {
        our_min_date: new Date("2020-01-01"),  // the only ones we've run so far
        our_max_date: new Date("2020-12-31"),  // the only ones we've run so far

        arr_selected: "DEN",
        center_selected: "ZDV",
        sel_date: new Date('January 10, 2020 14:00:00'),  // start???

        airportlist: [ "DEN", "DFW" ],  // the only ones we've run so far
        // centerlist: [ "ZDV", "ZFW", "ZLA", 'ZKC', 'ZME' ],

        tierlist: [ ["ZDV",  "ZDV (parent)"  ],

                    ["ZKC",  "ZKC (1st tier)" ],
                    ["ZMP",  "ZMP (1st tier)" ],
                    ["ZLC",  "ZLC (1st tier)" ],
                    ["ZLA",  "ZLA (1st tier)" ],
                    ["ZAB",  "ZAB (1st tier)" ],

                    ["ZFW",  "ZFW (2nd tier)" ],
                    ["ZME",  "ZME (2nd tier)" ],
                    ["ZID",  "ZID (2nd tier)" ],
                    ["ZAU",  "ZAU (2nd tier)" ],
                    ["ZSE",  "ZSE (2nd tier)" ],
                    ["ZOA",  "ZOA (2nd tier)" ],
                    ["ZHU",  "ZHU (2nd tier)" ] ],

        slider_vals : [0,70],

        hour_val   : 5,                   // from ui chooser
        y_m_d_val  : "2020_12_04",        // intermediate/temp value
        y_m_dt_val : "2020-12-04T18",     // portion of ISO time string to match
        y_m_da_val : "2020_12_04_05",     // arrival time is rounded to this
        y_m_dd_val : "2020-12-04 05:00",  // display on Chart component

        all_json_data: [],  // the (large) json received from server
        details_data : [],  // fetched data from everything.py
        chart_data   : [],  // fetched data from everything.py
        map_data     : [],  // fetched data from everything.py
        fe_data      : [],  // fetched data from everything.py
        ate_data     : [],  // fetched data from everything.py

        hourly_data  : [],  // set of chart_data for selected hour
        go_button_loading : false,
        use_pickle : false
   }
  },
    watch: {

        // slider vals changed; tell Chart component, but don't need to recalc hourly list
        slider_vals: function(vals) {

            this.slider_vals  = vals ; // redundant???

            if (this.hourly_data.length > 0 ) {
                let chart_args = { cdata: this.hourly_data, slider_vals : this.slider_vals };
                this.$root.$emit('draw_new_chart', (chart_args) );
            } else {
                console.log("nothing to chart");
            }

            // =========== caroline chart ==============
            this.set_and_show_flown_and_entry();

           this.CallAFunction_draw_circle();
        },

        // hour selector changed, CALC NEW chart and map data
        hour_val: function(hval) {

            this.hour_val  = hval ; // redundant???
            // almost like the other, but '-' and 'T' instead of '_' and ' '

            this.y_m_d_val =  this.sel_date.getUTCFullYear() + '_' +
                       String(this.sel_date.getUTCMonth()+1).padStart(2,'0') + '_' +
                       String(this.sel_date.getUTCDate()   ).padStart(2,'0');

            this.y_m_da_val =  this.y_m_d_val + '_' + String(this.hour_val).padStart(2,'0');
            this.y_m_dd_val =  this.y_m_d_val + ' ' + String(this.hour_val).padStart(2,'0') + ":00";

            this.y_m_dt_val =  this.sel_date.getUTCFullYear() + '-' +
                        String(this.sel_date.getUTCMonth()+1).padStart(2,'0') + '-' +
                        String(this.sel_date.getUTCDate()   ).padStart(2,'0') + 'T' +
                        String(this.hour_val).padStart(2,'0');

            // ---- tell Map component

            // new fvf: let map_args = { mdata: this.map_data, hour : this.y_m_dt_val };
            let map_args = { mdata: this.map_data[this.center_selected],
                             hour : this.y_m_dt_val };
            this.$root.$emit('draw_all_fc', (map_args) );

            // ---- tell Chart component

            //csv: this.set_and_show_hourly_data() // ???????

            // =========== caroline chart ==============

            this.set_and_show_flown_and_entry();
        }
    },
    methods: {

      form_fetch_args() {

        let udate =        this.sel_date.getUTCFullYear() + '_' +
                    String(this.sel_date.getUTCMonth()+1).padStart(2,'0')  + '_' +
                    String(this.sel_date.getUTCDate()   ).padStart(2,'0');

        //don't I wish: let udate = "&date=" + this.sel_date.strftime("%Y_%m_%d");

        let force_reload = Math.floor(Math.random() * 99999);

        let the_query = "get_everything" +
                        "?apt="  + this.arr_selected +
                        "&ctr="  + this.center_selected +
                        "&date=" + udate +
                        "&rand=" + force_reload +
                        "&pckl=" + this.use_pickle;

        console.log("fetch:" + the_query);

        return(the_query);
    },

    // =========== fetch respose ==============

    process_fetch_response(data) {

        this.all_json_data= data;  // save everything there is
        //this.map_data     = data.map_data[this.center_selected];
        //this.chart_data   = data.chart_data[this.center_selected];
        this.details_data = data.details_data[this.center_selected];
        //this.fe_data      = data.flw_chart_data[this.center_selected];
        //this.ate_data     = data.ate_chart_data[this.center_selected];

        // =========== chart details ==============

        //csv: this.set_and_show_hourly_data();

        // =========== OL FeatureCollection ==============

        // ---- tell Map component

        let map_args = { mdata: this.map_data,
                         hour : this.y_m_dt_val };
        this.$root.$emit('draw_all_fc', (map_args) );

        // =========== table details ==============

        this.$root.$emit('draw_new_details', (this.details_data) );

        // =========== caroline chart ==============

        this.set_and_show_flown_and_entry();
    },

    // -----------------------------------------------
    // ----------- everything processing  ---------
    // --------------------------------------------
    GoEverything() {

        if (this.use_pickle==true) {
          console.log("NOT doing anything here.")
          // not for flask: this.process_fetch_response(sample_json_data);
          return;
        }
        let the_query = this.form_fetch_args()

        // =========== fetch / response ==============

        document.body.style.cursor='wait';
        this.go_button_loading = true;

         // don't know which gzip might work...
        // content-encoding may be just for POST when SENDING to server...

// Q: need to manually gzip on server???
// https://stackoverflow.com/questions/9622998/how-to-use-content-encoding-gzip-with-python-simplehttpserver

    fetch(the_query, { headers: { 'Content-Type': 'application/json',
                                  'Content-Encoding': 'gzip',
                                  'Accept-Encoding' : 'gzip'          }})
        .then(response => response.json())
        .then(data => {
            document.body.style.cursor='default';
            this.go_button_loading = false;

            this.process_fetch_response(data);

        })
       .catch((error) => {
           document.body.style.cursor='default';
            this.go_button_loading = false;
           alert('Error:', error);
           console.error('Error:', error);
       });
    },
    // ---------------------------------------
    // --------------------------------------------

/*********************
                       arr_hr corner  first_sch_dist  at_ent_dist  flown_dist
0   2020_01_10_03     ne          2580.2       2550.9      2567.3
1   2020_01_10_03     nw           147.8        147.8       174.9
2   2020_01_10_03     se          1567.8       1521.4      1562.0
3   2020_01_10_03     sw           707.0        678.6       678.7
4   2020_01_10_04     ne          2321.1       2322.5      2329.6
*********************/

    // use GLOBALS this.chart_data and this.hour_val to construct
    //  new this.hourly_data and call chart func

    set_and_show_hourly_data() {

        // console.log("hr-a=" + this.y_m_da_val);

        // form new hourly dataset
        this.hourly_data = [ ];
        for (let k = 0; k < this.chart_data.length; k++ ){
            if (this.chart_data[k].arr_hr == this.y_m_da_val) {
                this.hourly_data.push( this.chart_data[k] );
            }
        }

        let chart_args = { cdata       : this.hourly_data,
                           slider_vals : this.slider_vals,
                           title_date  : this.y_m_dd_val   };

        this.$root.$emit('draw_new_chart', (chart_args) );
    },

    // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    CallAFunction_fvf_geojson() {
console.log("CallAFunction - feb geojson");
console.log(e_feb);

this.process_fetch_response(e_feb);
console.log(this.y_m_dt_val);
console.log("data to show:"+this.center_selected);
console.log(this.map_data);
          // not for flask:
        let map_args = { mdata: this.map_data,
                         hour : this.y_m_dt_val };
        this.$root.$emit('draw_all_fc', (map_args) );
console.log("new emit");
    },

    // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    CallAFunction_draw_circle() {
console.log("CallAFunction - circular");

        let circ_data = [
            { 'arr_hr' :  0, 'dist' : 10 },
            { 'arr_hr' :  1, 'dist' : 40 },
            { 'arr_hr' :  2, 'dist' : 30 },
            { 'arr_hr' :  3, 'dist' : 50 },
            { 'arr_hr' :  4, 'dist' : 40 },
            { 'arr_hr' :  5, 'dist' : 10 },
            { 'arr_hr' :  6, 'dist' : 30 },
            { 'arr_hr' :  7, 'dist' : 20 },
            { 'arr_hr' :  8, 'dist' : 30 },
            { 'arr_hr' :  9, 'dist' : 20 },
            { 'arr_hr' : 10, 'dist' : 40 },
            { 'arr_hr' : 11, 'dist' : 20 },
            { 'arr_hr' : 12, 'dist' : 10 },
            { 'arr_hr' : 13, 'dist' : 20 },
            { 'arr_hr' : 14, 'dist' : 30 },
            { 'arr_hr' : 15, 'dist' : 50 },
            { 'arr_hr' : 16, 'dist' : 40 },
            { 'arr_hr' : 17, 'dist' : 30 },
            { 'arr_hr' : 18, 'dist' : 10 },
            { 'arr_hr' : 19, 'dist' : 20 },
            { 'arr_hr' : 20, 'dist' : 10 },
            { 'arr_hr' : 21, 'dist' : 30 },
            { 'arr_hr' : 22, 'dist' : 20 },
            { 'arr_hr' : 23, 'dist' : 10 } ];

            let chart_args = { cdata       : circ_data,
                               slider_vals : this.slider_vals,
                               title_date  : this.y_m_dd_val   };
console.log("emit circ:");
            this.$root.$emit('draw_circ_chart', (chart_args) );
    },

        /*********************************************************************/
    set_and_show_flown_and_entry() {
console.log("set_and_show_flown_and_entry -- fvf");

        //if (this.fe_data.length > 0 ) {
          // FIXME: s.b. 0 !!!!!!!!!!!
          if (this.map_data.features.length > 99999) {
            let chart_args = { cdata       : this.map_data, // this.fe_data,
                               atedata     : this.ate_data,
                               slider_vals : this.slider_vals,
                               title_date  : this.y_m_dd_val   };
console.log("emit fe:");
            this.$root.$emit('draw_fe_chart', (chart_args) );

        } else {
            console.log("nothing to chart");
        }

    }
        // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  }
}
</script>

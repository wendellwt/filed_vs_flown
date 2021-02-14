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
                    v-on:click="GoEverything_feb()"
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
          <!-- b-button type="is-danger is-light"
                    size="is-small"
                    rounded
                    v-on:click="CallAFunction_fvf_geojson()"
                    >fvf_geojson()</b-button -->

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
        y_m_d_val  : "2020_03_02",        // intermediate/temp value
        y_m_dt_val : "2020-03-02T18",     // portion of ISO time string to match
        y_m_da_val : "2020_03_02_05",     // arrival time is rounded to this
        y_m_dd_val : "2020-03-03 05:00",  // display on Chart component

        hourly_data  : [],  // set of chart_data for selected hour
        go_button_loading : false,
        use_pickle : false
   }
  },
    watch: {

        // slider vals changed; tell Chart component, but don't need to recalc hourly list
        slider_vals: function(vals) {
console.log("slider:"+vals+" this="+this.slider_vals);
            //this.slider_vals  = vals ; // redundant???  TIGHT LOOP???

            if (this.hourly_data.length > 0 ) {
                let chart_args = { cdata: this.hourly_data, slider_vals : this.slider_vals };
                this.$root.$emit('draw_new_chart', (chart_args) );
            } else {
                console.log("nothing to chart");
            }

            // =========== caroline chart ==============
            //loop: this.set_and_show_flown_and_entry();

           //loop: this.CallAFunction_draw_circle();
        },

        // hour selector changed, CALC NEW chart and map data
        hour_val: function(hval) {
console.log("hour:"+hval+" this="+this.hour_val);
            //this.hour_val  = hval ; // redundant???  TIGHT LOOP???
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

            let hour_args = { hour : this.y_m_dt_val };

            this.$root.$emit('new_hour_slide', (hour_args) );

            // ---- tell Chart component

            //csv: this.set_and_show_hourly_data() // ???????

            // =========== caroline chart ==============

            // NOT TODAY: this.set_and_show_flown_and_entry();
        }
    },
    methods: {

    // -----------------------------------------------
    // ----------- everything processing  ---------
    // --------------------------------------------

    GoEverything_feb() {

console.log('aaaaaaaaaaaa')
        let fetch_args = { sel_date    : this.sel_date,
                           arr_apt     : this.arr_selected,
                           center      : this.center_selected,
                           pickle      : this.use_pickle   };

        this.$root.$emit('fetch_data', (fetch_args) );
    },
    // ---------------------------------------

    // use GLOBALS this.chart_data and this.hour_val to construct
    //  new this.hourly_data and call chart func

    set_and_show_hourly_data() {
console.log("set and sshow");
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
   // CALLED BY:
   //   * process_fetch_data
   //   * hour slider
   //   * high/low slider
   set_and_show_flown_and_entry() {
console.log("set_and_show_flown_and_entry -- fvf");
/*********************************
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
***************************/
    }
        // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  },
  mounted () {

  // Model's fetch needs to tell when to turn off spin button
  this.$root.$on('go_button_loading', (gbl_val) => {
        this.go_button_loading = gbl_val;
    })

  }
}
</script>

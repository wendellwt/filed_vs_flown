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
             v-model="date_selected"
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
                            v-model="hour_selected"
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
var zdv_tiers = [ ["ZDV",  "ZDV (parent)"   ],
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
                  ["ZHU",  "ZHU (2nd tier)" ]  ];

export default {
  name: 'panel',
  prop: ['valid'],

  data () {
      return {
        our_min_date: new Date("2020-01-01"),  // the only ones we've run so far
        our_max_date: new Date("2021-05-31"),  // the only ones we've run so far

        arr_selected    : "DEN",
        center_selected : "ZDV",
        date_selected   : new Date('March 2, 2020 14:00:00'),  // start???

        airportlist: [ "DEN", "DFW" ],  // the only ones we've run so far

        tierlist: zdv_tiers,

        slider_vals : [0,70],

        hour_selected   : 5,                   // from ui chooser
        y_m_d_h_m       : new Date(Date.UTC(2020,3-1,2,15,0,0)),
        go_button_loading : false,
        use_pickle : false
   }
  },
    watch: {

        // slider vals changed; tell Chart component, but don't need to recalc hourly list
        slider_vals: function() {

            let chart_s_args = { slider_vals : this.slider_vals };
            this.$root.$emit('chart_slider_vals', (chart_s_args) );
        },

        // hour selector changed, CALC NEW chart and map data
        hour_selected: function() {

            this.y_m_d_h_m =  new Date(Date.UTC(
                              this.date_selected.getUTCFullYear(),
                              this.date_selected.getUTCMonth(),
                              this.date_selected.getUTCDate(),
                              this.hour_selected,   // HOUR is from slider
                              0, 0));   // MINUTE is zero!

            // ---- tell Map component
            let hour_args = { hour : this.y_m_d_h_m };
//console.log("new_hour_slider:emit:"+this.y_m_d_h_m);
            this.$root.$emit('new_hour_slider', (hour_args) );

        }
    },

    // -----------------------------------------------
    methods: {

    GoEverything_feb() {

        let fetch_args = { sel_date  : this.date_selected,
                           arr_apt   : this.arr_selected,
                           center    : this.center_selected,
                           pickle    : this.use_pickle   };

        this.$root.$emit('fetch_data', (fetch_args) );
    },
    // ---------------------------------------

    CallAFunction_draw_circle() { // DEBUGGING <<<<<<<<<<<<<<<<<<<

            let chart_args = { cdata       : "use_local_data",
                               slider_vals : this.slider_vals,
                               title_date  : this.y_m_dd_val   };
console.log("emit circ:");
            this.$root.$emit('draw_circ_chart', (chart_args) );
    },

  },
  mounted () {

  // Model's fetch needs to tell when to turn off spin button
  this.$root.$on('go_button_loading', (gbl_val) => {
        this.go_button_loading = gbl_val;
    })

  }
}
</script>

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
             :selectable-dates="populated_dates"
             maxlength=11
            >
          </b-datepicker>
        </b-field>
  </div>

        <!-- ========== arrival ========= -->
        <div class="panel-block">
          <div class="columns">
            <div class="column is-three-quarters">
              <b-dropdown :triggers="['click']" aria-role="list"
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

        <!-- ========== Path Type ========= -->
        <div class="panel-block">
          <div class="columns">
            <div class="column is-three-quarters">
              <b-dropdown :triggers="['click']" aria-role="list"
                    v-model="ptype_selected" >
              <button class="button is-light is-small" slot="trigger">
                <span>Path type</span>
                <b-icon icon="menu-down"></b-icon>
              </button>

              <b-dropdown-item  v-for="ptype in ptypelist"
                          v-bind:value="ptype[0]"
                          :key="ptype[0]">{{ ptype[1] }}</b-dropdown-item>
              </b-dropdown>

            </div>
            <div class="column">{{ptype_selected}}</div>
          </div>
       </div>


        <!-- ========== center ========= -->
        <div class="panel-block">
          <div class="columns">
            <div class="column is-three-quarters">
              <b-dropdown :triggers="['click']" aria-role="list" :disabled="center_disabled"
                    v-model="center_selected" >
              <button class="button is-light is-small" slot="trigger">
                <span>Center</span>
                <b-icon icon="menu-down"></b-icon>
              </button>

              <b-dropdown-item  v-for="ctr in tierlist"
                          v-bind:value="ctr[0]"
                          :key="ctr[0]">{{ ctr[1] }}</b-dropdown-item>
              </b-dropdown>

            </div>
            <div class="column">{{center_selected}}</div>
          </div>
       </div>
        <!-- ========== center ========= -->
        <div class="panel-block">
          <div class="columns">
            <div class="column is-three-quarters">
              <b-dropdown :triggers="['click']" aria-role="list"
                    v-model="source_selected" >
              <button class="button is-light is-small" slot="trigger">
                <span>Source</span>
                <b-icon icon="menu-down"></b-icon>
              </button>

              <b-dropdown-item  v-for="src in sourcelist"
                          v-bind:value="src[0]"
                          :key="src[0]">{{ src[1] }}</b-dropdown-item>
              </b-dropdown>

            </div>
            <div class="column">{{source_selected}}</div>
          </div>
       </div>


        <!-- ========== brought over from AppUI ========= -->

        <div class="panel-block">

          <b-button type='is-info'
                    size="is-small"
                    :loading.sync="go_button_loading"
                    rounded
                    v-on:click="GoEverything_feb20()"
                    >GET DATA</b-button>
                &nbsp; &nbsp; &nbsp;
            <b-checkbox type="is-info"
                        size="is-small"
                        v-model="use_pickle">use pickle</b-checkbox>
        </div>
        <div class="panel-block">

        </div>

  <p class="panel-heading">
    Analyze Dataset
  </p>
        <!-- ========== hour slider ========= -->
        <div class="panel-block">
          <b-field label="opsday quarter hour">
              <b-slider size="is-small" :min="0" :max="24*4-1"
                            indicator
                            type="is-info"
                            v-model="hour_slider_val"
                            :custom-formatter="val => opsday(val)"
                  >
              </b-slider>
          </b-field>
       </div>
        <!-- ========== max/min slider ========= -->
        <div class="panel-block">
          <b-field label="max chart y-axis">
              <b-slider size="is-small" :min="0" :max="70"
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

                  //["ZFW",  "ZFW (2nd tier)" ],
                  //["ZME",  "ZME (2nd tier)" ],
                  //["ZID",  "ZID (2nd tier)" ],
                  ["ZAU",  "ZAU (2nd tier)" ]
                  //["ZSE",  "ZSE (2nd tier)" ],
                  //["ZOA",  "ZOA (2nd tier)" ],
                  //["ZHU",  "ZHU (2nd tier)" ]
                    ];
var path_types = [ ["full",   "depart -> tracon"],
                   ["within", "within ARTCC"],
                   ["upto",   "upto ARTCC"] ];

var source_types = [ ["sched", "scheduled"],
                     ["filed", "first filed"],
                     ["depart", "last file before depart"] ,
                     ["at_ent", "active at artcc entry"],
                     ["flown",  "flown"] ];

var source_types_f = [ ["sched", "scheduled"],
                       ["filed", "first filed"],
                       ["depart", "last file before depart"] ,
                       //["at ent", "meaningless if full path"],
                       ["flown",  "flown"] ];

export default {
  name: 'panel',
  prop: ['valid'],

  data () {
      return {
        our_min_date: new Date("2019-01-01"),  // the only ones we've run so far
        our_max_date: new Date("2021-05-31"),  // the only ones we've run so far

        arr_selected    : "DEN",
        center_selected : "ZDV",
        center_disabled : false,
        ptype_selected  : "within",
        source_selected : "flown",
        date_selected   :   new Date(2020, 1-1, 4),
        populated_dates : [

// should use psqlcssi and sed for this:
 new Date(2020,  1-1,  1),
 new Date(2020,  1-1,  2),
 new Date(2020,  1-1,  3),
 new Date(2020,  1-1,  4),
 new Date(2020,  1-1,  5),
 new Date(2020,  1-1,  6),
 new Date(2020,  1-1,  7),
 new Date(2020,  1-1,  8),
 new Date(2020,  1-1,  9),
 new Date(2020,  1-1, 10),
 new Date(2020,  1-1, 11),
 new Date(2020,  1-1, 12),
 new Date(2020,  1-1, 13),
 new Date(2020,  1-1, 14),
 new Date(2020,  1-1, 15),
 new Date(2020,  1-1, 16),
 new Date(2019,  8-1,  1),
 new Date(2019,  8-1,  2),
 new Date(2019,  8-1,  3),
 new Date(2019,  8-1,  4)
            ],

        airportlist   : [ "DEN", "DFW" ],  // the only ones we've run so far
        tierlist      : zdv_tiers,
        ptypelist     : path_types,
        sourcelist    : source_types,

        slider_vals       : [0,40],
        hour_slider_val   : 15*4,             // from ui chooser
        y_m_d_h_m         : new Date(Date.UTC(2020,1-1,4,23,30,0)),
        go_button_loading : false,
        use_pickle        : false,


   }
  },
    watch: {
        ptype_selected: function() {
          if (this.ptype_selected == "full") {
            this.center_disabled = true;
            this.sourcelist = source_types_f;
          } else {
            this.center_disabled = false;
            this.sourcelist = source_types;
          }
        },

        // slider vals changed; tell Chart component, but don't need to recalc hourly list
        slider_vals: function() {

            let chart_s_args = { slider_vals : this.slider_vals };

//console.log("emit: new_slider_vals");

            this.$root.$emit('chart_slider_vals', (chart_s_args) );
        },

        // hour selector changed, CALC NEW chart and map data
        hour_slider_val: function() {

            this.set_ymdhm_from_date_and_hour();

            // ---- tell Map and Chart components
            let hour_args = { hour : this.y_m_d_h_m };

//console.log("emit: new_hour_slider:"+this.y_m_d_h_m.toISOString());

            this.$root.$emit('new_hour_slider', (hour_args) );
        },

        date_selected: function() {
            this.set_ymdhm_from_date_and_hour();
        }
    },

    // -----------------------------------------------
    methods: {

        opsday(val) {
            let sval = parseInt(val);

            // TODO: use this:let od = Math.floor(sval/64) + this.date_selected.getUTCDate();
            let oh = Math.floor((sval + 32)/ 4) % 24;
            let om = (sval % 4) * 15;

            // couldn't make font smaller; and "dy-" made it too big to fit
            // let dv = ('0' + parseInt(od)).slice(-2) + '-' +
            let dv = ('0' + parseInt(oh)).slice(-2) + ':' +
                     ('0' + parseInt(om)).slice(-2);

            return(dv)
        },

/*************************************************/

        set_ymdhm_from_date_and_hour() {

            let sval = parseInt(this.hour_slider_val);
            let od = Math.floor(sval/64) + this.date_selected.getUTCDate();
            let oh = Math.floor((sval + 32)/ 4) % 24;
            let om = (sval % 4) * 15;

            this.y_m_d_h_m = new Date(Date.UTC(
                              this.date_selected.getUTCFullYear(),  // PROB. with WRAP
                              this.date_selected.getUTCMonth(),
                              od, oh, om, 0));   //  be careful here!!!
        },

/*************************************************/
    GoEverything_feb20() {

        if ((this.source_selected == "at_ent") &&
            (this.ptype_selected !== "within") ) {

            this.$buefy.dialog.alert("Selection choices make no sense.");
            return;
        }

        let fetch_args = { sel_date  : this.date_selected,
                           arr_apt   : this.arr_selected,
                           path      : this.ptype_selected,
                           center    : this.center_selected,
                           source    : this.source_selected,
                           ol_dtime  : this.y_m_d_h_m,  // pass through to OL
                           pickle    : this.use_pickle   };
//console.log("fetch_data");
//console.log(fetch_args);

        if (this.use_pickle==false) {  // don't spin it if just reading local file
            this.go_button_loading = true;  // turn spin button on (==spin)
        }

        this.$root.$emit('fetch_data', (fetch_args) );
    },
    // ---------------------------------------

  },
  mounted () {

  // Model's fetch needs to tell when to turn off spin button
  this.$root.$on('go_button_loading', (gbl_val) => {
        this.go_button_loading = gbl_val;
    })

  }
}
</script>

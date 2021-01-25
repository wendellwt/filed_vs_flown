<template>

<nav class="panel">
  <p class="panel-heading">
    Retrieve Dataset
  </p>
  <div class="panel-block">
            <b-field label="Select dates">
          <b-datepicker
            placeholder="Click to select..."
             v-model="sel_date"
             :min-date="our_min_date"
             :max-date="our_max_date"
            >
            <!-- removed for now (too hard): range -->
          </b-datepicker>
        </b-field>
  </div>

        <!-- ========== departure ========= -->
        <div class="panel-block">
          <div class="columns">
            <div class="column is-three-quarters">
              <b-dropdown :triggers="['hover']" aria-role="list"
                    v-model="dep_selected" >
              <button class="button is-light is-small" slot="trigger">
                    <span>Departure</span>
                    <!-- TODO: find this icon -->
                    <b-icon icon="menu-down"></b-icon>
              </button>
              <b-dropdown-item  v-for="apt in airportlist"
                          v-bind:value="apt"
                          :key="apt">{{ apt }}</b-dropdown-item>
              </b-dropdown>
            </div>
            <div class="column">{{dep_selected}}</div>
          </div>
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

              <b-dropdown-item  v-for="ctr in centerlist"
                          v-bind:value="ctr"
                          :key="ctr">{{ ctr }}</b-dropdown-item>
              </b-dropdown>
            </div>
            <div class="column">{{center_selected}}</div>
          </div>
       </div>
        <!-- ========== begin window time ========= -->
        <div class="panel-block">
          <b-field label="Begin and end times">
              <b-timepicker
                rounded
                placeholder="Click to select..."
                icon="clock"
                editable
                :enable-seconds="enableSeconds"
                :hour-format="hourFormat"
                :incrementMinutes="minutesGranularity"
                :locale="locale">
              </b-timepicker>
              <b-timepicker
                rounded
                placeholder="Click to select..."
                icon="clock"
                editable
                :enable-seconds="enableSeconds"
                :hour-format="hourFormat"
                :incrementMinutes="minutesGranularity"
                :locale="locale">
              </b-timepicker>
          </b-field>
       </div>

        <!-- ========== brought over from AppUI ========= -->

        <div class="panel-block">

          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GoFvF()"
                    >get fvf</b-button>

          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GoSummary()"
                    >get summary</b-button>

          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GoEverything()"
                    >get all one day</b-button>
        </div>

        <!-- ========== go ========= -->
        <div class="panel-block">
          <b-button @click="clickMe" class="is-primary is-light is-small">Go</b-button>
       </div>
  <p class="panel-heading">
    Analyze Dataset
  </p>
        <!-- ========== max/min slider ========= -->
        <div class="panel-block">
          <b-field label="Max/Min selector">
              <b-slider size="is-medium" :min="0" :max="70"
                            type="is-info"
                            v-model="slider_vals"
                  >
              </b-slider>
        </div>
        <!-- ========== hour slider ========= -->
        <div class="panel-block">
          <b-field label="Hour selector">
              <b-slider size="is-medium" :min="0" :max="23"
                            type="is-info"
                            v-model="hour_val"
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
        enableSeconds : false,
        hourFormat : "24",
        locale : "en-US",
        minutesGranularity: 15,

        our_min_date: new Date("2019-01-01"),
        our_max_date: new Date("2021-05-31"),
        hourFormat_d: "24",
        incrementMinuts_d: 15,
        date_selected: new Date(),
        time_selected: new Date(),
        dep_selected: "any",
        arr_selected: "DEN",
        center_selected: "ZDV",
        // back when 'range' was included: dates: [],
        sel_date: new Date('January 10, 2020 09:00:00'),  // start???

        airportlist: [ "DEN", "DFW", "ATL", 'JFK', 'LAX', 'MIA' ],
        centerlist: [ "ZDV", "ZFW", "ZLA", 'ZKC', 'ZME' ],

        slider_vals : [0,70],
        hour_val : 8,

        details_data : [],
        chart_data   : [],
        map_data     : [],
        hourly_data  : []
   }
  },
    watch: {
        slider_vals: function(vals) {

            this.slider_vals  = vals ; // redundant???

            //console.log("slider is now:" + vals);

            if (this.hourly_data.length > 0 ) {
                let chart_args = { cdata: this.hourly_data, slider_vals : this.slider_vals };
                this.$root.$emit('draw_new_chart', (chart_args) );
            } else {
                console.log("nothing to chart");
            }
        },
        hour_val: function(hval) {

            this.hour_val  = hval ; // redundant???

            //console.log("hour is now:" + hval);

            this.set_and_show_hourly_data();
        }
    },
    methods: {
      // -----------------------------------------------
      clickMe() {
          this.$buefy.notification.open('Clicked!!')
      },
      // -----------------------------------------------
    GoFvF() {
        let force_reload = Math.floor(Math.random() * 99999);

        // apt is bogus
        let the_query = "get_fvf?apt=IAD&rand=" + force_reload;

        console.log("emit fvf url");
        console.log(the_query);
        this.$root.$emit('fvfurl', (the_query) );
    },
    // ---------------------------------------
    GoSummary() {

        let udate = "&date="+ this.sel_date.getUTCFullYear() + '_' +
                       String(this.sel_date.getUTCMonth()+1).padStart(2,'0')  + '_' +
                              this.sel_date.getUTCDate() ;

        //don't I wish: let udate = "&date=" + this.sel_date.strftime("%Y_%m_%d");

console.log("udate=" + udate);

        let force_reload = "&rand=" + Math.floor(Math.random() * 99999);

        let the_query = "get_summary?apt=DEN&ctr=ZDV" + udate + force_reload;

        console.log("fetch:" + the_query);
        //console.log(the_query);
        // this.$root.$emit('summaryurl', (the_query) );

       fetch(the_query)
        .then(response => response.json())
        .then(data => {

            //this.everything_data = data;
            console.log("HELP: this is not valid any more: this.everything_data");

            // first, send data over to Table page for tabular/text
            console.log("emit draw_new_table");
            this.$root.$emit('draw_new_table', (data) );
            // nope: this.$root.$emit('draw_new_table', (data, this.sel_date) );

            // second, send data over to Charts page for bar charts
            console.log("emit draw_new_chart");
            let chart_args = { cdata: this.hourly_data, slider_vals : this.slider_vals };
            this.$root.$emit('draw_new_chart', (chart_args) );
        });

    },
    // --------------------------------------------
    // ----------- everything processing  ---------
    // --------------------------------------------
    GoEverything() {

        // =========== query url ==============

        let udate =        this.sel_date.getUTCFullYear() + '_' +
                    String(this.sel_date.getUTCMonth()+1).padStart(2,'0')  + '_' +
                           this.sel_date.getUTCDate() ;

        //don't I wish: let udate = "&date=" + this.sel_date.strftime("%Y_%m_%d");

console.log("udate=" + udate);

        let force_reload = Math.floor(Math.random() * 99999);

        let the_query = "get_everything" +
                        "?apt="  + this.arr_selected +
                        "&ctr="  + this.center_selected +
                        "&date=" + udate +
                        "&rand=" + force_reload;

console.log("fetch:" + the_query);

       // =========== fetch / response ==============

       fetch(the_query)
        .then(response => response.json())
        .then(data => {

            this.map_data     = data.map_data;
            this.chart_data   = data.chart_data;
            this.details_data = data.details_data;

            // =========== OL FeatureCollection ==============

            this.$root.$emit('draw_all_fc', (this.map_data) );

            // =========== table details ==============

            this.$root.$emit('draw_new_details', (this.details_data) );

            // =========== chart details ==============

            this.set_and_show_hourly_data();

        });
    },
    // ---------------------------------------

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

        let use_this_hr = "2020_01_10_" +  String(this.hour_val).padStart(2,'0');
        console.log("hr=" + use_this_hr);

        this.hourly_data = [ ];
        for (let k = 0; k < this.chart_data.length; k++ ){
            if (this.chart_data[k].arr_hr == use_this_hr) {
                this.hourly_data.push( this.chart_data[k] );
            }
        }

        let chart_args = { cdata: this.hourly_data, slider_vals : this.slider_vals };
        this.$root.$emit('draw_new_chart', (chart_args) );
    }
  }
}
</script>

<template>

<nav class="panel">
  <p class="panel-heading">
    Commands
  </p>
  <div class="panel-block">
            <b-field label="Select dates">
          <b-datepicker
            placeholder="Click to select..."
             v-model="dates"
             :min-date="our_min_date"
             :max-date="our_max_date"
            range>
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
        </div>

        <!-- ========== go ========= -->
        <div class="panel-block">
          <b-button @click="clickMe" class="is-primary is-light is-small">Go</b-button>
       </div>
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
        dep_selected: "unk",
        arr_selected: "DEN",
        center_selected: "ZDV",
        dates: [],

        airportlist: [ "DEN", "DFW", "ATL", 'JFK', 'LAX', 'MIA' ],
        centerlist: [ "ZDV", "ZFW", "ZLA", 'ZKC', 'ZME' ],
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
        let force_reload = Math.floor(Math.random() * 99999);

        // apt is bogus
        let the_query = "get_summary?apt=DEN&ctr=ZDV&date=2020_01_10&rand=" + force_reload;

        console.log("emit summary url");
        console.log(the_query);
        this.$root.$emit('summaryurl', (the_query) );
    },
    // ---------------------------------------
  }

}
</script>

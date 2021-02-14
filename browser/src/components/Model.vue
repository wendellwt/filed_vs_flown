<template>
<div>
    <!-- this is the MODEL portion of the system -->
  </div>
</template>

<script>

// a file captured from ./everything.py over on rserver:
import e_feb from "./files/g_2020-03-02.json";    // set to empty file for flask

export default {
  name: 'model',
  prop: ['valid'],

  data () {
      return {

        y_m_d_val  : "2020_03_02",        // intermediate/temp value
        y_m_dt_val : "2020-03-02T18",     // portion of ISO time string to match
        y_m_da_val : "2020_03_02_05",     // arrival time is rounded to this
        y_m_dd_val : "2020-03-02 05:00",  // display on Chart component

        // NEW feb 13: send data to their owner components
        all_json_data: [],  // the (large) json received from server
   }
  },

    methods: {

      form_fetch_args(fa) {

        let udate =        fa.sel_date.getUTCFullYear() + '_' +
                    String(fa.sel_date.getUTCMonth()+1).padStart(2,'0')  + '_' +
                    String(fa.sel_date.getUTCDate()   ).padStart(2,'0');

        //don't I wish: let udate = "&date=" + this.sel_date.strftime("%Y_%m_%d");

        let force_reload = Math.floor(Math.random() * 99999);

        let the_query = "get_feb" +
                        "?apt="  + fa.arr_apt +
                        "&ctr="  + fa.center +
                        "&date=" + udate +
                        "&rand=" + force_reload;

        console.log("fetch:" + the_query);

        return(the_query);
    },

    // =========== fetch respose ==============

    process_fetch_response(new_data) {

        this.all_json_data= new_data;  // save everything there is

        // =========== OL FeatureCollection ==============

        // ---- tell Map component

        let map_args = { mdata: new_data.map_data.ZDV,  // FIXME <<<<<<<<
                         hour : this.y_m_dt_val };
        this.$root.$emit('new_model_data', (map_args) );

        // =========== chart details ==============

        //csv: this.set_and_show_hourly_data();

        // =========== table details ==============

        // this.$root.$emit('draw_new_details', (this.details_data) );

        // =========== caroline chart ==============

        // NOT TODAY: this.set_and_show_flown_and_entry();
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
  },
  mounted () {
    // -----------------------------------------------
    // ----------- fetch MODEL data ---------
    // --------------------------------------------

    this.$root.$on('fetch_data', (fetch_args) => {

        if (fetch_args.pickle==true) {
          console.log("using STORED json file.")
          // not for flask:
          this.process_fetch_response(e_feb);
          return; // <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        }
        let the_query = this.form_fetch_args(fetch_args)

        // =========== fetch / response ==============

        document.body.style.cursor='wait';
        this.go_button_loading = true;

         // don't know which gzip might work...
        // content-encoding may be just for POST when SENDING to server...

        // <<<<<<<<<<<<<<< when vscode on faa laptop:
        //the_query = "http://172.26.21.40:3939/content/201/" + the_query;

// Q: need to manually gzip on server???
// https://stackoverflow.com/questions/9622998/how-to-use-content-encoding-gzip-with-python-simplehttpserver

    fetch(the_query, {
        mode: 'no-cors',  // so faa laptop + vscode can fetch from rserver
      headers: {
        'Content-Type': 'text/plain',
             // "Access-Control-Allow-Origin": "*",
        //'Content-Type': 'application/json'//,
      //                            'Content-Encoding': 'gzip',
      //                            'Accept-Encoding' : 'gzip'
               }
      })
        .then(response => response.json())
        .then(data => {
            document.body.style.cursor='default';
            this.$root.$emit('go_button_loading', false);

            this.process_fetch_response(data);

        })
       .catch((error) => {
           document.body.style.cursor='default';
           this.$root.$emit('go_button_loading', false);
           alert('Error:', error);
           console.error('Error:', error);
       });
    })
  }
}
</script>

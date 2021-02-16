<template>
<div>
    <!-- this is the MODEL portion of the system -->
  </div>
</template>

<script>

// a file captured from ./everything.py over on rserver:
// TODO: for FLASK, when publishing, make this a very small valid json file!
import e_feb from "./files/j_2020-01-10.json";    // set to empty file for flask

export default {
  name: 'model',
  prop: ['valid'],

  data () {
      return {

        // NEW feb 13: send data to their owner components
        all_json_data  : [],  // the (large) json received from server
        y_m_d_h_m      : new Date(Date.UTC(2020,3,2,15,0,0)),
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

        let map_args = { mdata: new_data.map_data,
                         hour : this.y_m_d_h_m };
console.log("emit:"+this.y_m_d_h_m);
        this.$root.$emit('new_model_data', (map_args) );

        // =========== ef chart details ==============
        let chart_args = { ef_data     : new_data.chart_data,
                           title_date  : "put date/time here"   };
        this.$root.$emit('new_ef_data', (chart_args) );


        /*** OLD =========== chart details ==============
        let chart_args = { cdata: new_data.chart_data.ZDV,  // FIXME <<<<<<<<
                         title_date  : this.y_m_dd_val   };
        this.$root.$emit('new_barchart_data', (chart_args) );
      ***/
        
        //this.set_and_show_hourly_data();

        // =========== table details ==============

        this.$root.$emit('new_details_data', (new_data.details_data) ); // FIXME <<<<<

    },

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

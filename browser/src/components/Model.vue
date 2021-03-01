<template>
<div>
    <!-- this is the MODEL portion of the system -->
  </div>
</template>

<script>

// a file captured from ./everything.py over on rserver:
// CONSIDER: for FLASK, when publishing, make this a very small valid json file!
//import e_feb from "./files/n_2020-01-10.json";    // set to empty file for flask

/***************** vscode *
import g_at_ent_within from "./files/at_ent_within.json";
import g_depart_upto   from "./files/depart_upto.json";
import g_depart_within from "./files/depart_within.json";
import g_filed_upto    from "./files/filed_upto.json";
import g_filed_within  from "./files/filed_within.json";
import g_flown_upto    from "./files/flown_upto.json";
import g_flown_within  from "./files/flown_within.json";
import g_sched_upto    from "./files/sched_upto.json";
import g_sched_within  from "./files/sched_within.json";

//nope: import z_at_ent_within from "./files/zzz_at_ent_within.json";
import z_depart_within from "./files/zzz_depart_within.json";
import z_filed_within  from "./files/zzz_filed_within.json";
import z_flown_within  from "./files/zzz_flown_within.json";
import z_sched_within  from "./files/zzz_sched_within.json";
***************** vscode */


export default {
  name: 'model',
  prop: ['valid'],

  data () {
      return {

        // NEW feb 13: send data to their owner components
        all_json_data  : [],  // the (large) json received from server
        y_m_d_h_m      : new Date(Date.UTC(2020,8-1,8,23,30,0)),

        fetch_center  : "na",
        fetch_path    : "na",
        fetch_source  : "na",
        fetch_arr_apt : "na"
   }
  },

    methods: {

      form_fetch_args(fa) {

        this.fetch_center  = fa.center;
        this.fetch_path    = fa.path;
        this.fetch_source  = fa.source;
        this.fetch_arr_apt = fa.arr_apt;

        let udate =        fa.sel_date.getUTCFullYear() + '_' +
                    String(fa.sel_date.getUTCMonth()+1).padStart(2,'0')  + '_' +
                    String(fa.sel_date.getUTCDate()   ).padStart(2,'0');

        //don't I wish: let udate = "&date=" + this.sel_date.strftime("%Y_%m_%d");

        let force_reload = Math.floor(Math.random() * 99999);

        let the_query = "get_feb" +
                        "?date=" + udate +
                        "&ctr="  + fa.center +
                        "&pth="  + fa.path +
                        "&src="  + fa.source +
                        "&apt="  + fa.arr_apt +
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

//console.log("emit: new_model_data:"+this.y_m_d_h_m);

        this.$root.$emit('new_model_data', (map_args) );

        // =========== table details ==============

        this.$root.$emit('new_details_data', (new_data.details_data) );

        // =========== ef chart details ==============
        let chart_args = { cdata      : new_data.chart_data,
                           center     : this.fetch_center,
                           path       : this.fetch_path,
                           source     : this.fetch_source,
                           arr_apt    : this.fetch_arr_apt,
                           title_date : "put date/time here"   };

//console.log("emit: new_bar_data");
//console.log(chart_args.cdata);

        this.$root.$emit('new_bar_data', (chart_args) );
    },

  },
  mounted () {
    // -----------------------------------------------
    // ----------- fetch MODEL data ---------
    // --------------------------------------------

    this.$root.$on('fetch_data', (fetch_args) => {

        if (fetch_args.pickle==true) {

          console.log("using STORED json file.");

//console.log("path="+fetch_args.path);
let f = "helpme";
/*************** vscode *
if (fetch_args.path == "full") {
    //if (fetch_args.source == "at_ent") {f= g_at_ent_upto;}
    if (fetch_args.source == "depart") {f= z_depart_within;}
    if (fetch_args.source == "filed")  {f= z_filed_within;}
    if (fetch_args.source == "flown")  {f= z_flown_within;}
    if (fetch_args.source == "sched")  {f= z_sched_within;}
} else {

if (fetch_args.path == "within") {
    if (fetch_args.source == "at_ent") {f= g_at_ent_within;}
    if (fetch_args.source == "depart") {f= g_depart_within;}
    if (fetch_args.source == "filed")  {f= g_filed_within;}
    if (fetch_args.source == "flown")  {f= g_flown_within;}
    if (fetch_args.source == "sched")  {f= g_sched_within;}
    }

if (fetch_args.path == "upto") {
    //if (fetch_args.source == "at_ent") {f= g_at_ent_upto;}
    if (fetch_args.source == "depart") {f= g_depart_upto;}
    if (fetch_args.source == "filed")  {f= g_filed_upto;}
    if (fetch_args.source == "flown")  {f= g_flown_upto;}
    if (fetch_args.source == "sched")  {f= g_sched_upto;}
} }
******************* vscode */

//console.log("about to process");
//console.log(f)
          // Q: can the next line be enables for both?
          this.process_fetch_response(f);
          return; // <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        }
        let the_query = this.form_fetch_args(fetch_args)

        // =========== fetch / response ==============

        document.body.style.cursor='wait';
        this.go_button_loading = true;

         // don't know which gzip might work...
        // content-encoding may be just for POST when SENDING to server...

        // <<<<<<<<<<<<<<< when attempting on faa laptop:
        //the_query = "http://172.26.21.40:3939/content/201/" + the_query;

        // Q: need to manually gzip on server???
        // https://stackoverflow.com/questions/9622998/how-to-use-content-encoding-gzip-with-python-simplehttpserver

        fetch(the_query, {
          mode: 'no-cors',  // so faa laptop + ide can fetch from rserver
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

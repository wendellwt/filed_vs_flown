<template>
    <section>
      <nav class="level">

        <!-- ========== filename ========= -->
        <div class="level-item has-text-centered">
            <b-field label="">
                <b-input placeholder="asdex: enter filename here"
                         rounded
                         v-model="filename"
                         ></b-input>
            </b-field>
       </div>

       <!-- ========== geojson button ========= -->
        <div class="level-item has-text-centered">
          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GeoJson()"
                    >GeoJson</b-button>
       </div>

       <!-- ========== kml button ========= -->
        <div class="level-item has-text-centered">
          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GoKML()"
                    >GoKML</b-button>
       </div>

       <!-- ========== asdex button ========= -->
        <div class="level-item has-text-centered">
          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GoASDEX()"
                    >get ASDEX</b-button>
       </div>

       <!-- ========== nav end ========= -->
    </nav>
  </section>
</template>

<script>

// style guide??: https://www.rafaelescala.com/buefy-example/#buefy

export default {
  name: 'app',
  prop: ['valid'],

  data () {
      return {
        //filename: "asdex:enter filename here",
        filename: "/home/data/wturner/caroline/DAL1024.gjsn",
   }
  },
  methods: {
    // ---------------------------------------
    GeoJson() {
        let the_query = "get_geojson?fn=" + this.filename;

        console.log("emit geojsonurl");
        console.log(the_query);
        this.$root.$emit('geojsonurl', (the_query) );
    },
    // ---------------------------------------
    GoKML() {
        let the_query = "get_kml?fn=" + this.filename;

        console.log("emit kmlurl");
        console.log(the_query);
        this.$root.$emit('kmlurl', (the_query) );
    },
    // ---------------------------------------
    GoASDEX() {
        let force_reload = Math.floor(Math.random() * 99999);

        // apt is bogus
        let the_query = "get_asdex?apt=IAD&rand=" + force_reload;

        console.log("emit asdexurl");
        console.log(the_query);
        this.$root.$emit('asdexurl', (the_query) );
    },
    // ---------------------------------------
  }
}

</script>


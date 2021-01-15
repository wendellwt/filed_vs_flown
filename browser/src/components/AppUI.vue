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

       <!-- ========== paths button ========= -->
        <div class="level-item has-text-centered">
          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GoPaths()"
                    >get paths</b-button>
       </div>

       <!-- ========== paths button ========= -->
        <div class="level-item has-text-centered">
          <b-button type="is-success"
                    size="is-small"
                    rounded
                    v-on:click="GoFvF()"
                    >get fvf</b-button>
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
    GoPaths() {
        let force_reload = Math.floor(Math.random() * 99999);

        // apt is bogus
        let the_query = "get_paths?apt=IAD&rand=" + force_reload;

        console.log("emit paths url");
        console.log(the_query);
        this.$root.$emit('pathsurl', (the_query) );
    },
    // ---------------------------------------
    GoFvF() {
        let force_reload = Math.floor(Math.random() * 99999);

        // apt is bogus
        let the_query = "get_fvf?apt=IAD&rand=" + force_reload;

        console.log("emit fvf url");
        console.log(the_query);
        this.$root.$emit('fvfurl', (the_query) );
    },
    // ---------------------------------------
    // ---------------------------------------
  }
}

</script>


<template>
    <div>
       <h1>Summary Table</h1>

         <table class="table table-bordered">
            <thead>
              <tr>
                <th>corner</th>
                <th>time</th>
                <th>sched</th>
                <th>flown</th>
              </tr>
            </thead>
            <tbody>
                <tr v-for="(item, idx) in summaryData" :key=idx>
                    <td>{{ item.corner }}</td>
                    <td>{{ item.hour }}</td>
                    <td>{{ item.sched_dist_zdv }}</td>
                    <td>{{ item.flown_dist_zdv }}</td>
                </tr>
            </tbody>

          </table>

  </div>
</template>

<script>

// $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

export default {
    data () {
      return {
        summaryData: 'bogus'
      }
    },

// ==========================================================

    methods: {
    },

// ==========================================================

  mounted () {

    this.$root.$on('summaryurl', (the_query) => {
      console.log("summary::"+the_query);

/* %%%%%%%%%%%%%%%%%%%%%%% WORKS:
let HELPME = [
  {"corner":"ne","sched_dist_zdv":52854,"flown_dist_zdv":52913},
  {"corner":"nw","sched_dist_zdv":26231,"flown_dist_zdv":26401},
  {"corner":"se","sched_dist_zdv":38674,"flown_dist_zdv":38408},
  {"corner":"sw","sched_dist_zdv":56440,"flown_dist_zdv":56410}
];
            console.log("emit v3");
            console.log(HELPME);  // does this change???

            this.$root.$emit('update', (HELPME) );
%%%%%%%%%%%%%%%%%%%%%%% */

      fetch(the_query)
        .then(response => response.json())
        .then(data => {

            // first, set our own variable to display (locally) table
            this.summaryData = data

            // second, send data over to Gallery page for bar charts
            console.log("emit update");
            console.log(data);

            this.$root.$emit('update', (data) );
        });

    })
  } // ---- mounted
}

</script>

<style lang="scss">
</style>


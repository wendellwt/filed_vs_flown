<template>
    <div>
        <h1>Summary Table {{the_date}}</h1>

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
        summaryData: 'bogus',
        the_date: new Date()
      }
    },

// ==========================================================

    methods: {
    },

// ==========================================================

  mounted () {

    this.$root.$on('draw_new_table', (the_data) => {
      console.log("draw_new_table::"+the_data);

      //this.the_date = the_date;

      // first, set our own variable to display (locally) table
      this.summaryData = the_data;

    }),

    this.$root.$on('summaryurl_OLD_UNUSED', (the_query) => {
      console.log("summary::"+the_query);

      fetch(the_query)
        .then(response => response.json())
        .then(data => {

            // first, set our own variable to display (locally) table
            this.summaryData = data

            // second, send data over to Gallery page for bar charts
            console.log("emit update");
            console.log(data);

            this.$root.$emit('draw_new_chart', (data) );
        });

    })
  } // ---- mounted
}

</script>

<style lang="scss">
</style>


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
      fetch(the_query)
        .then(response => response.json())
        .then(data => (this.summaryData = data));
    })
  } // ---- mounted
}

</script>

<style lang="scss">
</style>


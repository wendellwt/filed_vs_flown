<template>
    <div>
        <h1>Details Table {{the_date}}</h1>

         <table class="table table-bordered">
            <thead>
              <tr>
                <th>acid</th>
                <th>corner</th>
                <th>arrive time</th>
                <th>flight index</th>
                <th>at depart dist</th>
                <th>at entry dist</th>
                <th>flown dist</th>
              </tr>
            </thead>
            <tbody>
                <tr v-for="(item, idx) in detailData" :key=idx>
                    <td              >{{ item.acid         }}</td>
                    <td              >{{ item.corner       }}</td>
                    <td              >{{ item.arr_time     }}</td>
                    <td align="right">{{ item.fid          }}</td>
                    <td align="right">{{ parseFloat(item.b4_dep_dist).toFixed(1)  }}</td>
                    <td align="right">{{ parseFloat(item.b4_ent_dist).toFixed(1)  }}</td>
                    <td align="right">{{ parseFloat(item.flw_dist   ).toFixed(1)  }}</td>
                </tr>
            </tbody>

          </table>

  </div>
</template>

<script>

// =========================================================

export default {
    data () {
      return {
        detailData: 'bogus',
        the_date: new Date()
      }
    },

// ==========================================================

    methods: {
    },

// ==========================================================

  mounted () {

    this.$root.$on('draw_new_details', (the_data) => {

      // first, set our own variable to display (locally) table
      this.detailData = the_data;

    })
  }
}

</script>

<style lang="scss">
</style>


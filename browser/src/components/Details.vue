<template>
    <div>
        <h1>Details Table {{the_date}}</h1>

         <table class="table table-bordered">
            <thead>
              <tr>
                <th>acid</th>
                <th>corner</th>
                <th>arrive time</th>
                <th>fid</th>
                <th>at depart dist</th>
                <th>at entry dist</th>
                <th>flown dist</th>
              </tr>
            </thead>
            <tbody>
                <tr v-for="(item, idx) in detailData" :key=idx>
                    <td              >{{ item[ 0] }}</td>
                    <td              >{{ item[ 2] }}</td>
                    <td              >{{ item[10] }}</td>
                    <td align="right">{{ item[ 1] }}</td>
                    <td align="right">{{ parseFloat(item[8]).toFixed(1) }}</td>
                    <td align="right">{{ parseFloat(item[7]).toFixed(1) }}</td>
                    <td align="right">{{ parseFloat(item[6]).toFixed(1) }}</td>
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
        detailColumns: 'bogus',
        detailData: 'bogus',
        the_date: new Date()
      }
    },

// ==========================================================

    methods: {
    },

// ==========================================================

// >>> details_df.to_json(orient='split', default_handler=str, index=False)
// '{
// "columns":["acid","fid","corner","artcc","dep_apt","arr_apt","flw_dist","b4_ent_dist","b4_dep_dist","dep_time","arr_time"],
//             0      1     2        3       4         5         6          7             8             9          10
// "data":[
// ["SWA960",20200110475554,"se","ZDV","DAL","DEN",131.9,135.8,136.6,"2020-01-10 21:52:00+00:00","2020-01-10 23:23:00+00:00"],
// ["SWA1446",20200110478578,"nw","ZDV","SLC","DEN",172.7,172.1,172.1,"2020-01-10 19:00:00+00:00","2020-01-10 20:10:00+00:00"],
// ["LOF4635",20200110495135,"sw","ZDV","MTJ","DEN",136.6,140.1,137.2,"2020-01-10 19:15:00+00:00","2020-01-10 20:05:00+00:00"],

  mounted () {

    this.$root.$on('draw_new_details', (the_data) => {

      this.detailColumns = the_data['columns'];
      this.detailData = the_data['data'];

    })
  }
}

</script>

<style lang="scss">
</style>


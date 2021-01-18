<template>

  <div class="columns">
    <div class="column">
      <app-ui></app-ui>
      <app-ol></app-ol>
      <charts></charts>
    </div>
    <div class="column is-one-quarter">
      <data-pos></data-pos>
    </div>
  </div>
</template>

<script>

import AppUI   from "./components/AppUI.vue";
import AppOL   from "./components/AppOL.vue";
import DataPos from "./components/DataPos.vue";
import Charts  from "./components/Charts.vue";

export default {
  name: 'app',
  components: {
    'app-ui'   : AppUI,
    'app-ol'   : AppOL,
    'data-pos' : DataPos,
    'charts'   : Charts
  },

  data () {
    return {
        location  : null,
   }
  }
}

</script>

<style lang="scss">
</style>




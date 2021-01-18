<template>
    <section>
        <b-tabs position="is-centered" class="block">
            <b-tab-item label="Map">

  <div class="columns">
    <div class="column">
      <app-ol></app-ol>
    </div>
    <div class="column is-one-quarter">
      <data-pos></data-pos>
    </div>
  </div>

            </b-tab-item>
            <b-tab-item label="Charts"><charts /></b-tab-item>
        </b-tabs>
    </section>
</template>

<script>
import AppOL from './AppOL.vue';
import DataPos from "./DataPos.vue";
import Charts  from "./Charts.vue";

export default {
  name: 'Tabs',
    components: {
      'app-ol'   : AppOL,
      'data-pos' : DataPos,
      'charts'   : Charts
  },
  props: {
    msg: String
  }
}
</script>

<style lang="scss">
</style>


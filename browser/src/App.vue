<template>
  <div id="app">
    <div class="columns">
      <div class="column is-one-fifth">

        <Panel />

      </div>
      <div class="column">

        <Tabs />

      </div>
    </div>
  </div>
</template>

<script>

import Panel from './components/Panel.vue';
import Tabs from './components/Tabs.vue';

export default {
  name: 'App',
  components: {
    Panel,
    Tabs
  }
}

</script>

<style lang="scss">
</style>




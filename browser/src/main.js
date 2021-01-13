
import Vue from 'vue'
import App from './App.vue'

// ---------------- openayers

import VueLayers from 'vuelayers'
import 'vuelayers/lib/style.css' // needs css-loader

Vue.use(VueLayers);

// +++++++++++++ buefy
import Buefy from 'buefy'
import 'buefy/dist/buefy.css'
Vue.use(Buefy)

// ---------------- materialdesign icons

import 'vue-material-design-icons/styles.css';

// ---------------- main

new Vue({
  render: h => h(App),
}).$mount("#app")


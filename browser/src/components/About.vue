<template>
    <div>
      <markdown-it-vue class="md-body" :content="content" />
    </div>
</template>

<script>

// nope: //   $ npm install vue-markdown
// nope: Vue.use(VueMarkdown);
// nope: var VueMarkdown = require('vue-markdown');

// NOTE: This is the only one I could get working:
import MarkdownItVue from 'markdown-it-vue'
import 'markdown-it-vue/dist/markdown-it-vue.css'

export default {
  name: 'About',
    components: {
    //'vue-markdown': VueMarkdown
        MarkdownItVue
  },
  props: {
  },
    data() {

// https://github.com/ravenq/markdown-it-vue/blob/master/example/components/example.js
      return {
content: `
# about Filed vs Flown

This is a very nice application.

Note: I haven't updated this description page in a couple of weeks.
It may or may not be accurately reflect the latest updates.

## Left selector panel

This section contains the selectors and buttons used to construct an
SQL query to the PostGIS database of flights.

Date
  ~ select the date.  Currently this is the name of
the PostGIS table (sched_fvf_yyyy_mm_dd) which was derived
from the name of the Oracle table (ROUTE_yyyymmdd).
I think this is the day of departure.
Currently tables for all of 2020 have been populated.

Arrival
  ~ select the arrival airport.
Currently tables for DEN and DFW have been populated.

Center
  ~ select the ARTCC center that will be used for cropping of the
scheduled and flown flight paths.

GET DATA
  ~ Request data from rserver (query PostGIS using selected parameters)

debug
  ~ don't execute a query, just return canned 2020-01-10 data (fast)

### Analyze Dataset

Hour of map
  ~ For the Map and some of the Charts, select the (one) hour of the day to display.

min/max chart y-axis
  ~ adjust the Y-axis of some of the charts
(at least for the charts where I rememberd to enable this feature.)

## Tabs

### Map

Chart (upper) panel
  ~ the main bar chart showing sum of flown path distances by corner post

Map (lower) panel
  ~ a map disply showing the selected ARTCC and the flight paths within it.

Data Position (right) Panel.
  ~ a list of text about the flight paths showing in the map.
Data elements include: acid, corner post, departure airport, flight index, ac type,
length (distance) of the scheduled path at ARTCC entry,
length (distance) of the flown path,
and difference of flown distance and schedule distance.

Note: if you click on a Data Position block, the associated tracks
will be highlighted (flown in red, at_entry schedule in dark red).


### Charts

an experimental chart I was working on the other day

### Stacked

another experimental chart I was working on the other day

### Details

It was supposed to be the complete text list of flights for that day,
I don't know if I've kept it up-to-date as the other charts
have been updated.

`
      };
    },
}
</script>

<style lang="scss" scoped>
</style>


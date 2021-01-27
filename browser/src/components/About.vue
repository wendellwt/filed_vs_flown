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
[toc]

## Page Layout

### Retrieve Dataset

Explain Date, Arrival, Center

### Analyze Dataset

Explain Hour of map, min/max chart y-axis

## Tabs

Explain Map, Charts, Stacked, Details, About

`
      };
    },
}
</script>

<style lang="scss" scoped>
</style>



const path = require("path");

module.exports = {

    // Note: the number here is the one assigned by the 1st 'rconnect deploy'
    publicPath: "/fvf/",

    // custom: asdex/service is the "official" server dir
    outputDir: "../../asdex/service/fvf_code/",

    "transpileDependencies": [
        "buefy"
      ]
}


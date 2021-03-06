/**
 * Created by rich on 10/9/2016.
 */
var loadModule = "app/main"
// Configuration Object for Dojo Loader:
dojoConfig = {
    baseUrl: "src/", // Where we will put our packages
    selectorEngine: "lite",
    async: 1, // We want to make sure we are using the "modern" loader
    hasCache: {
        "host-node": 1, // Ensure we "force" the loader into Node.js mode
        "dom": 0 // Ensure that none of the code assumes we have a DOM
    },
    // While it is possible to use config-tlmSiblingOfDojo to tell the
    // loader that your packages share the same root path as the loader,
    // this really isn't always a good idea and it is better to be
    // explicit about our package map.
    packages: [{
        name: "dojo",
        location: "dojo"
    },{
        name: "app",
        location: "app"
    }],
    deps: [ loadModule ]
};

// Now load the Dojo loader
require("./src/dojo/dojo.js");

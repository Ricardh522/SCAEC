/**
 * Created by rich on 10/9/2016.
 */
require([
    "dojo/node!util",
    "dojo/node!fs",
    "dojo/request/node",
    "dojo/Deferred"



    ], function(
        util,
        fs,
        nodeRequest,
        Deferred
    ){


    // function readFilePromise(filename) {
    //     var dfd = new Deferred();
    //     fs.readFile(filename, function(err, data) {
    //         if(err) dfd.reject(err);
    //         dfd.resolve(data);
    //     });
    //     return dfd.promise;
    // }

    function getScrap(faa_id) {
       var  payload = {'Site': faa_id, 'AptSecNum': '0'}
        nodeRequest("http://www.gcr1.com/5010web/airport.cfm", {
            data: payload,
            method: "POST",
            handleAs: "text"
        }).then(function(out) {
            console.log(out);
        });
    }

    getScrap("AIK").then(function(content) {
        console.log(content);
    }, function(err) {
        console.log(err);
    });

});
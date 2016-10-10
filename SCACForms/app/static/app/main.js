/**
 * Created by rich on 10/9/2016.
 */
require(["dojo/dom", "dojo/promise/all", "dojo/dom-prop", "dojo/Deferred", "dojo/_base/array", "dojo/parser", "dojo/dojo", "dojo/html", "dojo/query", "dojo/NodeList-dom", "dojo/domReady!"],
    function(dom, all, domProp, Deferred, Array, parser, dojo, html, query) {
        parser.parse();
        var mainDeferred = new Deferred();
        var json_output = [];
        var node = dom.byId("main");
        var text = node.innerText;
        html.set(node, text);
        var nl = query("table", node);
        var airports = Array.map(nl, function(airport) {
            var deferred = new Deferred();
            var faa_id = domProp.get(airport, "class");
            faa_id = faa_id.split("_")[0];
            var curform = {
                "faa_id": faa_id,
                "fields": []
            };


            var trs = query(".DataLabel", airport);
            var i = 1;
            var labels = Array.map(trs, function(data_label) {
                var deferred2 = new Deferred();
                (function() {
                    var title;
                    var data;
                    var children = data_label.childNodes;
                    var multi_line = {
                        "id": i,
                        "title": "",
                        "data": []
                    };
                    i += 1;
                    if (children.length == 1) {
                        if (children[0].hasOwnProperty('data')) {
                            try {
                                multi_line.title = children[0].data;
                            } catch(err) {
                                console.log(err);
                            }
                        }
                        if (children[0].hasOwnProperty('innerHTML')) {
                            try {
                                multi_line.data = children[0].innerHTML;
                            } catch(err) {
                                console.log(err);
                            }
                        }
                    } else if (children.length > 1) {
                        if (children[0].hasOwnProperty('data')) {
                            try {
                                title = children[0].data;
                            } catch (err) {
                                console.log(err);
                            }
                        }

                        if (children[1].hasOwnProperty('innerHTML')) {
                            try {
                                data = children[1].innerHTML;
                            } catch (err) {
                                console.log(err);
                            }
                        }
                    }


                    return deferred2.resolve({"title": title, "data": data});
                })();
                return deferred2.promise;
            });
            all(labels).then(function(e) {
                var res = Array.map(e, function(x) {
                    var deferred3 = new Deferred();
                    (function() {
                        var d = false;
                        if (x.title != "") {
                            d = true;
                        } else {
                            d = false;
                        }
                        if (x.data != []) {
                            d = true;
                        } else {
                            d = false;
                        }

                        if(d === true) {
                            curform.fields.push(x)
                            deferred3.resolve(x);
                        } else {
                            deferred3.resolve("no data in cells");
                        }

                    })();
                    return deferred3.promise;
                });
                all(res).then(function(e) {
                    if (e.length) {
                        json_output.push(curform);
                        deferred.resolve(e);
                    } else {
                        deferred.resolve('empty array');
                    }
                });
            });

            return deferred.promise;
        });

        all(airports).then(function(arr) {
            html.set(node, json_output, {
                "cleanContent": true,
                "parseContent": true,
            });
            mainDeferred.resolve(json_output);
        });
        return mainDeferred.promise;
});
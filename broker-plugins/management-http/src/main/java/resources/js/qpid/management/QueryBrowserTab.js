/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 */
define(["dojo/parser",
        "dojo/query",
        "dojo/text!showQueryBrowserTab.html",
        "qpid/management/preference/PreferenceBrowserWidget",
        "qpid/common/updater",
        "dojo/domReady!"],
    function (parser, query, template, PreferenceBrowserWidget, updater)
    {
        function QueryBrowserTab(kwArgs)
        {
            this.controller = kwArgs.controller;
            this.management = this.controller.management;
        }

        QueryBrowserTab.prototype.getTitle = function (changed)
        {
            return "Query Browser";
        };

        QueryBrowserTab.prototype.open = function (contentPane)
        {
            var that = this;
            this.contentPane = contentPane;
            contentPane.containerNode.innerHTML = template;
            parser.parse(contentPane.containerNode)
                .then(function (instances)
                {
                    that.onOpen(contentPane.containerNode)
                }, function (e)
                {
                    console.error("Unexpected error on parsing query tab template", e);
                });
        };

        QueryBrowserTab.prototype.onOpen = function (containerNode)
        {
            var that = this;
            var queryBrowserWidgetNode = query(".queryBrowserWidgetNode", containerNode)[0];
            this.queryBrowserWidget = new PreferenceBrowserWidget({
                management: this.management,
                structure: this.controller.structure,
                preferenceType: "query",
                preferenceTypeFriendlyPlural: "queries",
                preferenceTypeFriendlySingular: "Query"
            }, queryBrowserWidgetNode);
            this.queryBrowserWidget.on("open",
                function (event)
                {
                    var tabData = {
                        tabType: "query",
                        data: event.preference,
                        modelObject: event.parentObject,
                        preferenceId: event.preference.id
                    };
                    that.controller.showTab(tabData);
                });
            this.queryBrowserWidget.startup();

            this.contentPane.on("show",
                function ()
                {
                    that.queryBrowserWidget.resize();
                });
            updater.add(this);
        };

        QueryBrowserTab.prototype.close = function ()
        {
            updater.remove(this);
            if (this.queryBrowserWidget)
            {
                this.queryBrowserWidget.destroyRecursive();
                this.queryBrowserWidget = null;
            }
        };

        QueryBrowserTab.prototype.destroy = function ()
        {
            this.close();
            this.contentPane.onClose();
            this.controller.tabContainer.removeChild(this.contentPane);
            this.contentPane.destroyRecursive();
        };

        QueryBrowserTab.prototype.update = function()
        {
            if (this.contentPane.selected)
            {
                this.queryBrowserWidget.update();
            }
        };

        return QueryBrowserTab;
    });

(function (a) {
    a.fn.formset = function (b) {
        var c = a.extend({}, a.fn.formset.defaults, b);
        var d = function (b, c, d) {
                var e = new RegExp("(" + c + "-\\d+)");
                var f = c + "-" + d;
                if (a(b).attr("for")) a(b).attr("for", a(b).attr("for").replace(e, f));
                if (b.id) b.id = b.id.replace(e, f);
                if (b.name) b.name = b.name.replace(e, f)
            };
        a(this).each(function (b) {
            a(this).addClass(c.formCssClass);
            if (c.addDeleteButton) {
                if (a(this).is("TR")) {
                    a(this).children(":last").append('<a class="' + c.deleteCssClass + '" href="javascript:void(0)">' + c.deleteText + "</a>")
                } else if (a(this).is("UL") || a(this).is("OL")) {
                    a(this).append('<li><a class="' + c.deleteCssClass + '" href="javascript:void(0)">' + c.deleteText + "</a></li>")
                } else {
                    a(this).append('<a class="' + c.deleteCssClass + '" href="javascript:void(0)">' + c.deleteText + "</a>")
                }
            }
            a(this).find("a." + c.deleteCssClass).click(function () {
                var b = a(this).parents("." + c.formCssClass);
                b.remove();
                if (c.removed) c.removed(b);
                var e = a("." + c.formCssClass);
                a("#id_" + c.prefix + "-TOTAL_FORMS").val(e.length);
                if (e.length == 1) {
                    a("a." + c.deleteCssClass).hide()
                }
                for (var f = 0, g = e.length; f < g; f++) {
                    a(e.get(f)).find("input,select,textarea,label").each(function () {
                        d(this, c.prefix, f)
                    })
                }
                return false
            })
        });
        if (a(this).length) {
            if (c.addBtnObj) {
                $addBtn = c.addBtnObj
            } else {
                if (a(this).attr("tagName") == "TR") {
                    var e = this.eq(0).children().length;
                    a(this).parent().append('<tr><td colspan="' + e + '"><a class="' + c.addCssClass + '" href="javascript:void(0)">' + c.addText + "</a></tr>");
                    $addBtn = a(this).parent().find("tr:last a")
                } else {
                    a(this).filter(":last").after('<a class="' + c.addCssClass + '" href="javascript:void(0)">' + c.addText + "</a>");
                    $addBtn = a(this).filter(":last").next()
                }
            }
            $addBtn.click(function () {
                var b = parseInt(a("#id_" + c.prefix + "-TOTAL_FORMS").val());
                var e = a("." + c.formCssClass + ":first").clone(true).get(0);
                a(e).removeAttr("id").insertAfter(a("." + c.formCssClass + ":last"));
                a(e).find("input,select,textarea,label").each(function () {
                    d(this, c.prefix, b);
                    var e = a(this);
                    if (e.is("input:checkbox") || e.is("input:radio")) {
                        e.attr("checked", false)
                    } else {
                        e.val("")
                    }
                });
                var f = b + 1;
                a("#id_" + c.prefix + "-TOTAL_FORMS").val(f);
                if (f > 1) {
                    a("a." + c.deleteCssClass).show()
                }
                if (c.added) c.added(a(e));
                return false
            })
        }
        if (a(this).length == 1) {
            a("a." + c.deleteCssClass).hide()
        }
        return a(this)
    };
    a.fn.formset.defaults = {
        prefix: "form",
        addText: "add another",
        deleteText: "remove",
        addCssClass: "add-row",
        deleteCssClass: "delete-row",
        formCssClass: "dynamic-form",
        added: null,
        removed: null,
        addBtnObj: null,
        addDeleteButton: true
    }
})(jQuery)

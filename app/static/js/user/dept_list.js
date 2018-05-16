$(document).ready(function() {

        // 获取sessionStorage中搜索表单对应的几个类型值，如果存在就将其填充到表单的value中
        var deptlist_keyword = sessionStorage.getItem('deptlist_keyword');
        var deptlist_current_page = sessionStorage.getItem('deptlist_current_page');
        var dept_data_length = sessionStorage.getItem('dept_data_length');

        var data =  {
                "page":1,
                "deptlist_keyword":'',
                "dept_data_length":10
            };

        if ( deptlist_keyword ) {
            $('#deptlist_keyword').val(deptlist_keyword);
            data["deptlist_keyword"] = deptlist_keyword;
        }
        if ( deptlist_current_page ) {
            data["page"] = deptlist_current_page;
        }
        if ( dept_data_length ) {
            $('select#dept_table_length').val(dept_data_length);
            data["dept_data_length"] = dept_data_length;
        }

        // 点击提交表单，重新设置sessionStorage的值，并且重新初始化ajax的data数据
        $('#search_btn').click(function () {
            var deptlist_keyword = $('input#deptlist_keyword').val();
            var dept_data_length = $('select#dept_table_length').val();

            data = {
                "page":1,
                "deptlist_keyword":deptlist_keyword,
                "dept_data_length":dept_data_length
            };
            if ( deptlist_keyword ) {
                sessionStorage.setItem('deptlist_keyword',deptlist_keyword );
            }
            else {
                sessionStorage.removeItem('deptlist_keyword');
            }
            sessionStorage.setItem('deptlist_current_page',1 );
            sessionStorage.setItem('dept_data_length',dept_data_length );

            $.ajax({
                url:'/users/dept_list_ajax',
                type:'POST',
                data:JSON.stringify(data),
                contentType: 'application/json; charset=UTF-8',
                dataType:'JSON',
                success:function (callback) {
                    if (callback.page_content) {
                        $('div#deptlist_notfound').html('');
                        var page_count=callback.page_count;
                        var page_content=callback.page_content;
                        var per_page = callback.per_page;
                        $('tbody#deptlist_dynamic')
                            .empty()
                            .append(page_content);
                        var notes = "第1页/共 " + Math.ceil(page_count/per_page) + "页, 每页" + per_page + "条/共" + page_count + " 条";
                        $('div#deptlist_notes').text(notes);
                    } else {
                        $('tbody#deptlist_dynamic').empty();
                        $('div#deptlist_notfound').html('未发现任何相关记录');
                        $('div#deptlist_notes').text('');
                    }
                    monitor(Math.ceil(page_count/per_page),data['page'],data);
                }
            });
        });

        // 无任何搜索条件，默认进入主机列表页面时提交的ajax
        $.ajax({
                url:'/users/dept_list_ajax',
                type:'POST',
                data:JSON.stringify(data),
                contentType: 'application/json; charset=UTF-8',
                dataType:'JSON',
                success:function (callback) {
                    if (callback.page_content) {
                        $('div#deptlist_notfound').html('');
                        var page_count=callback.page_count;
                        var page_content=callback.page_content;
                        var per_page = callback.per_page;
                        $('tbody#deptlist_dynamic').append(page_content);
                        var notes = "第1页/共 " + Math.ceil(page_count/per_page) + "页, 每页" + per_page + "条/共" + page_count + " 条";
                        $('div#deptlist_notes').text(notes);
                    } else {
                        $('tbody#deptlist_dynamic').empty();
                        $('div#deptlist_notfound').html('未发现任何相关记录');
                    }
                    monitor(Math.ceil(page_count/per_page),data['page'],data);
                }

        });

    // 实现分页功能的函数
    function monitor(totalpages,current_page,data) {
        $('#deptlist_pageLimit').bootstrapPaginator({
            currentPage: current_page,
            totalPages:totalpages,
            size:"normal",
            bootstrapMajorVersion: 3,
            alignment:"right",
            numberOfPages:8,
            itemTexts: function (type, page, current) {
                switch (type) {
                case "first": return "首页";
                case "prev": return "上一页";
                case "next": return "下一页";
                case "last": return "末页";
                case "page": return page;
                }       // 默认显示的是第一页。
            },
                onPageClicked: function (event, originalEvent, type, page){     //给每个页眉绑定一个事件，其实就是ajax请求，其中page变量为当前点击的页上的数字。
                    sessionStorage.setItem('deptlist_current_page',page );
                    data["page"] = page;
                    $.ajax({
                        url:'/users/dept_list_ajax',
                        type:'POST',
                        data:JSON.stringify(data),
                        contentType: 'application/json; charset=UTF-8',
                        dataType:'JSON',
                        success:function (callback) {
                            $('div#deptlist_notfound').html('');
                            var page_count=callback.page_count;
                            var page_content=callback.page_content;
                            var per_page = callback.per_page;
                            $('tbody#deptlist_dynamic')
                                .empty()
                                .append(page_content);
                            var notes = "第" + page + "页/共 " + Math.ceil(page_count/per_page) + "页, 每页" + per_page + "条/共" + page_count + " 条";
                            $('div#deptlist_notes').text(notes);
                        }
                    })
                }
        });
    }
    

});
/**
 * Created by qiankun on 2018/3/20.
 * Last edited by qiankun on 2018/3/20.
 */

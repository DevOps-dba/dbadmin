$(document).ready(function() {

        // 获取sessionStorage中搜索表单对应的几个类型值，如果存在就将其填充到表单的value中
        var mysqldb_name = sessionStorage.getItem('mysqldb_name');
        var mysqldb_ipaddress = sessionStorage.getItem('mysqldb_ipaddress');
        var mysqldb_status = sessionStorage.getItem('mysqldb_status');
        var mysqldb_current_page = sessionStorage.getItem('mysqldb_current_page');
        var mysqldb_data_length = sessionStorage.getItem('mysqldb_data_length');

        var data =  {
            "page":1,
            "mysqldb_name":'',
            "mysqldb_ipaddress":'',
            "mysqldb_status":'',
            "mysqldb_data_length":10
        };

        if ( mysqldb_name ) {
            $('#mysqldb_name').val(mysqldb_name);
            data["mysqldb_name"] = mysqldb_name;
        }
        if ( mysqldb_ipaddress ) {
            $('#mysqldb_ipaddress').val(mysqldb_ipaddress);
            data["mysqldb_ipaddress"] = mysqldb_ipaddress;
        }
        if ( mysqldb_status ) {
            $('#mysqldb_status').val(mysqldb_status);
            data["mysqldb_status"] = mysqldb_status;
        }
        if ( mysqldb_current_page ) {
            data["page"] = mysqldb_current_page;
        }
        if ( mysqldb_data_length ) {
            $('select#mysqldb_data_length').val(mysqldb_data_length);
            data["mysqldb_data_length"] = mysqldb_data_length;
        }

        // 点击提交表单，重新设置sessionStorage的值，并且重新初始化ajax的data数据
        $('#search_btn').click(function () {
            var mysqldb_name = $('input#mysqldb_name').val();
            var mysqldb_data_length = $('select#mysqldb_data_length').val();
            var mysqldb_ipaddress = $('input#mysqldb_ipaddress').val();
            var mysqldb_status = $('select#mysqldb_status').val();

            data = {
                "page":1,
                "mysqldb_name":mysqldb_name,
                "mysqldb_ipaddress":mysqldb_ipaddress,
                "mysqldb_status":mysqldb_status,
                "mysqldb_data_length":mysqldb_data_length
            };
            if ( mysqldb_name ) {
                sessionStorage.setItem('mysqldb_name',mysqldb_name );
            }
            else {
                sessionStorage.removeItem('mysqldb_name');
            }
            if ( mysqldb_ipaddress ) {
                sessionStorage.setItem('mysqldb_ipaddress',mysqldb_ipaddress );
            }
            else {
                sessionStorage.removeItem('mysqldb_ipaddress');
            }
            if ( mysqldb_status ) {
                sessionStorage.setItem('mysqldb_status',mysqldb_status );
            }
            else {
                sessionStorage.removeItem('mysqldb_status');
            }

            sessionStorage.setItem('mysqldb_current_page',1 );
            sessionStorage.setItem('mysqldb_data_length',mysqldb_data_length );

            $.ajax({
                url:'/assets/mysqldb_list_ajax',
                type:'POST',
                data:JSON.stringify(data),
                contentType: 'application/json; charset=UTF-8',
                dataType:'JSON',
                success:function (callback) {
                    if (callback.page_content) {
                        $('div#mysqldblist_notfound').html('');
                        var page_count=callback.page_count;
                        var page_content=callback.page_content;
                        var per_page = callback.per_page;
                        $('tbody#mysqldblist_dynamic')
                            .empty()
                            .append(page_content);
                        var notes = "第1页/共 " + Math.ceil(page_count/per_page) + "页, 每页" + per_page + "条/共" + page_count + " 条";
                        $('div#mysqldblist_notes').text(notes);
                    } else {
                        $('tbody#mysqldblist_dynamic').empty();
                        $('div#mysqldblist_notfound').html('未发现任何相关记录');
                        $('div#mysqldblist_notes').text('');
                    }
                    monitor(Math.ceil(page_count/per_page),data['page'],data);
                    checkbox_op();
                }
            });
        });

        // 无任何搜索条件，默认进入主机列表页面时提交的ajax
        $.ajax({
                url:'/assets/mysqldb_list_ajax',
                type:'POST',
                data:JSON.stringify(data),
                contentType: 'application/json; charset=UTF-8',
                dataType:'JSON',
                success:function (callback) {
                    if (callback.page_content) {
                        $('div#mysqldblist_notfound').html('');
                        var page_count=callback.page_count;
                        var page_content=callback.page_content;
                        var per_page = callback.per_page;
                        $('tbody#mysqldblist_dynamic').append(page_content);
                        var notes = "第1页/共 " + Math.ceil(page_count/per_page) + "页, 每页" + per_page + "条/共" + page_count + " 条";
                        $('div#mysqldblist_notes').text(notes);
                    } else {
                        $('tbody#mysqldblist_dynamic').empty();
                        $('div#mysqldblist_notfound').html('未发现任何相关记录');
                    }
                    monitor(Math.ceil(page_count/per_page),data['page'],data);
                    checkbox_op();
                }

        });

    // 实现分页功能的函数
    function monitor(totalpages,current_page,data) {
        $('#mysqldblist_pageLimit').bootstrapPaginator({
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
                    sessionStorage.setItem('mysqldb_current_page',page );
                    data["page"] = page;
                    $.ajax({
                        url:'/assets/mysqldb_list_ajax',
                        type:'POST',
                        data:JSON.stringify(data),
                        contentType: 'application/json; charset=UTF-8',
                        dataType:'JSON',
                        success:function (callback) {
                            $("input.ipt_check_all").removeAttr("checked");
                            $('div#mysqldblist_notfound').html('');
                            var page_count=callback.page_count;
                            var page_content=callback.page_content;
                            var per_page = callback.per_page;
                            $('tbody#mysqldblist_dynamic')
                                .empty()
                                .append(page_content);
                            var notes = "第" + page + "页/共 " + Math.ceil(page_count/per_page) + "页, 每页" + per_page + "条/共" + page_count + " 条";
                            $('div#mysqldblist_notes').text(notes);
                            checkbox_op();
                        }
                    })
                }
        });
    }
    
    function checkbox_op() {
        var check_all_obj = $('input.ipt_check_all');
        check_all_obj.click(function () {
            var userlist_checked = check_all_obj.prop('checked');
            if (userlist_checked) {
                $("input.ipt_check")
                    .attr('checked',"true")
                    .prop('checked',true);
                $(".gradeX").addClass('selected');

            } else {
                $("input.ipt_check").removeAttr("checked");
                $(".gradeX").removeClass('selected');
            }
        });

        $('input.ipt_check').click(function () {
            var single_user_checked = $(this).prop('checked');
            console.log(single_user_checked);
            console.log($(this));
            if (single_user_checked) {
                $(this)
                    .attr('checked',"true")
                    .prop('checked',true);
                $(this).parent().parent('tr.gradeX').addClass('selected');
            } else {
                $(this).removeAttr("checked");
                $(this).parent().parent('tr.gradeX').removeClass('selected');
            }
        });

        $('#btn_bulk_update').click(function () {
            var isChecked;
            var user_id;
            var line_num;
            var asset_update_array = [];
            var slct_bulk_update = $('select#slct_bulk_update').val();
            var user_operation_button;
            var href_string;
            var new_href_string;

            $("table#mysqldb_list_table tr.gradeX td:nth-child(1)").each(function (key, value) {
                isChecked = $(this).children('input').prop('checked');
                user_id = $(this).children('input').val();
                if (isChecked) {
                    asset_update_array.push(user_id);
                }
            });

            var bulk_data = {"type":slct_bulk_update,"asset_update_array":asset_update_array};
            $.ajax({
                url:'/assets/mysqldb_list_bulk_ajax',
                type:'POST',
                data:JSON.stringify(bulk_data),
                contentType: 'application/json; charset=UTF-8',
                dataType:'JSON',
                success:function (callback) {
                    var status = callback.status;
                    var message = callback.msg;
                    if ( status == 1 ) {
                        $('#bulkResultModal').css("top","140px");
                        $('#bulkResultInfo')
                            .css({'color':'red'})
                            .parents('.modal-dialog')
                            .css({"padding": "20px 80px"})
                    }
                    else {
                        $('#bulkResultInfo').css({'color':'green'});
                        $("table#mysqldb_list_table tr.gradeX td:nth-child(1)").each(function (key, value) {
                            isChecked = $(this).children('input').prop('checked');
                            line_num = key + 1;
                            if (isChecked) {
                                if (slct_bulk_update == 'active') {
                                    $("table#mysqldb_list_table tr:eq(" + line_num + ") td:nth-child(6)").html('<span class="label label-primary" style="font-size:12px;">已激活</span>');
                                    user_operation_button = $("table#mysqldb_list_table tr:eq(" + line_num + ") td:nth-child(8)");
                                    href_string = user_operation_button.find('a:eq(0)').attr("href");
                                    new_href_string = href_string.replace(/1$/,0);
                                    user_operation_button.find('a:eq(0)')
                                        .text('禁用')
                                        .removeClass('btn-primary')
                                        .addClass('btn-danger')
                                        .attr("href",new_href_string);
                                }
                                else if (slct_bulk_update == 'deactive') {
                                   $("table#mysqldb_list_table tr:eq(" + line_num + ") td:nth-child(6)").html('<span class="label label-warning" style="font-size:12px;">未激活</span>');
                                    user_operation_button = $("table#mysqldb_list_table tr:eq(" + line_num + ") td:nth-child(8)");
                                    href_string = user_operation_button.find('a:eq(0)').attr("href");
                                    new_href_string = href_string.replace(/0$/,1);
                                    user_operation_button.find('a:eq(0)')
                                        .text('启用')
                                        .removeClass('btn-danger')
                                        .addClass('btn-primary')
                                        .attr("href",new_href_string);
                                }
                                else if (slct_bulk_update == 'delete') {
                                   $("table#asset_list_table tr:eq(" + line_num + ")").remove();
                                }
                                $(this).children('input')
                                    .removeAttr("checked")
                                    .end()
                                    .parent('tr.gradeX')
                                    .removeClass('selected');
                            }
                        });
                    }
                    if (! message ) {
                        $('#bulkResultInfo').empty().append("批量操作成功!");
                    }
                    else {
                        $('#bulkResultInfo').empty().append("批量操作失败!" + "<br />" + message);
                    }
                    $('input.ipt_check_all').removeAttr("checked");
                    $('#bulkResultModal').modal();
                }

            });


        });
    }


});
/**
 * Created by qiankun on 2018/3/21.
 * Last edited by qiankun on 2018/3/23.
 */

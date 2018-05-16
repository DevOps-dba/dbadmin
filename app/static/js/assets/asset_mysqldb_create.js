$(document).ready(function() {

    // $("#mysqldb_select").multiselect2side({
    //     selectedPosition: 'right',
    //     moveOptions:false,
    //     labelsx: '未选择',
    //     labeldx: '已选择'
    // });

    // $("[name='mysqldb_selectms2side__dx[]']").attr("required","true");


    // function getListsData() {
    //
    //     var ipaddress = $('#assets_host_ip').val();
    //     var data =  {
    //         "ipaddress":ipaddress
    //     };
    //
    //     $.ajax({
    //         url: '/assets/mysqldb_create_getdb_ajax',
    //         type:'POST',
    //         data:JSON.stringify(data),
    //         contentType: 'application/json; charset=UTF-8',
    //         dataType: 'JSON',
    //         success: function (callback) {
    //             if (callback) {
    //                 $.each(callback, function (index, item) {
    //                     $("#mysqldb_selectms2side__sx").append("<option value='" + item + "'>" + item + "</option>");
    //                 });
    //             }
    //         }
    //     });
    // }
    //
    // $('#show_mysqldb').click(function () {
    //     $("#mysqldb_selectms2side__sx").empty();
    //     $("[name='mysqldb_selectms2side__dx[]']").empty();
    //     getListsData();
    // });

    //
    // function postSelectData() {
    //
    //     var template_name = $("#template_name").val();
    //     var select_list;
    //     $("[name='itemselectms2side__dx[]']").each(function(){
    //         select_list = $(this).val();
    //     });
    //     var note = $("#note").val();
    //     console.log(select_list);
    //
    //     data = {
    //         data: JSON.stringify({
    //             "template_name":template_name,
    //             "select_list":select_list,
    //             "note":note
    //         })
    //     };
    //     if ( template_name && select_list) {
    //         jq.ajax({
    //             url: '/monitor/index/add_template_ajax',
    //             type: 'POST',
    //             data: data,
    //             dataType: 'JSON',
    //             success: function (callback) {
    //                 if ( callback == "OK" ) {
    //                     alert('新建主机模板成功 !!!');
    //                 }
    //                 else {
    //                     alert(callback);
    //                 }
    //             }
    //         });
    //     }
    //     else {
    //        alert('必须填写模板名称和选择监控项 !!!');
    //     }
    // }
    //
    // getListsData();
    // jq('#addtemplateSubmit').click( function () {
    //     postSelectData();
    // })

});


/**
 * Created by qiankun on 2018/3/22.
 * Last edited by qiankun on 2018/3/23.
 */

$(document).ready(function () {

    var url = window.location.href;
    var currentId = url.split('/')[url.split('/').length-1];

    function dateFtt(fmt,date)
    {
      var o = {
        "M+" : date.getMonth()+1,                 //月份
        "d+" : date.getDate(),                    //日
        "h+" : date.getHours(),                   //小时
        "m+" : date.getMinutes(),                 //分
        "s+" : date.getSeconds(),                 //秒
        "q+" : Math.floor((date.getMonth()+3)/3), //季度
        "S"  : date.getMilliseconds()             //毫秒
      };
      if(/(y+)/.test(fmt))
        fmt=fmt.replace(RegExp.$1, (date.getFullYear()+"").substr(4 - RegExp.$1.length));
      for(var k in o)
        if(new RegExp("("+ k +")").test(fmt))
      fmt = fmt.replace(RegExp.$1, (RegExp.$1.length==1) ? (o[k]) : (("00"+ o[k]).substr((""+ o[k]).length)));
      return fmt;
    }

    $('input#is_active').click(function () {
        var checked = $(this).prop('checked');
        var data =  {
            "id":currentId,
            "checked":checked
        };
        $.ajax({
            url:'/users/user_profile_update_ajax',
            type:'POST',
            data:JSON.stringify(data),
            contentType: 'application/json; charset=UTF-8',
            dataType:'JSON',
            success:function (callback) {
                var crtTime = new Date();
                if ( callback['status'] == 1 ){
                    if (checked) {
                        $(this).removeAttr("checked");
                    }
                    else {
                       $(this)
                           .attr('checked',"true")
                           .prop('checked',true);
                    }
                }
                else {
                    if (checked) {
                       $("table tr:eq(4) td:nth-child(2)")
                           .removeClass('text-danger')
                           .addClass('text-navy')
                           .html('<b>已激活</b>');
                    }
                    else {
                       $("table tr:eq(4) td:nth-child(2)")
                           .removeClass('text-navy')
                           .addClass('text-danger')
                           .html('<b>未激活</b>');
                    }
                    $("table tr:eq(6) td:nth-child(2)").html('<b>'+dateFtt("yyyy-MM-dd hh:mm:ss",crtTime)+'</b>');
                }
            }
        });

    });

    $('a#updatePassword').click(function () {
        $('input#newPassword').val('');
        $.ajax({
            url:'/users/user_profile_autopwd_ajax',
            type:'GET',
            contentType: 'application/json; charset=UTF-8',
            dataType:'JSON',
            success:function (callback) {
                $('input#newPassword').val(callback);
                $('#updatePwdModal').modal();
            }
        });
        $('a#autoPassword').click(function () {
            $('input#newPassword').val('');
            $.ajax({
                url:'/users/user_profile_autopwd_ajax',
                type:'GET',
                contentType: 'application/json; charset=UTF-8',
                dataType:'JSON',
                success:function (callback) {
                    $('input#newPassword').val(callback);
                }

            });
        });

        $('a#updatePwdSubmit').click(function () {
            var newPassword = $('input#newPassword').val();
            data = {"id":currentId,"newpwd":newPassword};
            $.ajax({
                url:'/users/user_profile_updatepwd_ajax',
                type:'POST',
                data:JSON.stringify(data),
                contentType: 'application/json; charset=UTF-8',
                dataType:'JSON',
                success:function (callback) {
                    $('#updatePwdModal').modal('hide');
                }

            });
        });
    });

});

/**
 * Created by Admin on 2018/3/15.
 */

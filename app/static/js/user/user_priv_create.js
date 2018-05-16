$(document).ready(function () {

   $('#new_select_db').click(function () {
       var db_id;
       var existed_db_array = [];

       $("table#select_db_table tr.gradeX").each(function (key, value) {
           db_id = $(this).children().eq(0).children('input').val();
           existed_db_array.push(db_id);
       });
       data = {"existed_db_array":''};
       if (existed_db_array.length > 0) {
           data = {"existed_db_array":existed_db_array};
       }

       $.ajax({
           url: '/users/get_all_db_ajax',
           type: 'POST',
           data:JSON.stringify(data),
           contentType: 'application/json; charset=UTF-8',
           dataType: 'JSON',
           success: function (callback) {
               if (callback.page_content) {
                   $('div#all_db_notfound').html('');
                   var page_content = callback.page_content;
                   $('tbody#all_db_dynamic')
                       .empty()
                       .append(page_content);
               } else {
                   $('tbody#all_db_dynamic').empty();
                   $('div#all_db_notfound').html('未发现任何相关记录');
               }
               checkbox_op();
               $('#addDatabaseModal').modal();
           }
       });


       $('#addDatabaseSubmit')
           .unbind()
           .click(function () {
           var isChecked;
           var db_id;
           var db_name;
           var db_ip;
           var selected_db_array = [];
           var tbody_string = '';

           $("table#all_db_table tr.gradeX td:nth-child(1)").each(function (key, value) {
                isChecked = $(this).children('input').prop('checked');
                db_id = $(this).children('input').val();
                db_name = $(this).parent().closest('td').text();
                if (isChecked) {
                    db_name = $(this).parent('tr.gradeX').children().eq(1).text();
                    db_ip = $(this).parent('tr.gradeX').children().eq(2).text();
                    selected_db_array.push({"db_id":db_id,"db_name":db_name,"db_ip":db_ip});
                }
           });

          $(selected_db_array).each(function(i,n){
              tbody_string += '<tr class="gradeX"><td class="text-center"><input type="checkbox" name="checked" value="'+ n['db_id'] +'" class="ipt_check"></td> <td class="text-center">' + n['db_name']+ '</td><td class="text-center">' + n['db_ip'] + '</td><td class="text-center"><input type="checkbox" name="checked" value="" class="ipt_check_ddl"></td><td class="text-center"><input type="checkbox" name="checked" value="" class="ipt_check_dml"></td></tr>';
          });
          $('tbody#select_db_dynamic').append(tbody_string);
          checkbox_op();
       });


   });

   $('#btn_bulk_update').click(function () {
        var isChecked;
        var slct_bulk_update = $('select#slct_bulk_update').val();
        if (slct_bulk_update == 'delete') {
            $("table#select_db_table tr.gradeX td:nth-child(1)").each(function (key, value) {
                isChecked = $(this).children('input').prop('checked');
                console.log(isChecked);
                if (isChecked) {
                    $(this).closest('tr.gradeX').remove();
                }
            });
        }
        else {
            $("table#select_db_table tr.gradeX td:nth-child(1)").each(function (key, value) {
                isChecked = $(this).children('input').prop('checked');
                if (isChecked) {
                    $(this).closest('tr.gradeX').children().eq(4).find('input')
                        .attr('checked', "true")
                        .prop('checked', true)
                        .end()
                        .end()
                        .eq(3).find('input')
                        .attr('checked', "true")
                        .prop('checked', true);
                }
            });
        }
        $('input.ipt_check_all').removeAttr("checked");
        $('input.ipt_check').removeAttr("checked").closest('tr.gradeX').removeClass("selected");

    });


   function checkbox_op() {
       $('input.ipt_check_all').click(function () {
           var userlist_checked = $(this).prop('checked');
           if (userlist_checked) {
               $("input.ipt_check")
                   .attr('checked', "true")
                   .prop('checked', true);
               $(".gradeX").addClass('selected');

           } else {
               $("input.ipt_check").removeAttr("checked");
               $(".gradeX").removeClass('selected');
           }
       });

       $('input.ipt_check').click(function () {
           var single_user_checked = $(this).prop('checked');
           if (single_user_checked) {
               $(this)
                   .attr('checked', "true")
                   .prop('checked', true);
               $(this).parent().parent('tr.gradeX').addClass('selected');
           } else {
               $(this).removeAttr("checked");
               $(this).parent().parent('tr.gradeX').removeClass('selected');
           }
       });
   }

   $('#new_priv_submit').click(function () {
       var users_name = $('input#users_name').val();
       var db_id;
       var db_priv_ddl;
       var db_priv_dml;
       var db_priv_type;
       var selected_db_id = [];
       $("table#select_db_table tr.gradeX td:nth-child(1)").each(function (key, value) {
           db_id = $(this).children('input').val();
           db_priv_ddl = $(this).parent().children().eq(3).find('input').prop('checked');
           db_priv_dml = $(this).parent().children().eq(4).find('input').prop('checked');
           if (db_priv_ddl && db_priv_dml) {
               db_priv_type = 0
           }
           else if (! db_priv_ddl && db_priv_dml) {
               db_priv_type = 1
           }
           else if ( db_priv_ddl && ! db_priv_dml) {
               db_priv_type = 2
           }
           else {
               return true
           }
           selected_db_id.push({"db_id":db_id,"db_priv_type":db_priv_type});
       });

       data = {"users_name":users_name,"selected_db_id":selected_db_id};
       $.ajax({
           url: '/users/user_priv_create_ajax',
           type: 'POST',
           data:JSON.stringify(data),
           contentType: 'application/json; charset=UTF-8',
           dataType: 'JSON',
           success: function (callback) {
               if ($('.alert').length > 0 ) {
                   $('#alert_info').empty().text(callback.msg);
                   if (callback.status == 1) {
                      $('.help-message').removeClass("alert-info").addClass("alert-danger").show();
                   }
                   else {
                      $('.help-message').removeClass("alert-danger").addClass("alert-info").show();
                   }
               }
               else {
                   $('.m-t').after('<div class="alert alert-info alert-dismissible help-message" style="margin-left: 0;display: none;"><button type="button" class="close" data-dismiss="alert" aria-hidden="true"> &times; </button> <div id="alert_info"></div> </div>');
                   $('#alert_info').empty().text(callback.msg);
                   if (callback.status == 1) {
                      $('.help-message').removeClass("alert-info").addClass("alert-danger").show();
                   }
                   else {
                      $('.help-message').removeClass("alert-danger").addClass("alert-info").show();
                   }
               }


           }
       });


   });


});

/**
 * Created by qiankun on 2018/3/28.
 * Lasted by qiankun on 2018/3/29
 */

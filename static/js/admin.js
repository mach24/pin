// Generated by CoffeeScript 1.4.0
(function() {

  jQuery(function() {
    $("#add_new_admin_user_button").click(function() {
      window.location.href = '/admin/admin_user/';
    });
    $("#add_new_admin_permission_button").click(function() {
      window.location.href = '/admin/admin_rol/';
    });
    $("#admin_permission_list").on('click', '.delete', function() {
      $.permsid = $(this).attr('permsid');
      $.permsname = $(this).attr('permsname');
      $("#delete_confirmation_dialog_id").html($.permsid);
      $("#delete_confirmation_dialog_name").html($.permsname);
      $("#admin_rol_delete_confirmation_dialog").dialog('open');
    });
    $('#admin_rol_delete_confirmation_dialog').dialog({
      autoOpen: false,
      modal: true,
      buttons: {
        'Cancel': function() {
          $(this).dialog('close');
        },
        'Confirm delete': function() {
          var url;
          $.confirm_dialog = $(this);
          url = "/admin/admin_rol/" + $.permsid + "/";
          $.ajax(url, {
            type: 'DELETE',
            dataType: 'json',
            success: function(data) {
              $("#perm" + $.permsid).remove();
              $.confirm_dialog.dialog('close');
            }
          });
        }
      }
    });
    $("#admin_users_list").on('click', '.delete', function() {
      $.userid = $(this).attr('userid');
      $.username = $(this).attr('username');
      $("#delete_confirmation_dialog_id").html($.userid);
      $("#delete_confirmation_dialog_name").html($.username);
      $("#admin_user_delete_confirmation_dialog").dialog('open');
    });
    $('#admin_user_delete_confirmation_dialog').dialog({
      autoOpen: false,
      modal: true,
      buttons: {
        'Cancel': function() {
          $(this).dialog('close');
        },
        'Confirm delete': function() {
          var url;
          $.confirm_dialog = $(this);
          url = "/admin/admin_user/" + $.userid + "/";
          $.ajax(url, {
            type: 'DELETE',
            dataType: 'json',
            success: function(data) {
              $("#user" + $.userid).remove();
              $.confirm_dialog.dialog('close');
            }
          });
        }
      }
    });
    $('#admin_user_list_next_button').click(function() {
      var limit, offset;
      limit = parseInt($('#limit').attr('value'));
      offset = parseInt($('#offset').attr('value'));
      $('#offset').attr('value', offset + limit);
      $('form').submit();
    });
    $('#admin_user_list_prev_button').click(function() {
      var limit, offset;
      limit = parseInt($('#limit').attr('value'));
      offset = parseInt($('#offset').attr('value'));
      $('#offset').attr('value', offset - limit);
      $('form').submit();
    });
    $("#add_new_admin_media_server_button").click(function() {
      window.location.href = '/admin/media_server/';
    });
    $("#admin_media_server_list").on('click', '.delete', function() {
      $.media_serverid = $(this).attr('media_serverid');
      $.media_serverurl = $(this).attr('media_serverurl');
      $("#delete_confirmation_dialog_id").html($.media_serverid);
      $("#delete_confirmation_dialog_name").html($.media_serverurl);
      $("#admin_media_server_delete_confirmation_dialog").dialog('open');
    });
    $('#admin_media_server_delete_confirmation_dialog').dialog({
      autoOpen: false,
      modal: true,
      buttons: {
        'Cancel': function() {
          $(this).dialog('close');
        },
        'Confirm delete': function() {
          var url;
          $.confirm_dialog = $(this);
          url = "/admin/media_server/" + $.media_serverid + "/";
          $.ajax(url, {
            type: 'DELETE',
            dataType: 'json',
            success: function(data) {
              $("#media_server" + $.media_serverid).remove();
              $.confirm_dialog.dialog('close');
            }
          });
        }
      }
    });
  });

}).call(this);

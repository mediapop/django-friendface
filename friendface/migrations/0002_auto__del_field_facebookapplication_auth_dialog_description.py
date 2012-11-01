# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'FacebookApplication.auth_dialog_description'
        db.delete_column('friendface_facebookapplication', 'auth_dialog_description')


    def backwards(self, orm):
        # Adding field 'FacebookApplication.auth_dialog_description'
        db.add_column('friendface_facebookapplication', 'auth_dialog_description',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


    models = {
        'friendface.facebookapplication': {
            'Meta': {'object_name': 'FacebookApplication'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'auth_dialog_data_help_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'auth_dialog_headline': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'auth_dialog_perms_explanation': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'auth_referral_default_activity_privacy': ('django.db.models.fields.CharField', [], {'max_length': '11', 'null': 'True', 'blank': 'True'}),
            'auth_referral_enabled': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'auth_referral_extended_perms': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'canvas_fluid_height': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'canvas_fluid_width': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'canvas_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '23', 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'created_time': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'daily_active_users': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'deauth_callback_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'default_scope': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hosting_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'icon_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'iphone_app_store_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'logo_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'mobile_web_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'monthly_active_users': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'page_tab_default_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'page_tab_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'privacy_policy_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'secure_canvas_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'secure_page_tab_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'social_discovery': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'subcategory': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'terms_of_service_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user_support_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'user_support_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'website_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'weekly_active_users': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'friendface.facebookauthorization': {
            'Meta': {'object_name': 'FacebookAuthorization'},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['friendface.FacebookApplication']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'redirect_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'scope': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'friendface.facebookinvitation': {
            'Meta': {'unique_together': "(('request_id', 'receiver'),)", 'object_name': 'FacebookInvitation'},
            'accepted': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['friendface.FacebookApplication']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'receiver': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'facebookinvitations_received'", 'to': "orm['friendface.FacebookUser']"}),
            'request_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'facebookinvitations_sent'", 'to': "orm['friendface.FacebookUser']"})
        },
        'friendface.facebookpage': {
            'Meta': {'object_name': 'FacebookPage'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'likes': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name_space': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'talking_about_count': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'friendface.facebooktab': {
            'Meta': {'object_name': 'FacebookTab'},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['friendface.FacebookApplication']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['friendface.FacebookPage']"})
        },
        'friendface.facebookuser': {
            'Meta': {'unique_together': "(('uid', 'application'),)", 'object_name': 'FacebookUser'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['friendface.FacebookApplication']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'locale': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'religion': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.IntegerField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'uid': ('django.db.models.fields.BigIntegerField', [], {})
        }
    }

    complete_apps = ['friendface']
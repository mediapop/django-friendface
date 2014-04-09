from django.contrib import admin
from friendface.models import (FacebookApplication,
                               FacebookPage,
                               FacebookUser,
                               FacebookTab, FacebookInvitation, FacebookAuthorization)


class PageTabInline(admin.StackedInline):
    model = FacebookTab
    extra = 0


class FacebookPageAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'id', 'link', 'likes', 'is_published')
    inlines = (PageTabInline,)
    readonly_fields = ('name',
                       'link',
                       'likes',
                       'talking_about_count',
                       'category',
                       'is_published')


class FacebookApplicationAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'id', 'has_privacy_policy', 'url',
                    '_installation_url')
    readonly_fields = ('name',
                       'access_token',
                       'namespace',
                       'url',
                       'description',
                       'category',
                       'subcategory',
                       'company',
                       'icon_url',
                       'link',
                       'logo_url',
                       'daily_active_users',
                       'weekly_active_users',
                       'monthly_active_users',
                       'auth_dialog_data_help_url',
                       'auth_dialog_headline',
                       'auth_dialog_perms_explanation',
                       'auth_referral_default_activity_privacy',
                       'auth_referral_enabled',
                       'auth_referral_extended_perms',
                       'canvas_fluid_height',
                       'canvas_fluid_width',
                       'canvas_url',
                       'contact_email',
                       'deauth_callback_url',
                       'iphone_app_store_id',
                       'hosting_url',
                       'mobile_web_url',
                       'page_tab_default_name',
                       'page_tab_url',
                       'privacy_policy_url',
                       'secure_canvas_url',
                       'secure_page_tab_url',
                       'social_discovery',
                       'terms_of_service_url',
                       'user_support_email',
                       'user_support_url',
                       'website_url')
    exclude = ('access_token_updated_at',)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(FacebookApplicationAdmin, self)\
            .get_readonly_fields(request, obj)

        if not obj is None:
            change_readonly_fields = ['id']
            change_readonly_fields.extend(readonly_fields)
            return change_readonly_fields

        return readonly_fields

    def has_privacy_policy(self, obj):
        return not obj.privacy_policy_url is None
    has_privacy_policy.boolean = True

    def url(self, obj):
        if obj.namespace:
            return '<a href="{0}" target="_blank">{0}</a>'.format(obj.url)
        else:
            return ''
    url.allow_tags = True

    def _installation_url(self, obj):
        if obj.secure_canvas_url:
            return '<a href="{0}" target="_blank">Install</a>'.format(
                obj.get_installation_url()
            )
        else:
            return ''
    _installation_url.allow_tags = True

    inlines = (PageTabInline,)


class FacebookUserAdmin(admin.ModelAdmin):
    list_filter = ('gender', 'application')
    date_hierarchy = 'created'
    search_fields = ('first_name', 'last_name', 'email', 'uid')
    exclude = ('access_token_updated_at',)
    list_display = ('__unicode__',
                    'uid',
                    'first_name',
                    'last_name',
                    'email',
                    'gender',
                    'application',
                    'created')
    readonly_fields = ('uid', 'application', 'created', 'first_name',
                       'last_name', 'timezone', 'religion', 'locale',
                       'location', 'email', 'gender', 'access_token')


class FacebookInvitationAdmin(admin.ModelAdmin):
    search_fields = ('sender__first_name',
                     'sender__last_name',
                     'receiver__first_name',
                     'receiver__last_name')
    date_hierarchy = 'created'
    readonly_fields = ('request_id',
                       'created',
                       'application',
                       'sender',
                       'receiver',
                       'accepted',
                       'next')
    list_filter = ('application',)
    list_display = ('__unicode__', 'created', 'sender', 'receiver',
                    'is_accepted')

    def is_accepted(self, obj):
        return obj.accepted is not None
    is_accepted.boolean = True


class FacebookAuthorizationAdmin(admin.ModelAdmin):
    readonly_fields = (
        'application',
        'scope',
        'redirect_uri',
        'next'
    )
    list_display = (
        'application', 'scope', 'redirect_uri', 'next'
    )

admin.site.register(FacebookPage, FacebookPageAdmin)
admin.site.register(FacebookApplication, FacebookApplicationAdmin)
admin.site.register(FacebookUser, FacebookUserAdmin)
admin.site.register(FacebookInvitation, FacebookInvitationAdmin)
admin.site.register(FacebookAuthorization, FacebookAuthorizationAdmin)
from django.urls import path, re_path
from .views import (
    ConferenceListView, ConferenceCreateView, ConferenceUpdateView,
    ConferenceDeleteView, conference_detail, DashboardView, ConferenceManagementView
)
from .views.conference_views import (
    conference_register,
    manage_participants, 
    create_participant, 
    edit_participant, 
    conference_info,
    delete_contact
)
from .views.registration_views import (
    company_registration_manage, 
    add_participant
)
from .views.form_views import (
    manage_form, 
    set_current_form, 
    formio_builder, 
    manage_formio, 
    render_formio, 
    delete_formio,
    submit_formio
)
from .views.api_views import (
    get_registration_form, 
    create_registration_form, 
    update_registration_form,
    delete_registration_form, 
    preview_registration_form, 
    get_field_logic_rules,
    save_field_logic_rules, 
    assign_tags_to_participants, 
    assign_group_to_participants,
    batch_delete_participants
)
from .views.survey_views import (
    survey_list, 
    survey_create, 
    survey_edit, 
    survey_delete, 
    survey_publish, 
    survey_responses, 
    survey_fill
)
from .views.survey_analysis_views import (
    survey_analysis, 
    survey_analysis_data, 
    survey_cross_analysis, 
    survey_trend_analysis, 
    export_survey_data
)
from .views.survey_template_views import (
    template_list, 
    template_create, 
    template_edit, 
    template_delete, 
    create_survey_from_template
)
from .views.survey_stats_views import (
    user_survey_stats,
    survey_completion_stats,
    conference_survey_stats,
    export_completion_stats,
    export_completion_report,
    survey_completion_chart
)
from .views.survey_reminder_views import (
    reminder_list,
    reminder_create,
    reminder_edit,
    reminder_delete,
    reminder_toggle,
    reminder_logs,
    reminder_preview
)

app_name = 'conference'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('create/', ConferenceCreateView.as_view(), name='create'),
    path('<int:pk>/', conference_detail, name='detail'),
    path('<int:pk>/edit/', ConferenceUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', ConferenceDeleteView.as_view(), name='delete'),
    path('management/', ConferenceManagementView.as_view(), name='management'),
    path('list/', ConferenceListView.as_view(), name='list'),
    path('<int:pk>/register/', conference_register, name='register'),
    path('<int:conference_id>/company-registration/', company_registration_manage, name='company_registration_manage'),
    path('<int:conference_id>/add-participant/', add_participant, name='add_participant'),
    path('registration/manage/', manage_form, name='manage_form'),  # 表单管理
    # Form.io 相关路由
    path('registration/formio-builder/', formio_builder, name='formio_builder'),
    # Form.io 表单管理
    path('registration/manage-formio/', manage_formio, name='manage_formio'),
    re_path(r'^(?P<conference_id>\d+)/registration/formio/?$', render_formio, name='render_formio'),
    path('set-current-form/', set_current_form, name='set_current_form'),  # 设置当前表单
    # Form.io 表单提交
    path('<int:conference_id>/registration/formio/submit/', submit_formio, name='submit_formio'),
    path('conference/<int:conference_id>/participants/', manage_participants, name='manage_participants'),
    path('conference/<int:conference_id>/info/', conference_info, name='conference_info'),
    path('conference/<int:conference_id>/participants/create/', create_participant, name='create_participant'),
    path('conference/<int:conference_id>/participants/<int:participant_id>/edit/', edit_participant, name='edit_participant'),
    path('conference/<int:conference_id>/participants/batch-delete/', batch_delete_participants, name='batch_delete_participants'),
    # 问卷调查
    path('survey/', survey_list, name='survey_list'),
    path('survey/create/', survey_create, name='survey_create'),
    path('survey/<int:survey_id>/edit/', survey_edit, name='survey_edit'),
    path('survey/<int:survey_id>/delete/', survey_delete, name='survey_delete'),
    path('survey/<int:survey_id>/publish/', survey_publish, name='survey_publish'),
    path('survey/<int:survey_id>/responses/', survey_responses, name='survey_responses'),
    path('survey/<int:survey_id>/conference/<int:conference_id>/fill/', survey_fill, name='survey_fill'),
    # 问卷分析
    path('survey/<int:survey_id>/analysis/', survey_analysis, name='survey_analysis'),
    path('survey/<int:survey_id>/analysis/data/', survey_analysis_data, name='survey_analysis_data'),
    path('survey/<int:survey_id>/analysis/cross/', survey_cross_analysis, name='survey_cross_analysis'),
    path('survey/<int:survey_id>/analysis/trend/', survey_trend_analysis, name='survey_trend_analysis'),
    path('survey/<int:survey_id>/export/', export_survey_data, name='export_survey_data'),
    # 问卷统计
    path('survey/stats/', user_survey_stats, name='user_survey_stats'),
    path('survey/<int:survey_id>/stats/', survey_completion_stats, name='survey_completion_stats'),
    path('conference/<int:conference_id>/survey-stats/', conference_survey_stats, name='conference_survey_stats'),
    path('conference/<int:conference_id>/survey-stats/export/', export_completion_stats, name='export_completion_stats'),
    path('conference/<int:conference_id>/survey-stats/report/', export_completion_report, name='export_completion_report'),
    path('conference/<int:conference_id>/survey-stats/chart/', survey_completion_chart, name='survey_completion_chart'),
    # 问卷模板
    path('survey/template/', template_list, name='template_list'),
    path('survey/template/create/', template_create, name='template_create'),
    path('survey/template/<int:template_id>/edit/', template_edit, name='template_edit'),
    path('survey/template/<int:template_id>/delete/', template_delete, name='template_delete'),
    path('survey/template/<int:template_id>/create-survey/', create_survey_from_template, name='create_survey_from_template'),
    # 问卷提醒
    path('survey/<int:survey_id>/reminders/', reminder_list, name='reminder_list'),
    path('survey/<int:survey_id>/reminders/create/', reminder_create, name='reminder_create'),
    path('survey/reminder/<int:reminder_id>/edit/', reminder_edit, name='reminder_edit'),
    path('survey/reminder/<int:reminder_id>/delete/', reminder_delete, name='reminder_delete'),
    path('survey/reminder/<int:reminder_id>/toggle/', reminder_toggle, name='reminder_toggle'),
    path('survey/reminder/<int:reminder_id>/logs/', reminder_logs, name='reminder_logs'),
    path('survey/reminder/<int:reminder_id>/preview/', reminder_preview, name='reminder_preview'),
    # API endpoints
    path('api/registration-form/<int:form_id>/', get_registration_form, name='get_registration_form'),
    path('api/registration-form/create/', create_registration_form, name='create_registration_form'),
    path('api/registration-form/<int:form_id>/update/', update_registration_form, name='update_registration_form'),
    path('api/registration-form/<int:form_id>/delete/', delete_registration_form, name='delete_registration_form'),
    path('api/registration-form/delete/', delete_formio, name='delete_formio'),
    path('api/registration-form/<int:form_id>/preview/', preview_registration_form, name='preview_registration_form'),
    path('api/registration-form/<int:form_id>/logic-rules/', get_field_logic_rules, name='get_field_logic_rules'),
    path('api/registration-form/<int:form_id>/logic-rules/save/', save_field_logic_rules, name='save_field_logic_rules'),
    path('api/participants/assign-tags/', assign_tags_to_participants, name='assign_tags_to_participants'),
    path('api/participants/assign-group/', assign_group_to_participants, name='assign_group_to_participants'),
    # 联系人管理
    path('contact/delete/<int:contact_id>/', delete_contact, name='delete_contact'),
]

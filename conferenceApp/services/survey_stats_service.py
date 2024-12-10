from django.db.models import Count, F, Q
from django.utils import timezone
from django.db.models.functions import TruncDate
from ..models.survey import Survey, SurveyResponse
from ..models.participant import Participant

class SurveyStatsService:
    @staticmethod
    def get_survey_completion_stats(survey):
        """获取问卷的整体完成统计"""
        total_participants = 0
        completed_count = 0
        completion_rate = 0
        
        # 获取所有需要填写此问卷的会议
        conferences = survey.conferences.all()
        
        for conference in conferences:
            # 获取会议参与者数量
            participant_count = conference.participants.count()
            total_participants += participant_count
            
            # 获取已完成问卷的人数
            completed = SurveyResponse.objects.filter(
                survey=survey,
                conference=conference
            ).count()
            completed_count += completed
        
        if total_participants > 0:
            completion_rate = (completed_count / total_participants) * 100
            
        return {
            'total_participants': total_participants,
            'completed_count': completed_count,
            'completion_rate': round(completion_rate, 2),
            'remaining_count': total_participants - completed_count
        }
    
    @staticmethod
    def get_user_survey_stats(user):
        """获取用户的问卷完成统计"""
        # 获取用户参与的所有会议
        conferences = user.participating_conferences.all()
        
        stats = {
            'total_required': 0,
            'completed': 0,
            'pending': 0,
            'completion_rate': 0,
            'surveys': []
        }
        
        for conference in conferences:
            # 获取会议中的所有问卷
            conference_surveys = conference.surveys.filter(
                status='published',
                surveyconference__is_required=True
            )
            
            for survey in conference_surveys:
                if survey.is_active:
                    stats['total_required'] += 1
                    
                    # 检查是否已完成
                    completed = SurveyResponse.objects.filter(
                        survey=survey,
                        user=user,
                        conference=conference
                    ).exists()
                    
                    if completed:
                        stats['completed'] += 1
                    else:
                        stats['pending'] += 1
                        
                    # 添加具体问卷信息
                    stats['surveys'].append({
                        'survey': survey,
                        'conference': conference,
                        'completed': completed,
                        'due_date': survey.end_time
                    })
        
        if stats['total_required'] > 0:
            stats['completion_rate'] = (stats['completed'] / stats['total_required']) * 100
            
        return stats
    
    @staticmethod
    def get_conference_survey_stats(conference):
        """获取会议的问卷完成统计"""
        # 获取会议中的所有问卷
        surveys = conference.surveys.all()
        participant_count = conference.participants.count()
        
        stats = {
            'total_surveys': surveys.count(),
            'total_participants': participant_count,
            'surveys': []
        }
        
        for survey in surveys:
            # 获取此问卷的完成情况
            completed_count = SurveyResponse.objects.filter(
                survey=survey,
                conference=conference
            ).count()
            
            completion_rate = 0
            if participant_count > 0:
                completion_rate = (completed_count / participant_count) * 100
                
            # 获取每日完成数量
            daily_stats = SurveyResponse.objects.filter(
                survey=survey,
                conference=conference
            ).annotate(
                date=TruncDate('submitted_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            stats['surveys'].append({
                'survey': survey,
                'is_required': survey.surveyconference_set.get(conference=conference).is_required,
                'completed_count': completed_count,
                'remaining_count': participant_count - completed_count,
                'completion_rate': round(completion_rate, 2),
                'daily_stats': list(daily_stats)
            })
            
        return stats
    
    @staticmethod
    def get_participant_completion_list(conference, survey=None):
        """获取参与者完成情况列表"""
        participants = conference.participants.all()
        
        completion_list = []
        for participant in participants:
            if survey:
                # 获取特定问卷的完成情况
                completed = SurveyResponse.objects.filter(
                    survey=survey,
                    conference=conference,
                    user=participant.user
                ).exists()
                
                completion_list.append({
                    'participant': participant,
                    'completed': completed,
                    'completed_at': SurveyResponse.objects.filter(
                        survey=survey,
                        conference=conference,
                        user=participant.user
                    ).values_list('submitted_at', flat=True).first()
                })
            else:
                # 获取所有问卷的完成情况
                required_surveys = conference.surveys.filter(
                    status='published',
                    surveyconference__is_required=True
                )
                completed_surveys = SurveyResponse.objects.filter(
                    conference=conference,
                    user=participant.user
                ).values_list('survey_id', flat=True)
                
                completion_list.append({
                    'participant': participant,
                    'total_required': required_surveys.count(),
                    'completed_count': len(completed_surveys),
                    'completion_rate': round(len(completed_surveys) / required_surveys.count() * 100, 2) if required_surveys.count() > 0 else 0
                })
                
        return completion_list
    
    @staticmethod
    def get_survey_completion_chart_data(conference):
        """获取问卷完成情况的图表数据"""
        surveys = conference.surveys.all()
        
        chart_data = {
            'labels': [],
            'completion_rates': [],
            'completed_counts': [],
            'total_participants': [],
            'colors': [
                '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', 
                '#f59e0b', '#10b981', '#06b6d4', '#3b82f6'
            ]
        }
        
        for survey in surveys:
            survey_stats = SurveyStatsService.get_survey_completion_stats(survey)
            
            chart_data['labels'].append(survey.title)
            chart_data['completion_rates'].append(survey_stats['completion_rate'])
            chart_data['completed_counts'].append(survey_stats['completed_count'])
            chart_data['total_participants'].append(survey_stats['total_participants'])
        
        return chart_data
    
    @staticmethod
    def generate_survey_completion_report(conference):
        """自动生成问卷完成统计报告"""
        stats = SurveyStatsService.get_conference_survey_stats(conference)
        chart_data = SurveyStatsService.get_survey_completion_chart_data(conference)
        completion_list = SurveyStatsService.get_participant_completion_list(conference)
        
        # 生成报告文本
        report = f"问卷完成度统计报告 - {conference.name}\n"
        report += f"生成时间：{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "1. 整体统计\n"
        report += f"   - 总问卷数：{len(stats['surveys'])}\n"
        report += f"   - 总参与者：{stats['total_participants']} 人\n\n"
        
        report += "2. 问卷完成情况\n"
        for survey_stat in stats['surveys']:
            report += f"   - {survey_stat['survey'].title}\n"
            report += f"     * 完成人数：{survey_stat['completed_count']} 人\n"
            report += f"     * 剩余人数：{survey_stat['remaining_count']} 人\n"
            report += f"     * 完成率：{survey_stat['completion_rate']}%\n\n"
        
        report += "3. 参与者完成情况\n"
        completed_participants = [p for p in completion_list if p['completed_count'] > 0]
        uncompleted_participants = [p for p in completion_list if p['completed_count'] == 0]
        
        report += f"   - 已完成问卷：{len(completed_participants)} 人\n"
        report += f"   - 未完成问卷：{len(uncompleted_participants)} 人\n\n"
        
        # 生成详细的参与者完成情况
        report += "4. 参与者详细完成情况\n"
        for participant in completion_list:
            report += f"   - {participant['participant'].user.get_full_name()}\n"
            report += f"     * 完成问卷数：{participant['completed_count']}\n"
            report += f"     * 完成率：{participant['completion_rate']}%\n\n"
        
        return {
            'text_report': report,
            'chart_data': chart_data
        }

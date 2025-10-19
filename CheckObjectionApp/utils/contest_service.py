# services/contest_service.py
from django.utils import timezone
from django.db.models import Count, Min, Q

from CheckObjectionApp.models import ContestParticipant


class ContestService:
    @staticmethod
    def get_contest_ranklist(contest_id):
        """获取比赛排名"""
        from CheckObjectionApp.models import ContestParticipant, ContestSubmission, ContestTopic

        participants = ContestParticipant.objects.filter(
            contest_id=contest_id,
            is_disqualified=False
        ).select_related('user')

        rank_data = []
        for participant in participants:
            # 计算每个参与者的解题情况
            submissions = ContestSubmission.objects.filter(
                participant=participant
            ).select_related('submission')

            # 统计AC的题目和罚时
            solved_problems = set()
            total_penalty = 0
            problem_stats = {}

            for contest_submission in submissions:
                topic_id = contest_submission.submission.topic_id
                if topic_id not in problem_stats:
                    problem_stats[topic_id] = {
                        'solved': False,
                        'submit_count': 0,
                        'ac_time': None,
                        'penalty': 0
                    }

                stats = problem_stats[topic_id]
                stats['submit_count'] += 1

                if contest_submission.submission.overall_result == 'AC' and not stats['solved']:
                    stats['solved'] = True
                    # 计算AC时间（从比赛开始到提交的时间，分钟）
                    ac_time = (
                                          contest_submission.submitted_at - contest_submission.contest.start_time).total_seconds() / 60
                    stats['ac_time'] = ac_time
                    # 罚时 = AC时间 + (错误提交次数 * 罚时分钟)
                    stats['penalty'] = ac_time + (stats['submit_count'] - 1) * contest_submission.contest.penalty_time
                    solved_problems.add(topic_id)
                    total_penalty += stats['penalty']

            rank_data.append({
                'participant': participant,
                'solved_count': len(solved_problems),
                'total_penalty': total_penalty,
                'problem_stats': problem_stats
            })

        # 按解题数降序，罚时升序排序
        rank_data.sort(key=lambda x: (-x['solved_count'], x['total_penalty']))
        return rank_data

    @staticmethod
    def can_view_contest(user, contest):
        """检查用户是否有权限查看比赛"""
        if contest.is_public:
            return True
        return ContestParticipant.objects.filter(
            contest=contest, user=user
        ).exists()
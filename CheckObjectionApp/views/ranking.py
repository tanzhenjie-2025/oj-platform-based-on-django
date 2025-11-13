# CheckObjectionApp/views/ranking.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from ..models import Contest, ContestParticipant, ContestSubmission, Submission


def ranking_view(request):
    """全局排行榜页面"""
    # 获取所有用户通过的题目统计（去重）
    user_rankings = Submission.objects.filter(
        overall_result='Accepted'
    ).values('user_name').annotate(
        solved_count=Count('topic_id', distinct=True)
    ).order_by('-solved_count')

    # 构建排行榜数据
    rankings = []
    for rank, user_data in enumerate(user_rankings, 1):
        rankings.append({
            'rank': rank,
            'user_name': user_data['user_name'],
            'solved_count': user_data['solved_count'],
        })

    context = {
        'rankings': rankings,
        'total_users': len(rankings),
        'page_title': '全局排行榜'
    }
    return render(request, 'CheckObjection/CheckObjection_ranking.html', context)


def contest_ranking(request, contest_id):
    """比赛排名页面"""
    contest = get_object_or_404(Contest, id=contest_id)
    rankings = get_contest_rankings(contest)

    context = {
        'contest': contest,
        'rankings': rankings,
        'total_users': len(rankings),
        'page_title': f'{contest.title} - 排行榜'
    }
    return render(request, 'CheckObjection/CheckObjection_ranking.html', context)


def contest_rank_list(request):
    """展示所有比赛列表"""
    contests = Contest.objects.all().order_by('-start_time')

    # 为每个比赛添加统计信息
    for contest in contests:
        contest.participant_count = contest.participants.count()
        contest.topic_count = contest.contest_topics.count()

    context = {
        'contests': contests,
        'page_title': '比赛排行榜'
    }
    return render(request, 'CheckObjection/contest/rank/rank_list.html', context)


def contest_rank_detail(request, contest_id):
    """展示具体比赛的排名详情 - 生产版本"""
    contest = get_object_or_404(Contest, id=contest_id)

    # 获取比赛的所有题目
    contest_topics = contest.contest_topics.select_related('topic').order_by('order')

    # 获取所有参赛者
    participants = contest.participants.filter(is_disqualified=False).select_related('user')

    # 构建排名数据
    rank_data = []

    for participant in participants:
        user = participant.user

        # 获取该用户在比赛中的所有提交
        contest_submissions = ContestSubmission.objects.filter(
            contest=contest,
            participant=participant
        ).select_related('submission', 'submission__topic').order_by('submitted_at')

        # 统计每个题目的最佳提交
        topic_results = {}
        total_accepted = 0
        total_penalty = 0

        # 按题目分组处理提交
        for contest_topic in contest_topics:
            topic = contest_topic.topic

            # 获取该题目的所有提交
            topic_submissions = [
                cs for cs in contest_submissions
                if cs.submission.topic_id == topic.id
            ]

            first_ac_time = None
            wrong_count = 0
            is_accepted = False
            penalty_minutes = 0

            # 遍历该题目的所有提交
            for cs in topic_submissions:
                submission = cs.submission
                is_ac = submission.overall_result == 'Accepted'

                if is_ac and not is_accepted:
                    is_accepted = True
                    first_ac_time = cs.submitted_at

                    # 计算该题目的罚时
                    if first_ac_time and contest.start_time:
                        time_diff = first_ac_time - contest.start_time
                        penalty_minutes = time_diff.total_seconds() / 60
                elif not is_ac and not is_accepted:
                    wrong_count += 1

            # 存储该题目的结果
            topic_results[topic.id] = {
                'is_accepted': is_accepted,
                'wrong_count': wrong_count,
                'first_ac_time': first_ac_time,
                'topic_order': contest_topic.order
            }

            # 如果该题目通过，累加通过数和罚时
            if is_accepted:
                total_accepted += 1
                topic_total_penalty = penalty_minutes + (wrong_count * contest.penalty_time)
                total_penalty += topic_total_penalty

        rank_data.append({
            'user': user,
            'username': user.username,
            'total_accepted': total_accepted,
            'total_penalty': total_penalty,
            'topic_results': topic_results,
            'participant': participant
        })

    # 按完成题目数量降序，罚时升序排序
    rank_data.sort(key=lambda x: (-x['total_accepted'], x['total_penalty']))

    # 添加排名（处理并列排名）
    current_rank = 1
    for i, data in enumerate(rank_data):
        if i > 0 and (rank_data[i - 1]['total_accepted'] == data['total_accepted'] and
                      rank_data[i - 1]['total_penalty'] == data['total_penalty']):
            data['rank'] = rank_data[i - 1]['rank']
        else:
            data['rank'] = current_rank
        current_rank += 1

    context = {
        'contest': contest,
        'contest_topics': contest_topics,
        'rank_data': rank_data,
        'page_title': f'{contest.title} - 详细排名'
    }
    return render(request, 'CheckObjection/contest/rank/rank_detail.html', context)


def get_contest_rankings(contest, limit=None):
    """获取比赛排名数据（简化版）"""
    participants = ContestParticipant.objects.filter(
        contest=contest, is_disqualified=False
    )

    rankings = []
    for participant in participants:
        # 计算每个参与者的总得分和AC数量
        total_score = 0
        ac_count = 0

        # 获取参与者的所有AC提交（按题目分组，取每个题目的最佳提交）
        for contest_topic in contest.contest_topics.all():
            best_submission = ContestSubmission.objects.filter(
                participant=participant,
                submission__topic=contest_topic.topic,
                submission__overall_result='Accepted'
            ).order_by('-submitted_at').first()

            if best_submission:
                total_score += contest_topic.score
                ac_count += 1

        rankings.append({
            'user_name': participant.user.username,
            'total_score': total_score,
            'ac_count': ac_count,
            'participant': participant
        })

    # 按得分和AC数量排序
    rankings.sort(key=lambda x: (-x['total_score'], -x['ac_count']))

    # 添加排名
    for i, rank in enumerate(rankings):
        rank['rank'] = i + 1

    return rankings[:limit] if limit else rankings
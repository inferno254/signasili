'use client';

import Link from 'next/link';
import { useProgress, useStreak, useBadges } from '@/lib/hooks/useProgress';
import { FireIcon, TrophyIcon, StarIcon } from '@heroicons/react/24/solid';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';

export default function LearnerDashboard() {
  const { data: progress, isLoading: progressLoading } = useProgress();
  const { data: streak, isLoading: streakLoading } = useStreak();
  const { data: badges, isLoading: badgesLoading } = useBadges();
  
  const { data: zones } = useQuery({
    queryKey: ['zones'],
    queryFn: async () => {
      const response = await api.content.zones();
      return response.data;
    },
  });

  if (progressLoading || streakLoading || badgesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const earnedBadges = badges?.earned || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Welcome back!</h1>
        <p className="text-gray-600 mt-1">Continue your KSL learning journey</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {/* XP Card */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <StarIcon className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Total XP</p>
              <p className="text-2xl font-bold text-gray-900">{progress?.total_xp || 0}</p>
            </div>
          </div>
        </div>

        {/* Streak Card */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center">
            <div className="p-3 bg-orange-100 rounded-lg">
              <FireIcon className="h-6 w-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Current Streak</p>
              <p className="text-2xl font-bold text-gray-900">{streak?.current_streak || 0} days</p>
            </div>
          </div>
        </div>

        {/* Lessons Card */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <TrophyIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Lessons Completed</p>
              <p className="text-2xl font-bold text-gray-900">{progress?.total_lessons_completed || 0}</p>
            </div>
          </div>
        </div>

        {/* SLO Mastery Card */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrophyIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">SLO Mastery</p>
              <p className="text-2xl font-bold text-gray-900">{Math.round(progress?.slo_mastery_rate || 0)}%</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Learning Zones */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Learning Zones</h2>
            <Link href="/learner/progress" className="text-primary-600 hover:text-primary-700 text-sm">
              View all progress →
            </Link>
          </div>

          <div className="space-y-4">
            {zones?.zones?.map((zone: any) => (
              <Link
                key={zone.id}
                href={`/learner/zone/${zone.id}`}
                className="block bg-white rounded-xl shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-16 w-16 bg-primary-100 rounded-lg flex items-center justify-center">
                      <span className="text-2xl font-bold text-primary-600">{zone.grade_level}</span>
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-semibold text-gray-900">{zone.name}</h3>
                      <p className="text-sm text-gray-600">{zone.total_quests} quests • Grade {zone.grade_level}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-gray-900">
                      {Math.round(zone.progress?.percentage || 0)}%
                    </div>
                    <div className="text-sm text-gray-600">{zone.progress?.completed_quests || 0}/{zone.total_quests} quests</div>
                  </div>
                </div>
                <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${zone.progress?.percentage || 0}%` }}
                  ></div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          {/* Recent Badges */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Badges</h3>
            {earnedBadges.length > 0 ? (
              <div className="space-y-3">
                {earnedBadges.slice(0, 3).map((badge: any) => (
                  <div key={badge.id} className="flex items-center">
                    <div className="h-10 w-10 bg-yellow-100 rounded-full flex items-center justify-center">
                      <TrophyIcon className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">{badge.name}</p>
                      <p className="text-xs text-gray-600">+{badge.points_reward} XP</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-600">Complete lessons to earn badges!</p>
            )}
            <Link
              href="/learner/badges"
              className="mt-4 block text-center text-sm text-primary-600 hover:text-primary-700"
            >
              View all badges →
            </Link>
          </div>

          {/* Daily Challenge */}
          <div className="bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl shadow-sm p-6 text-white">
            <h3 className="text-lg font-bold mb-2">Daily Challenge</h3>
            <p className="text-primary-100 mb-4">Practice 5 signs today to keep your streak!</p>
            <Link
              href="/practice"
              className="block w-full text-center bg-white text-primary-600 rounded-lg py-2 font-semibold hover:bg-primary-50 transition-colors"
            >
              Start Practice
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

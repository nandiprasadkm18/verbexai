import React from 'react';
import { useFetch } from '../hooks/useFetch';
import type { Meeting } from '../types.ts';
import { ArrowUpRight, ArrowDownRight, Users, CheckCircle2, MessageSquare, AlertTriangle } from 'lucide-react';

const StatCard = ({ label, value, delta, index }: { label: string, value: string | number, delta: string, index: number }) => (
  <div className={`corporate-card p-5 stagger-${(index % 5) + 1} relative group`}>
    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2.5">{label}</p>
    <div className="flex items-end justify-between">
      <h3 className="text-2xl font-bold text-primary tracking-tight">{String(value)}</h3>
      <div className={`flex items-center text-[11px] font-bold px-1.5 py-0.5 rounded ${
        delta.startsWith('+') || delta.toLowerCase() === 'critical' ? 'text-teal-700 bg-teal-50' : 'text-rose-700 bg-rose-50'
      }`}>
        {delta.startsWith('+') ? <ArrowUpRight size={12} className="mr-0.5" /> : delta.toLowerCase() === 'critical' ? <AlertTriangle size={10} className="mr-1" /> : <ArrowDownRight size={12} className="mr-0.5" />}
        {String(delta)}
      </div>
    </div>
  </div>
);

const ManagerView: React.FC = () => {
  const { data: stats } = useFetch<any>('/meetings/stats');
  const { data: recentMeetings } = useFetch<Meeting[]>('/meetings');
  const { data: speakers } = useFetch<any[]>('/speakers');

  const avgHealth = recentMeetings && recentMeetings.length > 0 
    ? Math.round(recentMeetings.reduce((acc, m) => acc + (m.health_score || 0), 0) / recentMeetings.length)
    : 0;

  const statItems = [
    { label: 'Total Meetings', value: stats?.meetings?.value || '0', delta: stats?.meetings?.delta || '0' },
    { label: 'Tasks Created', value: stats?.tasks?.value || '0', delta: stats?.tasks?.delta || '0' },
    { label: 'Decisions Logged', value: stats?.decisions?.value || '0', delta: stats?.decisions?.delta || '0' },
    { label: 'Stale Tasks', value: stats?.stale_tasks?.value || '0', delta: stats?.stale_tasks?.delta || '0' },
    { label: 'Avg Health', value: `${avgHealth}%`, delta: stats?.confidence?.delta || '0' },
  ];

  return (
    <div className="page p-8 max-w-7xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-10">
        {statItems.map((stat, i) => (
          <StatCard key={stat.label} {...stat} index={i} value={stats ? stat.value : '...'} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="corporate-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-primary tracking-tight">Recent Meeting Intelligence</h3>
              <button className="text-accent-teal text-sm font-semibold hover:underline">View All</button>
            </div>
            
            <div className="space-y-4">
              {recentMeetings?.map((meeting) => (
                <div key={meeting.id} className="flex items-center gap-4 p-4 rounded-lg border border-slate-100 hover:border-slate-200 hover:bg-slate-50/50 transition-all cursor-pointer group">
                  <div className="w-10 h-10 rounded bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-white group-hover:text-accent-teal transition-colors">
                    <Users size={20} />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-primary text-[15px]">{meeting.title}</h4>
                    <p className="text-slate-400 text-xs font-medium mt-0.5">{new Date(meeting.created_at).toLocaleDateString()} • {meeting.host_name}</p>
                  </div>
                  <div className="flex gap-6 items-center">
                    <div className="text-center">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Tasks</p>
                      <p className="text-[14px] font-bold text-primary">{meeting.task_count || 0}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Decisions</p>
                      <p className="text-[14px] font-bold text-primary">{meeting.decision_count || 0}</p>
                    </div>
                    <div className="w-10 h-10 rounded-full border-2 border-slate-100 p-0.5 ml-2">
                       <div className={`w-full h-full rounded-full flex items-center justify-center text-[10px] font-bold ${
                         (meeting.health_score || 0) > 80 ? 'bg-emerald-50 text-emerald-600' : 
                         (meeting.health_score || 0) > 40 ? 'bg-amber-50 text-amber-600' : 'bg-rose-50 text-rose-600'
                       }`}>
                         {Math.round(meeting.health_score || 0)}%
                       </div>
                    </div>
                  </div>
                </div>
              ))}
              {(!recentMeetings || recentMeetings.length === 0) && (
                <p className="text-sm text-slate-400 text-center py-10 font-bold uppercase tracking-widest">No Intelligence Data Sync'd</p>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-8">
          <div className="corporate-card p-6 bg-slate-900 text-white border-none shadow-premium relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-accent-teal/5 rounded-full -translate-y-16 translate-x-16 group-hover:bg-accent-teal/10 transition-all"></div>
            
            <div className="flex items-center justify-between mb-4 relative z-10">
              <h3 className="text-lg font-bold tracking-tight">Insight Logic</h3>
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
                <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest">{stats?.intelligence?.system_health || 'Active'}</span>
              </div>
            </div>

            <p className="text-slate-400 text-[11px] leading-relaxed mb-6 font-medium relative z-10">
              AI Cluster: <span className="text-accent-teal font-bold">{stats?.intelligence?.provider || 'Neural Core'}</span> • 
              Stability: <span className="text-white">99.9%</span>
            </p>

            <div className="mb-6 relative z-10">
              <div className="flex items-end justify-between mb-2">
                 <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Confidence Trend</p>
                 <span className="text-[14px] font-mono font-bold text-accent-teal">{stats?.intelligence?.precision || '94.2%'}</span>
              </div>
              <div className="h-16 w-full bg-white/2 rounded-lg border border-white/5 overflow-hidden flex items-end px-1 py-1">
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 100">
                  <path 
                    d={`M 0 80 Q 20 60 40 70 T 80 30 T 100 20`}
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="3" 
                    className="text-accent-teal" 
                    strokeLinecap="round"
                  />
                  <path 
                    d={`M 0 80 Q 20 60 40 70 T 80 30 T 100 20 L 100 100 L 0 100 Z`}
                    fill="url(#sparkline-gradient)" 
                    className="opacity-20 text-accent-teal"
                  />
                  <defs>
                    <linearGradient id="sparkline-gradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="currentColor" />
                      <stop offset="100%" stopColor="transparent" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>

            <div className="space-y-3 relative z-10">
               <div className="group/item flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 transition-all cursor-default">
                 <div className="flex items-center gap-3">
                    <CheckCircle2 size={14} className="text-emerald-400" />
                    <span className="text-[12px] font-bold tracking-tight text-slate-300">Extraction Precision</span>
                 </div>
                 <span className="text-[12px] font-mono font-bold text-emerald-400">{stats?.intelligence?.precision || '94.2%'}</span>
               </div>
               
               <div className="group/item p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 transition-all cursor-default">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                        <MessageSquare size={14} className="text-accent-blue" />
                        <span className="text-[12px] font-bold tracking-tight text-slate-300">Contextual Load</span>
                    </div>
                    <span className="text-[12px] font-mono font-bold">{stats?.intelligence?.contextual_load || '0%'}</span>
                  </div>
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-accent-blue transition-all duration-1000" 
                      style={{ width: stats?.intelligence?.contextual_load || '0%' }}
                    ></div>
                  </div>
               </div>

               <div className="grid grid-cols-2 gap-3">
                 <div className="p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-all cursor-default">
                    <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Latency</p>
                    <p className="text-[13px] font-mono font-bold text-white">1.2s</p>
                 </div>
                 <div className="p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-all cursor-default">
                    <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Memory</p>
                    <p className="text-[13px] font-mono font-bold text-white">4.8GB</p>
                 </div>
               </div>

               <div className="group/item flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 transition-all cursor-default">
                 <div className="flex items-center gap-3">
                    <AlertTriangle size={14} className="text-amber-400" />
                    <span className="text-[12px] font-bold tracking-tight text-slate-300">Intelligence Review</span>
                 </div>
                 <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono font-bold text-amber-400">{stats?.stale_tasks?.value || 0}</span>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">items</span>
                 </div>
               </div>
            </div>
          </div>

          <div className="corporate-card p-6">
             <h3 className="font-serif text-lg font-bold text-primary mb-5 relative">Ownership Map</h3>
             <div className="space-y-5 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
               {speakers?.map((person) => (
                 <div key={person.id}>
                   <div className="flex justify-between items-end mb-1.5">
                     <div>
                       <p className="text-[12px] font-bold text-primary leading-none">{person.name}</p>
                       <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wider mt-1">{person.role}</p>
                     </div>
                     <span className="text-[11px] font-bold text-primary">{Math.min(100, (person.tasks_owned * 15) + 10)}% Load</span>
                   </div>
                   <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                     <div className={`h-full ${person.color}`} style={{ width: `${Math.min(100, (person.tasks_owned * 15) + 10)}%` }}></div>
                   </div>
                 </div>
               ))}
               {(!speakers || speakers.length === 0) && (
                 <p className="text-[10px] text-slate-400 font-bold uppercase text-center py-4">No Team Ownership Logged</p>
               )}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManagerView;

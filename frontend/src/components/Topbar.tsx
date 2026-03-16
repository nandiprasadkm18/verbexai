import React from 'react';
import type { PageId } from '../types.ts';

interface TopbarProps {
  activePage: PageId;
}

const pageTitles: Record<PageId, string> = {
  manager: 'Manager View',
  meetings: 'All Meetings',
  tasks: 'Task Board',
  decisions: 'Decision Log',
  speakers: 'Speaker Map',
  stale: 'Stale Tasks',
  ingest: 'New Meeting',
  employees: 'Team Profiles',
};

const Topbar: React.FC<TopbarProps> = ({ activePage }) => {
  return (
    <header className="fixed top-0 right-0 left-inherit h-[60px] bg-white/80 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-8 z-40 transition-all duration-300" style={{ left: 'var(--sidebar-width, 240px)' }}>
      <h2 className="font-serif text-xl font-bold text-primary">{pageTitles[activePage]}</h2>
      
      <div className="flex items-center gap-6">
        {/* Removed non-functional static buttons here (search, notifications, export report) */}
      </div>
    </header>
  );
};

export default Topbar;
